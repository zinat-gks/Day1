# Knowledge Base Audit

Audit date: 2026-06-19

## Files

- Original bot file checked: `data/knowledge_base.jsonl`
- Cleaned candidate file created separately: `data/knowledge_base_audited.jsonl`
- Cleaned candidate builder: `merge_all_audited.py`

## Original File Status

- Records: 467
- JSON validity: 467 valid / 0 invalid
- Schema: `source_title`, `source_url`, `source_type`, `program`, `chunk_id`, `text`
- Source types:
  - `page`: 123
  - `subpage`: 142
  - `provisions`: 202
- Unique source URLs: 118
- Live URL check: 118 / 118 returned HTTP 200
- Live source types: 100 HTML pages, 18 PDFs
- Latest WordPress posts checked through 2026-06-05; latest titles are represented in the KB.
- Provision PDF hash check: 18 / 18 local PDFs match the current remote PDFs.

## Original File Issues Found

- No explicit `keywords` field exists in the original schema.
- Two exact duplicate text chunks are present.
- One source URL has duplicate chunk IDs because the same page appears as both `page` and `subpage`.
- Several chunks are raw 1200-character windows, so many chunks start or end mid-word.
- 27 chunks are under 120 characters; most are tail fragments, counters, or broken endings.
- Some chunks include boilerplate such as `Seen by`, `Downloaded`, and `Size`.
- Live HTML snippet check matched 242 / 254 HTML chunks. The 12 misses are mostly category/listing pages or tail fragments containing counters/broken text, not core provision facts.

## Cleaned Candidate

`data/knowledge_base_audited.jsonl` was created as a separate candidate file and does not replace the original bot file.

- Records: 373
- JSON validity: 373 valid / 0 invalid
- Schema adds: `keywords`
- Source URLs preserved: 118
- Source types:
  - `page`: 101
  - `subpage`: 108
  - `provisions`: 164
- Empty required fields: 0
- Empty keyword lists: 0
- Short chunks under 120 characters: 0
- Boilerplate `Seen by`: 0

## Recommendation

Keep `data/knowledge_base.jsonl` unchanged for the bot if the bot expects the original schema/count.
Use `data/knowledge_base_audited.jsonl` only after confirming the bot accepts the added `keywords` field and the lower, cleaner chunk count.
