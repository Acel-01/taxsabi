#!/usr/bin/env python3
"""OCR the Pension Reform Act 2014 gazette scan for the source register.

The PenCom PDF is a JBIG2 scan with an invisible, scrambled OCR text layer
(text rendering mode 3; extraction yields substituted codes). This script
ignores that layer, renders each page, and OCRs it with RapidOCR.

Run (deps are ephemeral):
    uv run --with pymupdf --with rapidocr-onnxruntime python scripts/ocr_pra_2014.py

Output: sources/pra_2014_ocr.txt
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import pymupdf
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parents[1]
PDF = Path("/tmp/opencode/PRA_2014.pdf")
OUT = ROOT / "sources" / "pra_2014_ocr.txt"
DPI = 200


def page_lines(engine: RapidOCR, page: pymupdf.Page) -> list[str]:
    pix = page.get_pixmap(dpi=DPI)
    img = pix.tobytes("png")
    result, _ = engine(img, use_cls=False)
    if not result:
        return []
    items = []
    for box, text, conf in result:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append((min(ys), min(xs), conf, text))
    items.sort(key=lambda t: (t[0], t[1]))
    return [text for *_, text in items]


def main() -> None:
    doc = pymupdf.open(PDF)
    engine = RapidOCR()
    pages: list[str] = []
    t0 = time.time()
    for i, page in enumerate(doc):
        lines = page_lines(engine, page)
        pages.append("\n".join(lines))
        print(f"page {i + 1}/{len(doc)}: {len(lines)} lines ({time.time() - t0:.0f}s)", flush=True)

    text = "\n\n".join(pages) + "\n"
    OUT.write_text(text)

    print(f"\nwrote {len(text):,} chars -> {OUT}")
    checks = {
        "title": r"PENSION REFORM ACT",
        "rates 8%": r"8%",
        "rates 10%": r"10%",
        "voluntary contributions": r"[Vv]oluntary [Cc]ontribution",
        "s.10(4) reference": r"10\s*\(4\)",
        "employer remittance": r"not later than 7 days|7 days",
    }
    for name, pattern in checks.items():
        hits = re.findall(pattern, text)
        print(f"  {name}: {len(hits)} hits")

    if len(sys.argv) > 1 and sys.argv[1] == "--sweep":
        for term in sys.argv[2:]:
            n = len(re.findall(re.escape(term), text))
            print(f"  sweep '{term}': {n}")


if __name__ == "__main__":
    main()
