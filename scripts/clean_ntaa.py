#!/usr/bin/env python3
"""Clean the extracted Nigeria Tax Administration Act 2025 text for the DAPT corpus.

Shares the hyphenation logic with clean_tax_act.py; NTAA-specific page
headers and CAPS-heading artifacts are handled here.

Usage: uv run python scripts/clean_ntaa.py
"""
from __future__ import annotations

import re
from pathlib import Path

from clean_tax_act import fix_hyphenation

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/tmp/opencode/ntaa_2025.txt")
OUT = ROOT / "data" / "dapt_corpus" / "ntaa_2025_clean.txt"

HEADER_PATTERNS = [
    re.compile(r"^\s*2025\s+No\.\s*5\s+A\s+\d{3}Nigeria Tax Administration Act, 2025\s*$", re.M),
    re.compile(r"^A\s+\d{3}\s+2025 No\. 5 Nigeria Tax Administration Act, 2025\s*$", re.M),
]


def main() -> None:
    raw = SRC.read_text()
    text = raw

    header_hits = 0
    for pattern in HEADER_PATTERNS:
        text, n = pattern.subn("", text)
        header_hits += n

    text, (kept, merged) = fix_hyphenation(text)

    # CAPS heading splits (O NE -> ONE); single capital + space + CAPS, excluding I
    # (Roman numerals like "PART I OF" must survive).
    caps_hits = len(re.findall(r"\b[A-HJ-Z]\s[A-Z]{2,}\b", text))
    text = re.sub(r"\b([A-HJ-Z])\s([A-Z]{2,})\b", r"\1\2", text)

    # Whitespace normalization
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        line = re.sub(r"\s+([;,])", r"\1", line)
        if line:
            lines.append(line)
    text = "\n".join(lines) + "\n"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)

    print(f"wrote {len(text):,} chars -> {OUT}")
    print(f"input {len(raw):,} chars | reduction {100 * (1 - len(text) / len(raw)):.1f}%")
    print(f"page headers removed: {header_hits}")
    print(f"hyphen breaks: {kept + merged} ({kept} compounds kept, {merged} merged)")
    print(f"CAPS heading splits merged: {caps_hits}")
    print()
    print("verification sweep:")
    checks = {
        "page headers": r"Nigeria Tax Administration Act, 2025\s*$",
        "caps splits remaining": r"\b[A-HJ-Z]\s[A-Z]{2,}\b",
        "roman numerals intact (sample)": r"\bPART I\b|\bPart I\b",
    }
    for name, pattern in checks.items():
        hits = re.findall(pattern, text, re.M)
        status = "OK" if not hits else f"{len(hits)}: {hits[:5]}"
        print(f"  {name}: {status}")
    # sanity checks
    for term in ["Pay As You Earn", "31st January", "relevant tax authority"]:
        print(f"  contains '{term}': {term in text}")


if __name__ == "__main__":
    main()
