# TOPA Archive Gateway + SPIDER

TOPA now has a provenance-first archive lane that can ingest public official archival metadata into JSONL, index it, and weave a weak-evidence discovery graph.

## Components

- `tools/topa_archive_gateway.py` — NARA/CIA/NSA/FBI provider gateway
- `tools/topa_spider.py` — document/entity/date/place graph
- `tools/topa_federated_search.py` — one local search surface across TOPA repo memory + arXiv corpus + archive corpus
- `tools/topa_json_rails.py` — JSON/JSONL/NDJSON and gzip/bzip2 rails
- `protocols/TOPA_ARCHIVE_GATEWAY_SPIDER_PROTOCOL_v1.0.json` — frozen epistemic contract

## Archive ingestion

Bounded live run:

```bash
python tools/topa_archive_gateway.py ingest \
  --providers nara,cia,nsa,fbi \
  --limit 25 \
  --expand-nara \
  --out work/archive/archive.jsonl \
  --receipt work/archive/receipt.json
```

For NARA, raising `--limit` allows enumeration of all metadata JSON links currently published on the official UAP bulk-download page. Large ZIP/PDF payloads are not mirrored automatically into GitHub.

## Weave SPIDER

```bash
python tools/topa_spider.py weave \
  --input work/archive/archive.jsonl \
  --nodes work/archive/nodes.jsonl \
  --edges work/archive/edges.jsonl \
  --receipt work/archive/spider.json
```

SPIDER permits weak edges:

- `MENTIONS`
- `SHARED_ENTITY`
- `SOURCE_LINEAGE`
- `SEMANTIC_SIMILARITY`

A weak edge is a **routing lead**, not evidence of causality. Graph density cannot upgrade a claim.

## Federated search

If the repository assimilation index, arXiv corpus and archive corpus exist:

```bash
python tools/topa_federated_search.py build \
  --repo work/repo-index.jsonl \
  --arxiv work/arxiv/arxiv-corpus.jsonl \
  --archive work/archive/archive.jsonl \
  --engine tantivy \
  --out work/federated-index

python tools/topa_federated_search.py search \
  --engine tantivy \
  --index work/federated-index \
  --query "tachyon Ukraine UAP" \
  --limit 25
```

SQLite FTS5 remains the fallback when Tantivy is unavailable.

## Raw / unexamined lane

`raw/unexamined/archive/` stores only manageable metadata/text/hashes/manifests and bounded SPIDER receipts. Huge official binaries remain source pointers.

## Current provider ceiling

- NARA UAP bulk metadata: exhaustive discovery from the official UAP bulk-download landing page is implemented.
- CIA Reading Room: exact document/PDF seed ingestion is implemented; exhaustive collection crawling is not yet claimed.
- NSA UFO/FOIA: official landing-page harvesting is implemented; deep enumeration is not yet claimed.
- FBI Vault UFO: official landing-page harvesting is implemented; deep enumeration is not yet claimed.

See `registry/TOPA_ARCHIVE_PROVIDER_REGISTRY_v1.0.json`.

## Laws

`DECLASSIFICATION_IS_PROVENANCE_NOT_TRUTH`

`SEARCH_HIT_IS_NOT_EVIDENCE`

`GRAPH_EDGE_IS_NOT_CAUSATION`

`SEMANTIC_SIMILARITY_IS_NOT_MECHANISM`

`GRAPH_DENSITY_IS_NOT_EVIDENCE`

`REPEATED_SAME_SOURCE_IS_NOT_INDEPENDENT_WITNESS`
