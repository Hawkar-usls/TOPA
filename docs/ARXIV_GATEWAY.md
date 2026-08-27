# TOPA arXiv Gateway

TOPA now has a provenance-preserving research discovery lane for arXiv.

## What it does

`tools/topa_arxiv_gateway.py` can:

1. search the official arXiv Atom API for an arbitrary topic or raw arXiv query;
2. preserve response hashes and per-record hashes;
3. append retrieved metadata to a JSONL research corpus;
4. rebuild a local embedded full-text index;
5. rank the locally accumulated corpus with Tantivy BM25;
6. fall back to SQLite FTS5 when Tantivy is unavailable;
7. emit an `ARXIV_RESEARCH_CANDIDATE` queue for TOPA investigation routing.

The local index is disposable and reproducible. The JSONL corpus + receipts are the durable provenance layer.

## Why Tantivy

Tantivy is an embedded Rust full-text search library inspired by Lucene. It is MIT licensed, fast, incremental, and does not require a separate search-server process. TOPA uses the maintained Python bindings (`tantivy==0.26.0`) when available.

SQLite FTS5 remains the zero-extra-service fallback.

## One-command topic investigation

```bash
python -m pip install -r tools/requirements-arxiv-gateway.txt
python tools/topa_arxiv_gateway.py investigate \
  "historical photographic plate artifacts" \
  --work-dir work/topa-arxiv/plate-artifacts \
  --limit 100
```

This writes:

```text
work/topa-arxiv/plate-artifacts/
  arxiv-corpus.jsonl
  arxiv-research-candidate-queue.jsonl
  arxiv-investigation-receipt.json
  tantivy-index/          # or arxiv-index.sqlite fallback
```

A later query can search the local memory directly:

```bash
python tools/topa_arxiv_gateway.py local-search \
  work/topa-arxiv/plate-artifacts/tantivy-index \
  "scan edge morphology duplicate plates" \
  --engine tantivy \
  --limit 20
```

## Remote-only search

Plain-language topic:

```bash
python tools/topa_arxiv_gateway.py remote-search \
  "efferocytosis fibrosis mechanical signaling" \
  --limit 50 \
  --out work/efferocytosis.jsonl \
  --receipt work/efferocytosis.receipt.json
```

Raw arXiv query:

```bash
python tools/topa_arxiv_gateway.py remote-search \
  'cat:astro-ph.IM AND abs:"photographic plates"' \
  --raw-query \
  --limit 100
```

Supported arXiv fields include `all`, `ti`, `au`, `abs`, `co`, `jr`, `cat`, `rn`, and `id`.

## API discipline

TOPA enforces the arXiv recommendation to wait at least 3 seconds between sequential API calls. Individual pages are capped at 2,000 results. Large-scale mirroring should use arXiv bulk/OAI-PMH routes rather than repeated search requests.

## Scientific firewall

The gateway discovers literature; it does not certify it.

- arXiv paper != empirical truth;
- preprint status is provenance, not validation;
- search/BM25 rank != evidence strength;
- author or citation status != truth;
- no search result != proof of absence;
- failed fetch != proof of absence;
- negative and contradictory papers stay searchable;
- a paper claim must still pass TOPA claim-level source, method, falsification, and replication gates.

Canonical rules: `protocols/TOPA_ARXIV_GATEWAY_PROTOCOL-v1.0.json`.
