"""
OCR the scanned 'Provisions' / 'Program' PDFs into text.

These rule docs are scanned images (no text layer), so we rasterize each page
and run Tesseract with rus+kaz+eng. Output goes to data/ocr/<name>.txt and a
combined data/ocr_provisions.jsonl for chunking.

Only OCRs PDFs whose manifest label looks like a rule doc (Provisions/Program),
not the winner/participant lists.
"""

import sys
import json
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract

OUT_DIR = Path("data/ocr")
OUT_DIR.mkdir(parents=True, exist_ok=True)
LANGS = "rus+kaz+eng"
DPI = 250


def ocr_pdf(path: Path) -> str:
    pages = convert_from_path(str(path), dpi=DPI)
    texts = []
    for img in pages:
        texts.append(pytesseract.image_to_string(img, lang=LANGS))
    return "\n\n".join(texts)


def main(only=None):
    m = pd.read_csv("data/files/manifest.csv")
    rule = m[m["label"].str.contains("Provision|Program", case=False, na=False)].copy()
    if only:
        rule = rule[rule["filename"].str.contains(only, na=False)]

    print(f"OCR-ing {len(rule)} rule docs (lang={LANGS}, dpi={DPI})...\n")
    records = []
    for _, r in rule.iterrows():
        pdf = Path("data/files") / r["filename"]
        if not pdf.exists():
            print(f"  ! missing {pdf}")
            continue
        try:
            text = ocr_pdf(pdf).strip()
        except Exception as e:
            print(f"  ! OCR failed {pdf.name}: {e}")
            continue
        txt_path = OUT_DIR / (pdf.stem + ".txt")
        txt_path.write_text(text, encoding="utf-8")
        records.append({
            "program": r["program"],
            "label": r["label"],
            "source_page": r["source_page"],
            "pdf_url": r["pdf_url"],
            "filename": r["filename"],
            "text": text,
            "text_length": len(text),
        })
        print(f"  v {pdf.name:55} {len(text):>6} chars")

    with open("data/ocr_provisions.jsonl", "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nDone. {len(records)} docs -> data/ocr/*.txt + data/ocr_provisions.jsonl")


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    main(only)
