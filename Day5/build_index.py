"""
Precompute embeddings for every chunk in the knowledge base and cache them.

Run once (re-run whenever knowledge_base.jsonl changes):
    python3 build_index.py

Output: data/kb_embeddings.npz  (vectors + parallel metadata)
"""

import json
import time
import numpy as np
import requests

import config as c

BATCH = 32


def embed_batch(texts):
    r = requests.post(
        c.EMB_URL,
        headers={"Authorization": f"Bearer {c.EMB_KEY}", "Content-Type": "application/json"},
        json={"model": c.EMB_MODEL, "input": texts},
        timeout=120,
    )
    r.raise_for_status()
    data = sorted(r.json()["data"], key=lambda d: d["index"])
    return [d["embedding"] for d in data]


def main():
    rows = [json.loads(l) for l in open(c.KB_PATH, encoding="utf-8")]
    texts = [r["text"] for r in rows]
    print(f"Embedding {len(texts)} chunks (model={c.EMB_MODEL}, batch={BATCH})...")

    vecs = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        for attempt in range(3):
            try:
                vecs.extend(embed_batch(batch))
                break
            except Exception as e:
                print(f"  batch {i} retry {attempt+1}: {e}")
                time.sleep(2)
        else:
            raise SystemExit(f"Failed on batch {i}")
        print(f"  {min(i+BATCH, len(texts))}/{len(texts)}")

    mat = np.array(vecs, dtype=np.float32)
    # L2-normalize so dot product == cosine similarity
    mat /= np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9

    keep = ("source_title", "source_url", "source_type", "program", "text")
    meta = [{**{k: r[k] for k in keep}, "keywords": r.get("keywords", [])} for r in rows]

    np.savez_compressed(c.INDEX_PATH, vectors=mat, meta=json.dumps(meta, ensure_ascii=False))
    print(f"Saved {mat.shape} -> {c.INDEX_PATH}")


if __name__ == "__main__":
    main()
