"""
Clean the scraped pages and re-chunk them.

Why: trafilatura grabbed the site's navigation menu on a handful of pages.
Those menu lines (links like "Programs", "Chess", "Travel Grants", language
toggles "Қаз/Рус/Eng", etc.) are noise: they repeat across pages, confuse
retrieval, and waste space in every chunk. We strip them line-by-line, then
re-chunk the cleaned text.

Inputs  : data/yessenov_pages.csv      (untouched)
Outputs : data/yessenov_pages_clean.csv
          data/yessenov_chunks_clean.jsonl
"""

import pandas as pd
import json
import re
from pathlib import Path

Path("data").mkdir(exist_ok=True)

# Exact menu/boilerplate lines to drop (matched case-insensitively, trimmed).
NAV_LINES = {
    "қаз", "рус", "eng", "(рус)", "(каз)", "(eng)",
    "menu", "bookshelf", "partners", "atf",
    "our mission:", "to develop kazakhstan's intellectual potential",
    "about us", "mission and reports", "founder", "programs", "программы",
    "the board of trustees", "the expert board", "s. yessenov", "biography",
    "publications in mass media", "multimedia", "newsfeed", "stories",
    "shakhmardan yessenov foundation",
    "internships", "yessenov scholarship", "english language",
    "yessenov data lab", "find your way", "yessenov launch pad",
    "2013-2024", "orleu", "chess", "conferences", "travel grants",
    "graduate studies", "yessenov lectures", "internships in it startups",
    "books", "almaty marathon",
}


def is_junk_line(line: str) -> bool:
    """True if a line is navigation/boilerplate rather than real content."""
    s = line.strip()
    if not s:
        return True
    low = s.lower()
    if low in NAV_LINES:
        return True
    if re.fullmatch(r"[×\-–—•|]+", s):          # separator-only lines
        return True
    if re.fullmatch(r"seen by:.*", low):         # view counters
        return True
    return False


def clean_text(text: str) -> str:
    """Drop junk lines, collapse blank runs."""
    if not isinstance(text, str):
        return ""
    kept = [ln.strip() for ln in text.split("\n") if not is_junk_line(ln)]
    cleaned = "\n".join(kept)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def chunk_text(text, chunk_size=1200, overlap=200):
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def main():
    df = pd.read_csv("data/yessenov_pages.csv")

    rows, records = [], []
    dropped_pages = []

    for _, row in df.iterrows():
        cleaned = clean_text(row["text"])

        # A page that's basically all-menu (like "Programs") leaves nothing.
        if len(cleaned) < 200:
            dropped_pages.append((row["title"], row["text_length"], len(cleaned)))
            continue

        rows.append({
            "url": row["url"],
            "title": row["title"],
            "text": cleaned,
            "text_length": len(cleaned),
        })

        for i, chunk in enumerate(chunk_text(cleaned)):
            records.append({
                "source_title": row["title"],
                "source_url": row["url"],
                "chunk_id": i,
                "text": chunk,
            })

    pd.DataFrame(rows).to_csv("data/yessenov_pages_clean.csv", index=False)
    with open("data/yessenov_chunks_clean.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Pages kept   : {len(rows)} / {len(df)}")
    print(f"Pages dropped: {len(dropped_pages)} (too little content after cleaning)")
    for title, before, after in dropped_pages:
        print(f"   - {title[:50]:50}  {before} -> {after} chars")
    print(f"Chunks       : {len(records)}  (was 129)")
    print("Wrote: data/yessenov_pages_clean.csv, data/yessenov_chunks_clean.jsonl")


if __name__ == "__main__":
    main()
