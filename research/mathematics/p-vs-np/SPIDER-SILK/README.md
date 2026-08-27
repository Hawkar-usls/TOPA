# SPIDER-SILK — read-only research layer beside the P-vs-NP project

This directory belongs to TOPA/SPIDER, not to the algorithm-development lane.

## Hard boundary

SPIDER may search, index, compare, deduplicate, hash, route, annotate, preserve negative results, improve its own search tooling, and prepare handoff material for the separate algorithm-development dialogue.

SPIDER must **not** modify proof-selector logic, transition semantics, theorem status, runtime strategy, or proof lemmas in the target algorithm.

## Two operational metaphors

### ArtMoney → Differential State Narrowing

Use repeated controlled observations to narrow an already-materialized explicit state down to components whose changes track a failure or hostile transition. This is diagnostic only; it is not a polynomial search over an implicit `2^n` SAT assignment space.

### Total Commander → Dual-Pane Structural Forensics

Use a read-only `GOOD/reference | BAD/hostile` two-pane view. Compare canonical contents, hide equal regions, inspect only changed/missing/extra structures, verify integrity with hashes, filter to relevant branches, and allow plugin-like extractors for new trace/document formats.

`Synchronize dirs` is used only as a metaphor for **reconciliation preview**. SPIDER never applies synchronization back into the algorithm state.

## Folder contract

- `sources/` — append-only source seeds and retrieval metadata.
- `dossiers/` — curated SILK JSON findings.
- `handoff/` — compact state for the separate algorithm dialogue.
- `runs/` — receipts/manifests from SPIDER searches when frozen permanently.

## Laws

- `SPIDER_IS_OBSERVER_AND_RESEARCHER_NOT_ALGORITHM_AUTHOR`
- `COMPARE_DOES_NOT_MODIFY`
- `SYNC_PREVIEW_IS_NOT_SYNC_APPLY`
- `SEARCH_HIT_IS_NOT_EVIDENCE`
- `MINIMAL_DIFF_IS_NOT_CAUSAL_PROOF`
- `HASH_MATCH_IS_A_SCREEN_NOT_SEMANTIC_AUTHORITY`
- `LIKELY_INVARIANT_IS_NOT_PROVED_INVARIANT`
- `OFFLINE_ORACLE_IS_NOT_ALLOWED_TO_HIDE_RUNTIME_COST`
- `P_VS_NP_IS_OPEN`
