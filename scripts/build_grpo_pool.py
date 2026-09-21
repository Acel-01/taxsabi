#!/usr/bin/env python3
"""Build the GRPO prompt pool (Phase 4.2), curated by measured difficulty.

Sources (single_calc only in v1):
  1. KTO calc prompts (`data/kto/prompts.jsonl`) - engine values already
     attached; difficulty tier taken from the KTO sampling stats where present.
  2. Verified SFT single-turn calc prompts not already in the KTO pool - engine
     values from their `authoritative` block; difficulty unknown until measured.
  3. Fresh novel scenarios with amounts never used in any training file, the
     held-out probe, or the KTO pool (template phrasings, en + Pidgin).

Every pool record carries the engine ground truth so the GRPO reward can score
the final total directly:
    {"id", "prompt", "language", "expected_total_tax",
     "expected_chargeable_income", "source", "tier", "sft_success", "family"}

Tiers come from exact-match success over sampled completions:
    0/3 -> hard | 1-2/3 -> mid | 3/3 -> easy | unm easured -> unknown

Modes:
    build (default)     write data/grpo/pool.jsonl + pool_unknown.jsonl
    --score-samples P   score a samples JSONL (sample_kto_completions output)
                        against expected totals, update tiers, rewrite pool
    --select mid        write data/grpo/train_pool.jsonl for the given tiers
                        (comma list), optional --limit with seed 42

Guards: no eval-suite prompt may enter the pool (same list as the SFT/KTO
assemblers); fresh scenarios may not reuse any known amount or (gross, reliefs)
pair.

Usage:
    uv run python scripts/build_grpo_pool.py
    uv run python scripts/build_grpo_pool.py --score-samples data/grpo/difficulty_samples.jsonl
    uv run python scripts/build_grpo_pool.py --select mid --limit 600
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_kto_prompts import (  # noqa: E402
    calc_authoritative,
    load_eval_prompts,
    load_jsonl,
    load_probe_values,
    load_used_scenario_amounts,
    norm,
    user_text,
)
from eval_qlora import TOTAL_TAX_RE, norm_amount  # noqa: E402
from eval_qlora import extract_labeled_amount  # noqa: E402
from rules_engine.engine import load_ruleset  # noqa: E402
from verify_sft_generation import collect_values  # noqa: E402

VERIFIED = ROOT / "data" / "sft_verified_v2"
KTO_PROMPTS = ROOT / "data" / "kto" / "prompts.jsonl"
KTO_STATS = ROOT / "data" / "kto" / "label_stats.json"
OUT_DIR = ROOT / "data" / "grpo"


def authoritative_values(record: dict) -> set[Decimal]:
    values: set[Decimal] = set()
    collect_values(record.get("authoritative", {}), values)
    return values


def tier_from_success(desirable: int, samples: int) -> str:
    if samples == 0:
        return "unknown"
    if desirable == 0:
        return "hard"
    if desirable >= samples:
        return "easy"
    return "mid"


def load_kto_pool() -> tuple[list[dict], dict[str, dict], set[Decimal], set[tuple]]:
    records = load_jsonl(KTO_PROMPTS)
    stats = {}
    if KTO_STATS.exists():
        stats = {entry["prompt_id"]: entry for entry in json.loads(KTO_STATS.read_text())["prompt_stats"]}
    forbidden: set[Decimal] = set()
    pairs: set[tuple] = set()
    for record in records:
        auth = record.get("authoritative", {})
        gross = auth.get("gross_annual_salary")
        if gross is not None:
            forbidden.add(Decimal(str(gross)))
            reliefs = auth.get("relief_inputs", {})
            forbidden.update(Decimal(str(v)) for v in reliefs.values())
            pairs.add((norm_amount(str(gross)), tuple(sorted((k, norm_amount(str(v))) for k, v in reliefs.items()))))
    return records, stats, forbidden, pairs


def pool_entry(pid: str, prompt: str, language: str, expected_tax: str,
               expected_ci: str, source: str, family: str | None,
               tier: str = "unknown", success: str | None = None) -> dict:
    return {
        "id": pid,
        "prompt": prompt,
        "language": language,
        "expected_total_tax": expected_tax,
        "expected_chargeable_income": expected_ci,
        "source": source,
        "tier": tier,
        "sft_success": success,
        "family": family,
    }


def from_kto(stats: dict[str, dict]) -> list[dict]:
    entries = []
    for record in load_jsonl(KTO_PROMPTS):
        if record.get("type") != "single_calc":
            continue
        auth = record.get("authoritative", {})
        if not auth.get("total_tax"):
            continue
        entry_stat = stats.get(record["id"])
        tier = "unknown"
        success = None
        if entry_stat:
            tier = tier_from_success(entry_stat["desirable"], entry_stat["samples"])
            success = f"{entry_stat['desirable']}/{entry_stat['samples']}"
        entries.append(pool_entry(
            record["id"], record["prompt"], record.get("language", "en"),
            auth["total_tax"], auth.get("chargeable_income", ""),
            "kto", record.get("scenario_family"), tier, success,
        ))
    return entries


def from_sft(seen: set[str], kto_ids: set[str]) -> list[dict]:
    entries = []
    for layer in ("single_en", "single_pcm", "topup_v3"):
        for record in load_jsonl(VERIFIED / f"{layer}.jsonl"):
            if record.get("type") != "single_calc":
                continue
            if record["id"] in kto_ids:
                continue
            auth = record.get("authoritative", {})
            if not auth.get("total_tax"):
                continue
            prompt = next(t["content"] for t in record["turns"] if t["role"] == "user")
            key = norm(prompt)
            if key in seen:
                continue
            seen.add(key)
            entries.append(pool_entry(
                record["id"], prompt, record.get("language", "en"),
                auth["total_tax"], auth.get("chargeable_income", ""),
                "sft", record.get("scenario_family"),
            ))
    return entries


def fresh_values(start: int, step: int, count: int, forbidden: set[Decimal]) -> list[int]:
    values: list[int] = []
    value = start
    while len(values) < count:
        value += step
        if Decimal(value) not in forbidden:
            values.append(value)
    return values


def from_fresh(count: int, forbidden: set[Decimal], forbidden_pairs: set[tuple],
               seen: set[str]) -> tuple[list[dict], set[Decimal], set[tuple]]:
    ruleset = load_ruleset()
    grosses = fresh_values(1_013_000, 17_000, 24, forbidden)
    high_grosses = fresh_values(26_000_000, 271_000, 8, forbidden)
    rents = fresh_values(173_000, 11_000, 60, forbidden)
    pensions = fresh_values(83_000, 7_000, 20, forbidden)
    nhis = fresh_values(29_000, 5_000, 14, forbidden)
    nhf = fresh_values(31_000, 6_000, 14, forbidden)
    mortgages = fresh_values(193_000, 13_000, 14, forbidden)
    life = fresh_values(61_000, 9_000, 12, forbidden)
    monthlies = fresh_values(97_000, 6_000, 14, forbidden)

    specs: list[tuple[str, int, dict, bool, int]] = []

    def add(family, gross, reliefs, monthly=False, style=0):
        specs.append((family, gross, reliefs, monthly, style))

    for index in range(20):
        add("salary_only", grosses[index], {}, style=index)
    for index in range(40):
        add("rent_below_cap", grosses[index % len(grosses)], {"rent": rents[index]}, style=index)
    for index in range(20):
        add("rent_above_cap", grosses[index % len(grosses)], {"rent": rents[40 + index]}, style=index)
    for index in range(16):
        add("pension_only", grosses[(index + 3) % len(grosses)], {"pension": pensions[index]}, style=index)
    for index in range(12):
        add("nhis_only", grosses[(index + 6) % len(grosses)], {"nhis": nhis[index]}, style=index)
    for index in range(12):
        add("nhf_only", grosses[(index + 9) % len(grosses)], {"nhf": nhf[index]}, style=index)
    for index in range(10):
        add("mortgage_only", grosses[(index + 2) % len(grosses)], {"mortgage_interest": mortgages[index]}, style=index)
    for index in range(8):
        add("life_only", grosses[(index + 11) % len(grosses)], {"life_insurance": life[index]}, style=index)
    for index in range(12):
        add("rent_and_pension", grosses[index % len(grosses)],
            {"rent": rents[index % 30], "pension": pensions[index % 16]}, style=index)
    for index in range(10):
        add("rent_and_nhis", grosses[(index + 5) % len(grosses)],
            {"rent": rents[(index + 7) % 34], "nhis": nhis[index % 12]}, style=index)
    for index in range(10):
        add("pension_and_nhf", grosses[(index + 8) % len(grosses)],
            {"pension": pensions[(index + 5) % 18], "nhf": nhf[index % 10]}, style=index)
    for index in range(8):
        add("rent_pension_nhis", grosses[(index + 13) % len(grosses)],
            {"rent": rents[(index + 3) % 28], "pension": pensions[index % 14], "nhis": nhis[index % 10]}, style=index)
    for index in range(12):
        add("monthly_salary", monthlies[index] * 12, {}, monthly=True, style=index)
    boundaries = [799_997, 800_003, 2_199_997, 2_999_997, 3_000_003, 3_400_003,
                  11_999_997, 12_000_003, 24_999_997, 25_000_003, 49_999_997, 50_000_003]
    for index, gross in enumerate(boundaries):
        add("band_boundary", gross, {}, style=index)
    for index, gross in enumerate(high_grosses):
        add("high_income", gross, {}, style=index)

    entries: list[dict] = []
    local_pairs: set[tuple] = set()
    for family, gross, reliefs, monthly, style in specs:
        amounts = {Decimal(gross)} | {Decimal(v) for v in reliefs.values()}
        if amounts & forbidden:
            continue
        pair = (norm_amount(str(gross)), tuple(sorted((k, norm_amount(str(v))) for k, v in reliefs.items())))
        if pair in forbidden_pairs or pair in local_pairs:
            continue
        local_pairs.add(pair)
        language = "pcm" if len(entries) % 5 == 4 else "en"
        prompt = user_text(gross, reliefs, language, style, monthly)
        key = norm(prompt)
        if key in seen:
            continue
        seen.add(key)
        pid = f"grpo-fresh-{len(entries):04d}"
        auth = calc_authoritative(gross, reliefs, ruleset)
        entries.append(pool_entry(
            pid, prompt, language, auth["total_tax"], auth["chargeable_income"],
            "fresh", f"novel-{family}",
        ))
        if len(entries) >= count:
            break
    return entries, forbidden, forbidden_pairs


def score_samples(pool: list[dict], samples_path: Path) -> Counter:
    expected = {entry["id"]: entry["expected_total_tax"] for entry in pool}
    hits: dict[str, int] = {}
    totals: dict[str, int] = {}
    scored = 0
    for row in load_jsonl(samples_path):
        pid = row["id"]
        if pid not in expected:
            continue
        totals[pid] = totals.get(pid, 0) + 1
        predicted = extract_labeled_amount(row["answer"], TOTAL_TAX_RE)
        if predicted is not None and predicted == norm_amount(expected[pid]):
            hits[pid] = hits.get(pid, 0) + 1
            scored += 1
    updated = 0
    for entry in pool:
        pid = entry["id"]
        if pid not in totals:
            continue
        tier = tier_from_success(hits.get(pid, 0), totals[pid])
        entry["tier"] = tier
        entry["sft_success"] = f"{hits.get(pid, 0)}/{totals[pid]}"
        updated += 1
    return Counter({"updated": updated, "exact": scored, "samples": sum(totals.values())})


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", type=int, default=210, help="fresh novel prompts")
    parser.add_argument("--pool", type=Path, default=OUT_DIR / "pool.jsonl")
    parser.add_argument("--score-samples", type=Path, default=None,
                        help="score sampled completions and update tiers in --pool")
    parser.add_argument("--select", default=None,
                        help="comma list of tiers to select into train_pool.jsonl")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    if args.score_samples:
        pool = load_jsonl(args.pool) if args.pool.exists() else []
        if not pool:
            raise SystemExit(f"pool not found: {args.pool}")
        stats = score_samples(pool, args.score_samples)
        write_jsonl(args.pool, pool)
        tiers = Counter(entry["tier"] for entry in pool)
        print(f"scored {stats['samples']} samples across {stats['updated']} prompts "
              f"({stats['exact']} exact)")
        print(f"tiers now: {dict(tiers)}")
        return

    if args.select:
        pool = load_jsonl(args.pool) if args.pool.exists() else []
        if not pool:
            raise SystemExit(f"pool not found: {args.pool}")
        tiers = {t.strip() for t in args.select.split(",") if t.strip()}
        selected = [entry for entry in pool if entry["tier"] in tiers]
        if args.limit and len(selected) > args.limit:
            random.Random(42).shuffle(selected)
            selected = selected[: args.limit]
        out = args.out or OUT_DIR / "train_pool.jsonl"
        write_jsonl(out, selected)
        print(f"selected {len(selected)} prompts ({sorted(tiers)}) -> {out}")
        print(f"  by tier: {dict(Counter(entry['tier'] for entry in selected))}")
        print(f"  by source: {dict(Counter(entry['source'] for entry in selected))}")
        return

    # build
    eval_prompts = load_eval_prompts()
    kto_records, kto_stats, forbidden, forbidden_pairs = load_kto_pool()
    kto_entries = from_kto(kto_stats)
    kto_ids = {entry["id"] for entry in kto_entries}
    seen = {norm(entry["prompt"]) for entry in kto_entries}

    sft_entries = from_sft(seen, kto_ids)
    fresh_entries, _, _ = from_fresh(args.fresh, forbidden, forbidden_pairs, seen)

    pool = kto_entries + sft_entries + fresh_entries
    overlap = [entry["id"] for entry in pool if norm(entry["prompt"]) in eval_prompts]
    if overlap:
        print(f"FAIL: {len(overlap)} pool prompts duplicate an eval suite prompt: {overlap[:5]}")
        raise SystemExit(1)

    write_jsonl(args.pool, pool)
    unknown = [entry for entry in pool if entry["tier"] == "unknown"]
    write_jsonl(OUT_DIR / "pool_unknown.jsonl", unknown)

    print(f"wrote {len(pool)} GRPO prompts -> {args.pool}")
    print(f"  sources: {dict(Counter(entry['source'] for entry in pool))}")
    print(f"  languages: {dict(Counter(entry['language'] for entry in pool))}")
    print(f"  tiers: {dict(Counter(entry['tier'] for entry in pool))}")
    print(f"  eval-overlap guard: clean ({len(eval_prompts)} eval prompts checked)")
    print(f"  difficulty measurement needed for {len(unknown)} prompts -> {OUT_DIR / 'pool_unknown.jsonl'}")


if __name__ == "__main__":
    main()
