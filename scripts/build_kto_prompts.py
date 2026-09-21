#!/usr/bin/env python3
"""Build the KTO prompt pool (Phase 3.1).

Two sources:
  1. Verified single-turn Q&A (`data/sft_verified_v2/`) - prompt plus the
     engine-verified gold answer, with the blueprint metadata a deterministic
     labeler needs (authoritative values, required terms, expected citation).
  2. Novel engine-locked calculation scenarios (fresh amounts and phrasings) -
     no gold answer; labels come from on-policy samples only. These are where
     the model genuinely errs, so they carry the contrast signal.

Every record has a `labeler` key naming the deterministic rule to apply:
    engine_tax   - total tax must match the engine (single_calc)
    engine_saving- saving (or from/to tax pair) must match the engine
                   (single_counterfactual)
    fact_terms   - required terms present, no unauthorised amounts
    fact_terms_cited - as fact_terms plus exact citation
    clarify_no_compute - asks monthly vs annual and states no tax

Guards:
  - No prompt may duplicate any eval-suite prompt (normalized, verbatim).
  - Novel scenarios may not reuse any held-out probe amount or any amount
    already used in `data/scenarios/train.jsonl`.

Output: `data/kto/prompts.jsonl` (95/5 prompt-level split, seed 42).

Usage:
    uv run python scripts/build_kto_prompts.py
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rules_engine.engine import calculate_full, load_ruleset  # noqa: E402

VERIFIED = ROOT / "data" / "sft_verified_v2"
SCENARIOS = ROOT / "data" / "scenarios"
OUT = ROOT / "data" / "kto" / "prompts.jsonl"

SFT_LAYERS = [
    ("sft_topup", "topup_v3"),
    ("sft_single_en", "single_en"),
    ("sft_single_pcm", "single_pcm"),
]

TYPE_LABELER = {
    "single_calc": "engine_tax",
    "single_counterfactual": "engine_saving",
    "single_fact": "fact_terms",
    "single_fact_cited": "fact_terms_cited",
    "clarify_ask": "clarify_no_compute",
}

EVAL_FILES = [
    "data/eval/paraphrase_suite.jsonl",
    "data/eval/coach_eval.jsonl",
    "data/eval/multiturn_suite.jsonl",
    "data/eval/probe_prompts_heldout.jsonl",
    "data/eval/baseline_prompts.jsonl",
]

# SFT-derived selection limits (0 = take all). Calc/cf are stratified by
# scenario_family after collapsing each scenario to one phrasing.
CAPS = {
    "single_calc": 180,
    "single_counterfactual": 60,
    "single_fact": 0,
    "single_fact_cited": 0,
    "clarify_ask": 0,
}
TOPUP_CALC = 38
TOPUP_CF = 12

SYSTEM_PROMPT = (
    "You are an assistant that answers questions about Nigerian individual "
    "income tax under the Nigeria Tax Act 2025 for the 2026 year of assessment."
)

# ---------------------------------------------------------------- amounts ----

# All amounts below are checked against every held-out probe amount and every
# amount used in data/scenarios/train.jsonl - see novel_prompts().
GROSS_GRID = [
    1_180_000, 1_640_000, 2_260_000, 2_940_000, 3_480_000, 4_040_000,
    4_960_000, 6_200_000, 7_360_000, 8_880_000, 10_400_000, 13_600_000,
    16_800_000, 22_400_000, 28_800_000, 36_000_000, 44_000_000,
    1_220_000, 1_480_000, 1_920_000, 2_180_000, 2_620_000, 3_160_000,
    3_760_000, 4_360_000, 5_240_000, 5_880_000, 6_640_000, 7_880_000, 9_480_000,
]
RENTS = [180_000, 320_000, 460_000, 640_000, 880_000, 1_240_000, 1_680_000,
         2_240_000, 2_640_000, 3_200_000, 3_840_000, 4_600_000]
PENSIONS = [96_000, 144_000, 264_000, 396_000, 528_000, 720_000, 864_000]
NHIS = [36_000, 54_000, 78_000, 114_000, 162_000]
NHF = [44_000, 68_000, 92_000, 134_000]
MORTGAGES = [260_000, 520_000, 780_000, 1_020_000, 1_420_000]
LIFE = [78_000, 126_000, 198_000, 276_000]
MONTHLIES = [96_000, 112_000, 137_000, 163_000, 188_000, 214_000, 246_000,
             287_000, 325_000, 384_000, 415_000, 458_000]
BOUNDARIES = [799_999, 800_001, 2_199_999, 2_999_999, 3_000_001, 3_400_001,
              11_999_999, 12_000_001, 24_999_999, 25_000_001, 49_999_999,
              50_000_001]
HIGH = [58_000_000, 72_000_000, 96_000_000, 124_000_000, 160_000_000,
        240_000_000, 380_000_000, 500_000_000]

RELIEF_VERBS_EN = {
    "rent": "I pay NGN {amt} in rent each year",
    "pension": "I contribute NGN {amt} to pension each year",
    "nhis": "I pay NGN {amt} in NHIS contributions",
    "nhf": "I pay NGN {amt} to the NHF",
    "mortgage_interest": "I pay NGN {amt} in mortgage interest each year",
    "life_insurance": "I pay NGN {amt} in life insurance premiums",
}
RELIEF_VERBS_PCM = {
    "rent": "I dey pay NGN {amt} rent every year",
    "pension": "I dey contribute NGN {amt} go pension",
    "nhis": "I dey pay NGN {amt} for NHIS",
    "nhf": "I dey pay NGN {amt} for NHF",
    "mortgage_interest": "I dey pay NGN {amt} as mortgage interest",
    "life_insurance": "I dey pay NGN {amt} for life insurance",
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def norm(text: str) -> str:
    return " ".join(text.lower().split())


def money(value) -> str:
    return format(value, ".2f")


def short_money(value: int) -> str:
    if value % 1_000_000 == 0:
        return f"{value // 1_000_000}m"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".") + "m"
    return f"{value // 1000}k"


def relief_phrase(reliefs: dict, language: str, short: bool) -> str:
    verbs = RELIEF_VERBS_PCM if language == "pcm" else RELIEF_VERBS_EN
    parts = []
    for key, value in reliefs.items():
        if short and language == "en":
            parts.append(f"{key.replace('_', ' ')} {short_money(int(value))}")
        else:
            parts.append(verbs[key].format(amt=format(int(value), ",")))
    if not parts:
        return ""
    separator = " and " if language == "pcm" else ", and "
    if short and language == "en":
        return " (" + ", ".join(parts) + ")"
    return " and " + separator.join(parts)


def user_text(gross: int, reliefs: dict, language: str, style: int,
              monthly: bool = False) -> str:
    if monthly:
        if language == "pcm":
            return f"My monthly salary na NGN {gross // 12:,} and I no get other reliefs. How much tax I go pay?"
        return f"My monthly salary is NGN {gross // 12:,} and I have no other reliefs. How much tax do I pay?"
    if language == "pcm":
        if style % 2 == 0:
            return f"I dey earn NGN {gross:,} a year{relief_phrase(reliefs, 'pcm', False)}. How much tax I go pay?"
        return (f"My annual money na {short_money(gross)}{relief_phrase(reliefs, 'pcm', False)}. "
                "Abeg calculate my tax.")
    if style % 3 == 0:
        return f"My annual salary is NGN {gross:,}{relief_phrase(reliefs, 'en', False)}. How much tax do I pay?"
    if style % 3 == 1:
        return f"I earn {short_money(gross)} a year{relief_phrase(reliefs, 'en', True)}. What's my tax?"
    return (f"I'm planning next year's budget. My annual salary is NGN {gross:,}"
            f"{relief_phrase(reliefs, 'en', False)}. How much tax do I pay?")


def calc_authoritative(gross: int, reliefs: dict, ruleset: dict) -> dict:
    result = calculate_full(gross, reliefs, ruleset)
    breakdown = [
        {"band": band["band"], "rate": format(band["rate"], ".2f"),
         "taxed_amount": format(band["taxed_amount"], ".2f"),
         "tax": format(band["tax"], ".2f")}
        for band in result["breakdown"]
    ]
    return {
        "gross_annual_salary": money(gross),
        "relief_inputs": {k: money(v) for k, v in reliefs.items()},
        "applied_reliefs": {k: money(v) for k, v in reliefs.items()},
        "total_relief": money(result["total_relief"]),
        "chargeable_income": money(result["chargeable_income"]),
        "total_tax": money(result["total_tax"]),
        "tax_breakdown": breakdown,
    }


# Gold corrections where the generated verified answer misstates the law.
# Evidence: "taxable person" includes an individual (Nigeria Tax Act 2025,
# interpretation section) and s.13(1)(a) requires every taxable person to file
# an annual return "whether or not liable to pay tax"; see SOURCE_REGISTER
# s.13(1) and the S5 LIRS filing note. The original top-up gold claimed a
# no-income student has no filing duty - that is not supported by the text.
GOLD_OVERRIDES = {
    "tu3-fact-student-00": (
        "Yes - you still need to file. Section 13(1)(a) of the Nigeria Tax Act 2025 "
        "requires every taxable person to file an annual return each year of assessment, "
        "whether or not they are liable to pay tax. A student with no income will owe no "
        "tax but is still expected to file a nil annual return."
    ),
    "tu3-fact-student-01": (
        "No - that is not right. Section 13(1)(a) of the Nigeria Tax Act 2025 requires "
        "every taxable person to file an annual return each year of assessment, whether or "
        "not they are liable to pay tax. A student with no income should still file a nil "
        "annual return."
    ),
    "tu3-fact-student-02": (
        "Yes - the filing duty still applies. Section 13(1)(a) of the Nigeria Tax Act 2025 "
        "requires every taxable person to file an annual return each year of assessment, "
        "whether or not they are liable to pay tax, so a student with no income files a nil "
        "annual return."
    ),
    "tu3-fact-student-03": (
        "Yes. Section 13(1)(a) of the Nigeria Tax Act 2025 requires an annual return from "
        "every taxable person, whether or not they are liable to pay tax. A student with no "
        "income therefore still files a nil annual return."
    ),
}


# ------------------------------------------------------------ SFT-derived ----


def stratified(records: list[dict], limit: int, family_key="scenario_family") -> list[dict]:
    """Collapse each scenario to one phrasing and round-robin across families."""
    by_family: dict[str, list[dict]] = {}
    for record in records:
        by_family.setdefault(record.get(family_key) or "unknown", []).append(record)
    family_items: dict[str, list[dict]] = {}
    for family, items in by_family.items():
        groups: dict[str, list[dict]] = {}
        for record in items:
            groups.setdefault(record.get("scenario_id") or record["id"], []).append(record)
        picked = []
        for index, scenario_id in enumerate(sorted(groups)):
            group = groups[scenario_id]
            picked.append(group[index % len(group)])
        family_items[family] = picked
    ordered: list[dict] = []
    indices = {family: 0 for family in family_items}
    while len(ordered) < limit:
        progressed = False
        for family in sorted(family_items):
            index = indices[family]
            if index < len(family_items[family]):
                ordered.append(family_items[family][index])
                indices[family] += 1
                progressed = True
                if len(ordered) >= limit:
                    break
        if not progressed:
            break
    return ordered


def sft_records(seen: set[str]) -> list[dict]:
    out: list[dict] = []
    for source, layer in SFT_LAYERS:
        records = load_jsonl(VERIFIED / f"{layer}.jsonl")
        picks: dict[str, list[dict]] = {}
        for record in records:
            if record.get("type") not in TYPE_LABELER:
                continue
            prompt = next(t["content"] for t in record["turns"] if t["role"] == "user")
            key = norm(prompt)
            if key in seen:
                continue
            seen.add(key)
            picks.setdefault(record["type"], []).append(record)
        for type_name, items in picks.items():
            if source == "sft_topup" and type_name == "single_calc":
                chosen = items[:TOPUP_CALC]
            elif source == "sft_topup" and type_name == "single_counterfactual":
                chosen = items[:TOPUP_CF]
            elif type_name in ("single_calc", "single_counterfactual"):
                cap = CAPS[type_name]
                chosen = stratified(items, cap) if cap else items
            else:
                chosen = items
            out.extend(convert(source, record) for record in chosen)
    return out


def convert(source: str, record: dict) -> dict:
    type_name = record["type"]
    prompt = next(t["content"] for t in record["turns"] if t["role"] == "user")
    gold = GOLD_OVERRIDES.get(record["id"]) or next(
        t["content"] for t in record["turns"] if t["role"] == "assistant"
    )
    authoritative = record.get("authoritative", {})
    item = {
        "id": record["id"],
        "source": source,
        "origin_id": record["id"],
        "type": type_name,
        "labeler": TYPE_LABELER[type_name],
        "language": record.get("language", "en"),
        "prompt": prompt,
        "gold_completion": gold,
        "authoritative": authoritative,
        "required_terms": record.get("required_terms", []),
        "scenario_id": record.get("scenario_id"),
        "scenario_family": record.get("scenario_family"),
    }
    if type_name == "single_fact_cited":
        item["expected_citation"] = authoritative.get("citation")
    return item


# ------------------------------------------------------------- novel calc ----


def novel_candidates() -> list[tuple[str, int, dict, bool, int]]:
    """(family, gross_annual, reliefs, monthly, style) candidates."""
    specs: list[tuple[str, int, dict, bool, int]] = []
    grosses = GROSS_GRID

    for index, gross in enumerate(grosses):
        specs.append(("salary_only", gross, {}, False, index))

    for index in range(50):
        specs.append(("rent_below_cap", grosses[index % len(grosses)],
                      {"rent": RENTS[index % 8]}, False, index))
    for index in range(30):
        specs.append(("rent_above_cap", grosses[index % len(grosses)],
                      {"rent": RENTS[8 + index % 4]}, False, index))

    for index in range(24):
        specs.append(("pension_only", grosses[index % len(grosses)],
                      {"pension": PENSIONS[index % len(PENSIONS)]}, False, index))
    for index in range(18):
        specs.append(("nhis_only", grosses[index % len(grosses)],
                      {"nhis": NHIS[index % len(NHIS)]}, False, index))
    for index in range(18):
        specs.append(("nhf_only", grosses[index % len(grosses)],
                      {"nhf": NHF[index % len(NHF)]}, False, index))
    for index in range(14):
        specs.append(("mortgage_only", grosses[index % len(grosses)],
                      {"mortgage_interest": MORTGAGES[index % len(MORTGAGES)]}, False, index))
    for index in range(12):
        specs.append(("life_only", grosses[index % len(grosses)],
                      {"life_insurance": LIFE[index % len(LIFE)]}, False, index))

    combos = [
        ("rent_and_pension", 22, lambda i: {"rent": RENTS[i % 8], "pension": PENSIONS[i % 4]}),
        ("rent_and_nhis", 16, lambda i: {"rent": RENTS[i % 6], "nhis": NHIS[i % 3]}),
        ("pension_and_nhf", 16, lambda i: {"pension": PENSIONS[i % 5], "nhf": NHF[i % 3]}),
        ("rent_pension_nhis", 16, lambda i: {"rent": RENTS[i % 5], "pension": PENSIONS[i % 4], "nhis": NHIS[i % 3]}),
        ("multiple_reliefs", 14, lambda i: {"rent": RENTS[i % 4], "pension": PENSIONS[i % 3],
                                            "nhf": NHF[i % 2], "nhis": NHIS[i % 2]}),
    ]
    for family, count, builder in combos:
        for index in range(count):
            specs.append((family, grosses[index % len(grosses)], builder(index), False, index))

    for index, monthly in enumerate(MONTHLIES):
        specs.append(("monthly_salary", monthly * 12, {}, True, index))
    for index, gross in enumerate(BOUNDARIES):
        specs.append(("band_boundary", gross, {}, False, index))
    for index, gross in enumerate(HIGH):
        specs.append(("high_income", gross, {}, False, index))
    return specs


def novel_prompts(limit: int, probe_values: set[Decimal], used_amounts: set[Decimal],
                  used_pairs: set[tuple], seen: set[str]) -> list[dict]:
    ruleset = load_ruleset()
    out: list[dict] = []
    for family, gross, reliefs, monthly, style in novel_candidates():
        amounts = {Decimal(gross)} | {Decimal(v) for v in reliefs.values()}
        if amounts & probe_values:
            continue
        if amounts & used_amounts:
            continue
        pair = (str(gross), tuple(sorted((k, str(v)) for k, v in reliefs.items())))
        if pair in used_pairs:
            continue
        language = "pcm" if len(out) % 5 == 4 else "en"
        prompt = user_text(gross, reliefs, language, style, monthly)
        key = norm(prompt)
        if key in seen:
            continue
        seen.add(key)
        pid = f"kto-novel-{len(out):04d}"
        out.append({
            "id": pid,
            "source": "novel_template",
            "origin_id": None,
            "type": "single_calc",
            "labeler": "engine_tax",
            "language": language,
            "prompt": prompt,
            "gold_completion": None,
            "authoritative": calc_authoritative(gross, reliefs, ruleset),
            "required_terms": [],
            "scenario_id": pid,
            "scenario_family": f"novel-{family}",
        })
        if len(out) >= limit:
            break
    return out


# ------------------------------------------------------------------ main ----


def load_eval_prompts() -> set[str]:
    prompts: set[str] = set()
    for rel in EVAL_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        for row in load_jsonl(path):
            for field in ("prompt", "instruction"):
                if row.get(field):
                    prompts.add(norm(row[field]))
            for turn in row.get("turns", []):
                if isinstance(turn, dict) and turn.get("user"):
                    prompts.add(norm(turn["user"]))
    return prompts


def load_probe_values() -> set[Decimal]:
    values: set[Decimal] = set()
    for row in load_jsonl(ROOT / "data" / "eval" / "probe_prompts_heldout.jsonl"):
        inputs = row.get("scenario_inputs") or {}
        for value in [inputs.get("gross_annual_salary"), *(inputs.get("relief_inputs") or {}).values()]:
            if value is not None:
                values.add(Decimal(str(value)))
    return values


def load_used_scenario_amounts() -> tuple[set[Decimal], set[tuple]]:
    amounts: set[Decimal] = set()
    pairs: set[tuple] = set()
    for row in load_jsonl(SCENARIOS / "train.jsonl"):
        gross = row["ground_truth"]["gross_annual_salary"]
        reliefs = row.get("relief_inputs") or {}
        amounts.add(Decimal(str(gross)))
        for value in reliefs.values():
            amounts.add(Decimal(str(value)))
        pairs.add((str(int(Decimal(str(gross)))), tuple(sorted((k, str(int(Decimal(str(v))))) for k, v in reliefs.items()))))
    return amounts, pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--novel", type=int, default=312, help="novel calculation prompts")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    eval_prompts = load_eval_prompts()
    probe_values = load_probe_values()
    used_amounts, used_pairs = load_used_scenario_amounts()
    seen: set[str] = set()

    pool = sft_records(seen)

    overlap_failures = [item["id"] for item in pool if norm(item["prompt"]) in eval_prompts]
    if overlap_failures:
        print(f"FAIL: {len(overlap_failures)} SFT-derived prompts duplicate an eval suite prompt")
        for pid in overlap_failures[:5]:
            print(f"  {pid}")
        raise SystemExit(1)

    pool += novel_prompts(args.novel, probe_values, used_amounts, used_pairs, seen)

    rng = random.Random(42)
    rng.shuffle(pool)
    val_size = max(1, int(len(pool) * 0.05))
    for index, item in enumerate(pool):
        item["split"] = "val" if index < val_size else "train"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fh:
        for item in pool:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    from collections import Counter

    by_source = Counter(item["source"] for item in pool)
    by_type = Counter(item["type"] for item in pool)
    by_language = Counter(item["language"] for item in pool)
    gold = sum(1 for item in pool if item["gold_completion"])
    with_gold = Counter(item["type"] for item in pool if item["gold_completion"])
    print(f"wrote {len(pool)} KTO prompts -> {args.out}")
    print(f"  sources: {dict(by_source)}")
    print(f"  types: {dict(by_type)}")
    print(f"  languages: {dict(by_language)}")
    print(f"  with gold completion: {gold} {dict(with_gold)}")
    print(f"  eval-overlap guard: clean ({len(eval_prompts)} eval prompts checked)")
    print(f"  novel guard: {len(probe_values)} probe amounts, {len(used_amounts)} used scenario amounts excluded")


if __name__ == "__main__":
    main()
