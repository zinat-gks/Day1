"""
Central config. Secrets are read from the gitignored 'API kays' file (or env
vars), never hardcoded here. This file is safe to commit.

Override anything via environment variables, e.g.:
    export CHAT_KEY=sk-...
"""

import os
import re
from pathlib import Path

SECRETS_FILE = Path(__file__).parent / "API kays"


def _load_secrets_text() -> str:
    try:
        return SECRETS_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


_TXT = _load_secrets_text()


def _find(pattern: str, default: str = "") -> str:
    m = re.search(pattern, _TXT)
    return m.group(1).strip() if m else default


# --- Endpoints (OpenAI-compatible, llm.alem.ai) ---
CHAT_URL = os.getenv("CHAT_URL", "https://llm.alem.ai/v1/chat/completions")
EMB_URL = os.getenv("EMB_URL", "https://llm.alem.ai/v1/embeddings")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gemma4")
EMB_MODEL = os.getenv("EMB_MODEL", "text-1024")
EMB_DIM = 1024

# --- Keys (env var wins; otherwise parsed from 'API kays') ---
# Chat: prefer the "Authorization: Bearer ..." line, fall back to "ключ ... gemma4".
CHAT_KEY = os.getenv("CHAT_KEY") or _find(r"Authorization:\s*Bearer\s+(sk-[\w-]+)") \
    or _find(r"gemma4[:\s]+(sk-[\w-]+)")
# Alternate chat key candidate (the other one in the file), used as a fallback on 401.
CHAT_KEY_ALT = os.getenv("CHAT_KEY_ALT") or _find(r"ключ от gemma4:\s*(sk-[\w-]+)")

EMB_KEY = os.getenv("EMB_KEY") or _find(r"text-1024 key:\s*(sk-[\w-]+)")

MAILERSEND_KEY = os.getenv("MAILERSEND_KEY") or _find(r"(mlsn\.[0-9a-f]+)")
FROM_EMAIL = os.getenv("FROM_EMAIL", "info@app.commit.kz")
FROM_NAME = os.getenv("FROM_NAME", "Yessenov Data Lab")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL") or _find(r"ADMIN_EMAIL[\"',=\s]+[\"']?([\w.+-]+@[\w.-]+)") \
    or "zinatgks@gmail.com"

KB_PATH = os.getenv("KB_PATH", "data/knowledge_base_audited.jsonl")
INDEX_PATH = os.getenv("INDEX_PATH", "data/kb_embeddings.npz")


def masked(key: str) -> str:
    if not key:
        return "(missing)"
    return key[:6] + "…" + key[-4:]
