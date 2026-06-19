"""Merge all source data into the final bot knowledge base.

Sources:
  1. data/yessenov_pages_clean.csv  - cleaned overview/bio pages
  2. data/program_subpages.csv      - year/apply pages with concrete facts
  3. data/ocr_provisions.jsonl      - OCR'd rule PDFs

Output:
  data/knowledge_base.jsonl

Record schema:
  {
    source_title, source_url, source_type, program,
    chunk_id, keywords, text
  }
"""

import csv
import json
import re
from pathlib import Path


MAX_CHARS = 1200
MIN_TAIL_CHARS = 160

STOPWORDS = {
    "about", "after", "also", "among", "and", "are", "with", "from", "for",
    "have", "into", "not", "that", "the", "their", "this", "will", "year",
    "program", "foundation", "yessenov", "shakhmardan", "қаз", "рус", "eng",
    "для", "при", "или", "что", "как", "это", "the", "на", "по", "в", "и",
}

BOILERPLATE_PATTERNS = [
    re.compile(r"^seen by:\s*[\d,]+$", re.I),
    re.compile(r"^downloaded:\s*[\d,]+,\s*size:\s*.*$", re.I),
    re.compile(r"^size:\s*[\d,.]+\s*(kb|mb|b)?$", re.I),
    re.compile(r"^read more:\s*here$", re.I),
]


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def is_boilerplate_line(line):
    line = line.strip()
    if not line:
        return True
    return any(pattern.match(line) for pattern in BOILERPLATE_PATTERNS)


def clean_text(text):
    text = text or ""
    text = text.replace("\xa0", " ")
    lines = [ln.strip() for ln in text.splitlines() if not is_boilerplate_line(ln)]
    text = "\n".join(lines)
    text = re.sub(r"Downloaded:\s*[\d,]+,\s*Size:\s*[\d,.]+\s*(?:KB|MB|B)?", "", text, flags=re.I)
    text = re.sub(r"Seen by:\s*[\d,]+", "", text, flags=re.I)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_piece(piece, chunk_size=MAX_CHARS):
    """Split a long paragraph without cutting through words."""
    words = piece.split()
    chunks, current = [], []
    current_len = 0
    for word in words:
        add_len = len(word) + (1 if current else 0)
        if current and current_len + add_len > chunk_size:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += add_len
    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_text(text, chunk_size=MAX_CHARS, min_tail_chars=MIN_TAIL_CHARS):
    """Paragraph-aware chunking, with no mid-word starts or tiny tail fragments."""
    text = clean_text(text)
    if not text:
        return []

    pieces = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    normalized = []
    for piece in pieces:
        if len(piece) <= chunk_size:
            normalized.append(piece)
        else:
            normalized.extend(split_long_piece(piece, chunk_size))

    chunks, current = [], ""
    for piece in normalized:
        candidate = piece if not current else f"{current}\n\n{piece}"
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = piece
    if current:
        chunks.append(current)

    if len(chunks) > 1 and len(chunks[-1]) < min_tail_chars:
        tail = chunks.pop()
        if len(chunks[-1]) + len(tail) + 2 <= chunk_size + 200:
            chunks[-1] = f"{chunks[-1]}\n\n{tail}"
        else:
            chunks.append(tail)

    return [c.strip() for c in chunks if c.strip()]


def keywords_for(record):
    text = f"{record['source_title']} {record['program']} {record['text']}".lower()
    tokens = re.findall(r"[a-zа-яёәіңғүұқөһ0-9][a-zа-яёәіңғүұқөһ0-9-]{2,}", text)
    counts = {}
    for token in tokens:
        if token in STOPWORDS:
            continue
        if token.isdigit() and not re.fullmatch(r"20\d{2}|19\d{2}", token):
            continue
        counts[token] = counts.get(token, 0) + 1

    program_terms = [term for term in record["program"].split("-") if term]
    ranked = sorted(counts, key=lambda t: (-counts[t], t))
    out = []
    for token in program_terms + ranked:
        if token not in out:
            out.append(token)
        if len(out) >= 12:
            break
    return out


def add_chunks(records, *, source_title, source_url, source_type, program, text):
    for chunk in chunk_text(text):
        record = {
            "source_title": source_title,
            "source_url": source_url,
            "source_type": source_type,
            "program": program or "",
            "chunk_id": 0,
            "keywords": [],
            "text": chunk,
        }
        record["keywords"] = keywords_for(record)
        records.append(record)


def main():
    records = []

    # 1) Cleaned pages. Skip URLs that also appear in program sub-pages; those
    # sub-pages contain the same material plus more concrete application facts.
    sub_rows = read_csv("data/program_subpages.csv")
    subpage_urls = {row["url"] for row in sub_rows}
    n_page = 0
    for row in read_csv("data/yessenov_pages_clean.csv"):
        if row["url"] in subpage_urls:
            continue
        before = len(records)
        add_chunks(
            records,
            source_title=row["title"],
            source_url=row["url"],
            source_type="page",
            program="",
            text=row["text"],
        )
        n_page += len(records) - before

    # 2) Program sub-pages (the concrete facts).
    n_sub = 0
    for row in sub_rows:
        before = len(records)
        add_chunks(
            records,
            source_title=row["title"],
            source_url=row["url"],
            source_type="subpage",
            program=row["program"],
            text=row["text"],
        )
        n_sub += len(records) - before

    # 3) OCR'd provisions.
    n_ocr = 0
    ocr_path = Path("data/ocr_provisions.jsonl")
    if ocr_path.exists():
        with open(ocr_path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                title = f"{r['program']} — {r['label']} ({r['filename']})"
                before = len(records)
                add_chunks(
                    records,
                    source_title=title,
                    source_url=r["pdf_url"],
                    source_type="provisions",
                    program=r["program"],
                    text=r["text"],
                )
                n_ocr += len(records) - before

    # De-duplicate exact text from the same source URL/type, then assign stable
    # chunk IDs per source URL + source type.
    deduped = []
    seen = set()
    for r in records:
        key = (r["source_url"], r["source_type"], re.sub(r"\s+", " ", r["text"]).strip())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    counters = {}
    for r in deduped:
        key = (r["source_url"], r["source_type"])
        r["chunk_id"] = counters.get(key, 0)
        counters[key] = r["chunk_id"] + 1

    with open("data/knowledge_base.jsonl", "w", encoding="utf-8") as f:
        for r in deduped:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("Knowledge base built -> data/knowledge_base.jsonl")
    print(f"  page chunks       : {n_page}")
    print(f"  subpage chunks    : {n_sub}   (concrete facts: amounts, deadlines, eligibility)")
    print(f"  provisions chunks : {n_ocr}   (OCR'd rule PDFs)")
    print(f"  duplicates removed: {len(records) - len(deduped)}")
    print(f"  TOTAL             : {len(deduped)}")


if __name__ == "__main__":
    main()
