"""
Stage 2 scraper: go one level DEEPER than the program overview pages.

The top-level program pages (e.g. /yessenov-scholarship/) are just descriptions.
The concrete facts (amounts, deadlines, eligibility, GPA, documents) live on the
year sub-pages behind the "Apply" button (e.g. /...-2026/), and in the
"Program Provisions" PDFs linked at the bottom of those sub-pages.

This script:
  1. Starts from the program pages already in yessenov_pages.csv.
  2. Follows links that go DEEPER under the same program (the year/apply pages).
  3. Extracts clean text from each sub-page  -> data/program_subpages.csv
  4. Finds + downloads every PDF (provisions/program) -> data/files/*.pdf
                                                       -> data/files/manifest.csv
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, unquote
import trafilatura
import pandas as pd
import re
import time
from pathlib import Path

Path("data/files").mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (research; YDL2026 student project)"}

# The 16 program overview pages we already know about.
SEEDS = [
    "https://yessenovfoundation.org/en/about-us/programs/knowledge/books/",
    "https://yessenovfoundation.org/en/about-us/programs/resources/yessenov-launch-pad/",
    "https://yessenovfoundation.org/en/about-us/programs/science/yessenov-scholarship/",
    "https://yessenovfoundation.org/en/about-us/programs/science/research-internships/",
    "https://yessenovfoundation.org/en/about-us/programs/science/orleu/",
    "https://yessenovfoundation.org/en/about-us/programs/knowledge/books/scientific-conferences/",
    "https://yessenovfoundation.org/en/about-us/programs/resources/yessenov-data-lab/",
    "https://yessenovfoundation.org/en/about-us/programs/resources/internships-in-it-startups/",
    "https://yessenovfoundation.org/en/about-us/programs/science/graduate-studies/",
    "https://yessenovfoundation.org/en/about-us/programs/knowledge/chess/",
    "https://yessenovfoundation.org/en/about-us/programs/knowledge/yessenov-lectures/find-your-way/",
    "https://yessenovfoundation.org/en/about-us/programs/science/travel-grants/",
    "https://yessenovfoundation.org/en/about-us/programs/knowledge/english-language-program/",
]


def get(url):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r


def real_pdf_url(href: str) -> str | None:
    """Resolve a link to a direct PDF URL, unwrapping the ?download=&kcccount= form."""
    low = href.lower()
    if "kcccount=" in low:
        q = parse_qs(urlparse(href).query)
        if "kcccount" in q:
            cand = unquote(q["kcccount"][0])
            if cand.lower().endswith(".pdf"):
                return cand
    if low.endswith(".pdf"):
        return href
    return None


def child_links(seed: str, soup: BeautifulSoup) -> list[str]:
    """Links that go DEEPER under the same program path (the year/apply pages)."""
    base_path = urlparse(seed).path.rstrip("/")
    out = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(seed, a["href"]).split("#")[0].rstrip("/") + "/"
        p = urlparse(full)
        if p.netloc != "yessenovfoundation.org":
            continue
        path = p.path.rstrip("/")
        # deeper than the seed, same prefix, and not a language switch
        if path.startswith(base_path + "/") and path != base_path:
            if "/en/" in full:
                out.add(full)
    return sorted(out)


def main():
    subpages = []          # {program, url, title, text, text_length}
    pdfs = {}              # pdf_url -> {program, source_page, filename}

    for seed in SEEDS:
        program = seed.rstrip("/").split("/")[-1]
        try:
            soup = BeautifulSoup(get(seed).text, "html.parser")
        except Exception as e:
            print(f"! seed failed {seed}: {e}")
            continue

        kids = child_links(seed, soup)
        print(f"\n[{program}] {len(kids)} sub-pages")

        for url in kids:
            try:
                html = get(url).text
            except Exception as e:
                print(f"  ! {url}: {e}")
                continue

            text = trafilatura.extract(html, include_tables=True,
                                       include_links=False, include_comments=False) or ""
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            s = BeautifulSoup(html, "html.parser")
            title = s.title.get_text(strip=True) if s.title else ""

            if len(text) > 200:
                subpages.append({"program": program, "url": url, "title": title,
                                 "text": text, "text_length": len(text)})
                print(f"  + text {len(text):>5}  {url.split('/')[-2]}")

            # collect PDFs on this sub-page
            for a in s.find_all("a", href=True):
                pdf = real_pdf_url(urljoin(url, a["href"]))
                if pdf and pdf not in pdfs:
                    label = a.get_text(strip=True) or "file"
                    fname = f"{program}__{Path(urlparse(pdf).path).name}"
                    pdfs[pdf] = {"program": program, "source_page": url,
                                 "label": label, "filename": fname}
            time.sleep(0.7)

    # download PDFs
    print(f"\nDownloading {len(pdfs)} PDFs...")
    manifest = []
    for pdf_url, meta in pdfs.items():
        dest = Path("data/files") / meta["filename"]
        try:
            r = get(pdf_url)
            dest.write_bytes(r.content)
            meta["bytes"] = len(r.content)
            meta["pdf_url"] = pdf_url
            manifest.append(meta)
            print(f"  v {meta['filename']}  ({len(r.content)//1024} KB)  [{meta['label'][:30]}]")
        except Exception as e:
            print(f"  ! {pdf_url}: {e}")
        time.sleep(0.5)

    pd.DataFrame(subpages).to_csv("data/program_subpages.csv", index=False)
    pd.DataFrame(manifest).to_csv("data/files/manifest.csv", index=False)
    print(f"\nDone. {len(subpages)} sub-pages -> data/program_subpages.csv")
    print(f"      {len(manifest)} PDFs -> data/files/  (see manifest.csv)")


if __name__ == "__main__":
    main()
