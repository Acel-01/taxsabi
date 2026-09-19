#!/usr/bin/env python3
"""Clean the extracted Nigeria Tax Act 2025 text for DAPT corpus use.

Fixes PDF-extraction artifacts:
  1. Gazette page headers (2 variants, ~107 occurrences)
  2. Hyphenated line breaks ("Commence-\\nment") with a compound-preservation rule
  3. Curated broken-word fixes (leading/trailing/mid-word space artifacts)
  4. CAPS heading artifacts ("V AT" -> "VAT", "T AX" -> "TAX", ...)
  5. Whitespace normalization

Verification sweep after cleaning reports any remaining known-pattern hits.

Usage: uv run python scripts/clean_tax_act.py
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "sources" / "tax_act_2025.txt"
OUT = ROOT / "data" / "dapt_corpus" / "tax_act_2025_clean.txt"

# --- 1. Page headers (full-line matches) ---
HEADER_PATTERNS = [
    re.compile(r"^Nigeria Tax Act, 2025A\s+\d{3,4}\s+2025\s+No\. 7\s*$", re.M),
    re.compile(r"^Nigeria Tax Act, 2025\s+2025\s+No\. 7\s+A\s+\d{3,4}\s*$", re.M),
]

# --- 2. Line-break word fragments (broken across newlines without hyphen) ---
LINEBREAK_FIXES = {
    "Shor\nt T\nitle": "Short Title",
    "Shor\nt": "Short",
    "T\nAX BILL": "TAX BILL",
    "S\ntamp Duties": "Stamp Duties",
    "V\nalue": "Value",
    "T\nitle": "Title",
    "pr\nduced": "produced",
    "Tarrif\nfs": "Tariffs",
    "Start-\nup": "Start-up",
    "ENECTED by the National Assembly": "ENACTED by the National Assembly",
}

# --- 3. Curated broken-word fixes ---
# Leading-letter separated (T ax -> Tax)
LEADING_FIXES = {
    "T ax": "Tax", "T axation": "Taxation", "T itle": "Title", "T otal": "Total",
    "T rade": "Trade", "T ransaction": "Transaction", "T ransportation": "Transportation",
    "S tamp": "Stamp", "S tartup": "Startup", "S tates": "States", "S tatus": "Status",
    "V alue": "Value",
    "r elating": "relating", "r epresentatives": "representatives",
    "pr oduction": "production", "pr ofit": "profit", "pr ofits": "profits",
    "pr oducts": "products", "pr emises": "premises", "pr emium": "premium",
    "pr duced": "produced", "pr oduced": "produced", "pr ofessions": "professions",
    "pr ospecting": "prospecting",
}
# Trailing-letter separated (Offshor e -> Offshore; Par t -> Part)
TRAILING_FIXES = {
    "Offshor e": "Offshore", "expenditur e": "expenditure", "Par t": "Part",
    "Hydr ocarbon": "Hydrocarbon", "Ascer tainment": "Ascertainment",
    "Char geable": "Chargeable", "royalties": "royalties", "compulsor y": "compulsory",
}
# CAPS heading artifacts (V AT -> VAT)
CAPS_FIXES = {
    "V AT": "VAT", "V A T": "VAT",
    "C APITAL": "CAPITAL", "C HARGEABLE": "CHARGEABLE", "D EEP": "DEEP",
    "D EVELOPMENT": "DEVELOPMENT", "E CONOMIC": "ECONOMIC", "E XEMPTION": "EXEMPTION",
    "G ENERAL": "GENERAL", "H YDROCARBON": "HYDROCARBON", "I MPOSITION": "IMPOSITION",
    "I NCOME": "INCOME", "M ISCELLANEOUS": "MISCELLANEOUS", "O BJECTIVE": "OBJECTIVE",
    "O BJECTIVES": "OBJECTIVES", "P ART": "PART", "P ETROLEUM": "PETROLEUM",
    "R ATES": "RATES", "R EMITTANCES": "REMITTANCES", "S PECIAL": "SPECIAL",
    "S PECIALISED": "SPECIALISED", "S UPPLEMENTARY": "SUPPLEMENTARY",
    "S URCHARGE": "SURCHARGE", "T AX": "TAX",
}

# --- 4. Protected strings (must survive cleaning untouched) ---
PROTECTED_CHECK = ["I of", "V of", "X of", "S/N AGENCY", "S/N MINERALS", "Part I of"]


def fix_hyphenation(text: str) -> tuple[str, int]:
    """Join hyphenated line breaks. Keep the hyphen only when the compound
    appears with a hyphen elsewhere in the text (real compound like
    'sub-section'); otherwise drop it ('Commence-ment' -> 'Commencement')."""
    mid_line = text.replace("-\n", "-")
    pairs = re.findall(r"(\w+)-\n([a-z])", text)
    kept = merged = 0

    def repl(match: re.Match) -> str:
        nonlocal kept, merged
        left, right = match.group(1), match.group(2)
        compound = f"{left}-{right}"
        if re.search(rf"(?<![-\w]){re.escape(compound)}(?![-\w])", mid_line):
            kept += 1
            return compound
        merged += 1
        return left + right

    text = re.sub(r"(\w+)-\n([a-z])", repl, text)
    return text, (kept, merged)


def main() -> None:
    raw = SRC.read_text()
    text = raw

    # 1. Page headers
    header_hits = 0
    for pattern in HEADER_PATTERNS:
        text, n = pattern.subn("", text)
        header_hits += n

    # 2. Line-break fragments (before dehyphenation so "Start-\nup" wins)
    lb_hits = 0
    for broken, fixed in LINEBREAK_FIXES.items():
        lb_hits += text.count(broken)
        text = text.replace(broken, fixed)

    # 3. Hyphenation
    text, (kept, merged) = fix_hyphenation(text)

    # 4. Word fixes (longest-first to avoid partial overlaps)
    for table in (TRAILING_FIXES, LEADING_FIXES):
        for broken, fixed in sorted(table.items(), key=lambda kv: -len(kv[0])):
            text = text.replace(broken, fixed)
    for broken, fixed in sorted(CAPS_FIXES.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(broken, fixed)

    # 5. Whitespace normalization
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        line = re.sub(r"\s+([;,])", r"\1", line)
        if line:
            lines.append(line)
    text = "\n".join(lines) + "\n"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)

    # --- Verification sweep ---
    print(f"wrote {len(text):,} chars -> {OUT}")
    print(f"input {len(raw):,} chars | reduction {100 * (1 - len(text) / len(raw)):.1f}%")
    print(f"page headers removed: {header_hits}")
    print(f"line-break fragments fixed: {lb_hits}")
    print(f"hyphen breaks: {kept + merged} ({kept} compounds kept, {merged} merged)")
    print()
    print("verification sweep (remaining artifact patterns):")
    checks = {
        "page headers": r"^Nigeria Tax Act, 2025.*A\s*\d{3,4}",
        "broken T ax/S tatus/V alue class": r"\b[Tt]\sax\b|\bS\s(tatus|tamp|tartup)\b|\bV\salue\b",
        "CAPS split (single cap + CAPS)": r"\b[A-HJ-Z]\s[A-Z]{2,}\b",
        "mid-word pr-/r- breaks": r"\bpr\s[a-z]{3,}\b|\br\selating\b",
        "trailing-letter breaks": r"\b(Offshor|expenditur)\se\b|\bcompulsor\sy\b",
        "line-break fragments": r"\bShor\nt\b|\bT\nitle\b|\bpr\nduced\b|\bTarrif\nfs\b",
    }
    for name, pattern in checks.items():
        hits = re.findall(pattern, text, re.M)
        status = "OK (0)" if not hits else f"REMAINING: {len(hits)} — {Counter(hits).most_common(5)}"
        print(f"  {name}: {status}")
    protected_ok = all(p in text for p in PROTECTED_CHECK)
    print(f"protected strings intact: {'yes' if protected_ok else 'NO — CHECK!'}")


if __name__ == "__main__":
    main()
