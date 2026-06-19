"""
Merge all data sources into one final knowledge base for the bot.

Sources:
  1. data/yessenov_chunks_clean.jsonl   - cleaned overview/bio pages   (type=page)
  2. data/program_subpages.csv          - year/apply pages, the facts   (type=subpage)
  3. data/ocr_provisions.jsonl          - OCR'd rule PDFs               (type=provisions)

Output:
  data/knowledge_base.jsonl   - unified chunks, schema:
      {source_title, source_url, source_type, program, chunk_id, text}
"""

import json
import pandas as pd
from pathlib import Path


def chunk_text(text, chunk_size=1200, overlap=200):
    chunks, start = [], 0
    text = text or ""
    while start < len(text):
        c = text[start:start + chunk_size].strip()
        if c:
            chunks.append(c)
        start += chunk_size - overlap
    return chunks


def main():
    records = []

    # 1) cleaned pages (already chunked)
    n_page = 0
    with open("data/yessenov_chunks_clean.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            records.append({
                "source_title": r["source_title"],
                "source_url": r["source_url"],
                "source_type": "page",
                "program": "",
                "chunk_id": r["chunk_id"],
                "text": r["text"],
            })
            n_page += 1

    # 2) program sub-pages (the concrete facts) - chunk them
    n_sub = 0
    sub = pd.read_csv("data/program_subpages.csv")
    for _, row in sub.iterrows():
        for i, c in enumerate(chunk_text(row["text"])):
            records.append({
                "source_title": row["title"],
                "source_url": row["url"],
                "source_type": "subpage",
                "program": row["program"],
                "chunk_id": i,
                "text": c,
            })
            n_sub += 1

    # 3) OCR'd provisions - chunk them
    n_ocr = 0
    ocr_path = Path("data/ocr_provisions.jsonl")
    if ocr_path.exists():
        with open(ocr_path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                title = f"{r['program']} — {r['label']} ({r['filename']})"
                for i, c in enumerate(chunk_text(r["text"])):
                    records.append({
                        "source_title": title,
                        "source_url": r["pdf_url"],
                        "source_type": "provisions",
                        "program": r["program"],
                        "chunk_id": i,
                        "text": c,
                    })
                    n_ocr += 1

    with open("data/knowledge_base.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("Knowledge base built -> data/knowledge_base.jsonl")
    print(f"  page chunks       : {n_page}")
    print(f"  subpage chunks    : {n_sub}   (concrete facts: amounts, deadlines, eligibility)")
    print(f"  provisions chunks : {n_ocr}   (OCR'd rule PDFs)")
    print(f"  TOTAL             : {len(records)}")


if __name__ == "__main__":
    main()
