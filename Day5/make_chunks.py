import pandas as pd
import json
from pathlib import Path

Path("data").mkdir(exist_ok=True)

df = pd.read_csv("data/yessenov_pages.csv")


def chunk_text(text, chunk_size=1200, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start += chunk_size - overlap

    return chunks


records = []

for _, row in df.iterrows():
    chunks = chunk_text(row["text"])

    for i, chunk in enumerate(chunks):
        records.append({
            "source_title": row["title"],
            "source_url": row["url"],
            "chunk_id": i,
            "text": chunk
        })

with open("data/yessenov_chunks.jsonl", "w", encoding="utf-8") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

print(f"Saved {len(records)} chunks to data/yessenov_chunks.jsonl")