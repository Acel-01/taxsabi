#!/usr/bin/env python3
"""Clean the extracted PenCom Voluntary Contributions guidelines for the DAPT corpus.

Removes running headers ("National Pension Commission" + letter-spaced title)
and the page number that follows each header, plus the cover-page boilerplate.
Body text is preserved verbatim.

Usage: uv run python scripts/clean_pencom_vc.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "sources" / "pencom_vc_guidelines_2018.txt"
OUT = ROOT / "data" / "dapt_corpus" / "pencom_vc_guidelines_2018_clean.txt"

RUNNING_HEADER = re.compile(r"^G\s*U\s*I\s*D\s*E\s*L\s*I\s*N\s*E\s*S\s+ON\s")
DROP_EXACT = {"National Pension Commission", "www.pencom.gov.ng", "PenCom"}
PAGE_NUMBER = re.compile(r"^\d{1,3}$")


def main() -> None:
    raw = SRC.read_text()
    lines = raw.split("\n")

    kept: list[str] = []
    headers = 0
    page_numbers = 0
    expect_page_number = False

    for line in lines:
        stripped = line.strip()

        if RUNNING_HEADER.match(stripped):
            headers += 1
            expect_page_number = True
            continue
        if stripped in DROP_EXACT:
            continue
        if not stripped:
            continue
        if expect_page_number:
            expect_page_number = False
            if PAGE_NUMBER.match(stripped):
                page_numbers += 1
                continue

        line = re.sub(r"[ \t]+", " ", line).strip()
        line = re.sub(r"\s+([;,])", r"\1", line)
        kept.append(line)

    text = "\n".join(kept) + "\n"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)

    print(f"wrote {len(text):,} chars -> {OUT}")
    print(f"input {len(raw):,} chars | reduction {100 * (1 - len(text) / len(raw)):.1f}%")
    print(f"running headers removed: {headers}")
    print(f"page numbers removed: {page_numbers}")
    print()
    print("verification sweep:")
    checks = {
        "running headers": r"G\s*U\s*I\s*D\s*E\s*L\s*I\s*N\s*E\s*S\s+ON",
        "cover boilerplate": r"www\.pencom\.gov\.ng",
    }
    for name, pattern in checks.items():
        hits = re.findall(pattern, text)
        status = "OK" if not hits else f"{len(hits)}: {hits[:3]}"
        print(f"  {name}: {status}")
    for term in [
        "1/3 of the month’s salary",
        "Section 10 (4) of the PRA 2014",
        "notify his employer in writing",
        "Voluntary Contributions shall be made only in Nigerian Currency",
    ]:
        print(f"  contains '{term}': {term in text}")


if __name__ == "__main__":
    main()
