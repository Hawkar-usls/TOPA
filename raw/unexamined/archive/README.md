# TOPA raw / unexamined archive lane

This directory is append-only discovery memory for **unexamined** archival material.

Allowed in Git:
- JSON / JSONL / NDJSON metadata
- public extracted text or bounded snippets
- SHA-256 receipts
- official source URLs and binary pointers
- SPIDER graph receipts / bounded boards

Not mirrored automatically:
- multi-megabyte / multi-gigabyte ZIP, PDF, image, video, or audio corpora
- restricted or non-public material

Large official objects remain at the source and are represented by provenance pointers and hashes when fetched. This keeps the repository reproducible without turning GitHub into an uncontrolled binary mirror.

Scientific firewall:

`DECLASSIFICATION_IS_PROVENANCE_NOT_TRUTH`

`SEARCH_HIT_IS_NOT_EVIDENCE`

`GRAPH_EDGE_IS_NOT_CAUSATION`

`SEMANTIC_SIMILARITY_IS_NOT_MECHANISM`

`GRAPH_DENSITY_IS_NOT_EVIDENCE`

Every new record begins with `review_state = UNEXAMINED`. Weak SPIDER edges are routing leads only and may be deleted or downgraded by later evidence.
