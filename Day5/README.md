# Yessenov Foundation Assistant — Day 5 (YDL 2026 Final Project)

A bilingual (EN/RU) Streamlit chatbot that answers questions about the
**Shakhmardan Yessenov Foundation's** grants, scholarships and programs —
grounded strictly in data collected from the foundation's website, with a
hard "I don't know" guardrail so it never invents deadlines, amounts or rules.

## Features
- **RAG** over a 373-chunk knowledge base using the `text-1024` embedding model
- **Hybrid retrieval** (semantic + keyword) with **typo correction** against the corpus
- **gemma4** chat with a strict anti-hallucination + out-of-scope prompt
- **Bilingual UI** — the whole interface localizes to Russian, not just answers
- **Source citations** under every answer
- Optional **email summary** to the admin (MailerSend, on explicit click only)
- Light / Dark themes in the Foundation's brand purple

## Data pipeline
| Step | Script | Output |
|------|--------|--------|
| Scrape overview pages | `scrape_yessenov.py` | `data/yessenov_pages.csv` |
| Clean nav-menu noise | `clean_chunks.py` | cleaned pages |
| Crawl apply sub-pages + download PDFs | `scrape_provisions.py` | `data/program_subpages.csv`, `data/files/` |
| OCR scanned provision PDFs (rus+kaz+eng) | `ocr_provisions.py` | `data/ocr/`, `data/ocr_provisions.jsonl` |
| Merge + chunk + dedup | `merge_all.py` | `data/knowledge_base_audited.jsonl` |
| Build embedding index | `build_index.py` | `data/kb_embeddings.npz` |

## Run it
```bash
pip install streamlit requests numpy
streamlit run app.py
```

## API keys (NOT in this repo)
The app reads keys from a local file named **`API kays`** (chat, embeddings,
MailerSend) — this file is **gitignored and never committed**. Create your own
`API kays` (or set the matching environment variables in `config.py`) to run it.

> Secrets policy: no API keys live in git. See `.gitignore`.
