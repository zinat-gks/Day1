import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import trafilatura
import pandas as pd
import time
import re
from pathlib import Path

BASE_URL = "https://yessenovfoundation.org"
START_URL = "https://yessenovfoundation.org/en/about-us/programs/"

# We only want useful pages, not the whole website
USEFUL_KEYWORDS = [
    "program",
    "scholarship",
    "internship",
    "data-lab",
    "yessenov",
    "grant",
    "orleu",
    "launch-pad",
    "find-your-way",
    "english-language",
]

MAX_PAGES = 40

Path("data").mkdir(exist_ok=True)


def is_useful_url(url: str) -> bool:
    """
    Keep only Yessenov Foundation pages that look related to programs/grants.
    """
    parsed = urlparse(url)

    if parsed.netloc != "yessenovfoundation.org":
        return False

    if "/en/" not in url:
        return False

    bad_extensions = [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".zip"]
    if any(url.lower().endswith(ext) for ext in bad_extensions):
        return False

    lower_url = url.lower()
    return any(keyword in lower_url for keyword in USEFUL_KEYWORDS)


def get_links(url: str) -> list[str]:
    """
    Get links from one page.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Could not open {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        full_url = urljoin(url, a["href"])
        full_url = full_url.split("#")[0]

        if is_useful_url(full_url):
            links.append(full_url)

    return list(set(links))


def clean_text(text: str) -> str:
    """
    Clean extra spaces and repeated newlines.
    """
    if not text:
        return ""

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_page_text(url: str) -> dict:
    """
    Extract title and main text from a page.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(
            downloaded,
            include_links=False,
            include_tables=True,
            include_comments=False,
        )
    except Exception as e:
        print(f"Extraction failed for {url}: {e}")
        text = ""

    text = clean_text(text)

    title = ""
    try:
        html = requests.get(url, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")
        if soup.title:
            title = soup.title.get_text(strip=True)
    except Exception:
        pass

    return {
        "url": url,
        "title": title,
        "text": text,
        "text_length": len(text),
    }


def main():
    visited = set()
    queue = [START_URL]
    rows = []

    while queue and len(visited) < MAX_PAGES:
        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)
        print(f"\n[{len(visited)}] Parsing: {url}")

        page = extract_page_text(url)

        if page["text_length"] > 300:
            rows.append(page)
            print(f"Saved text length: {page['text_length']}")
        else:
            print("Skipped: too little useful text")

        new_links = get_links(url)
        for link in new_links:
            if link not in visited and link not in queue:
                queue.append(link)

        time.sleep(1)

    df = pd.DataFrame(rows)
    df.to_csv("data/yessenov_pages.csv", index=False)

    print("\nDone!")
    print(f"Saved {len(df)} pages to data/yessenov_pages.csv")


if __name__ == "__main__":
    main()