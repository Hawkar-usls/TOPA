# TOPA Provenance

TOPA is a consolidation repository. It does not erase where its material came from.

## Source repositories

The bootstrap process currently imports from five JANUS repositories:

| Source | Role | Import target |
|---|---|---|
| `Hawkar-usls/janus-meta-registry` | historical TOPA receipts, case corpora and falsification passes | `corpus/meta-registry/` |
| `Hawkar-usls/Janus_Genesis` | canonical TOPA epistemic foundation | `protocols/` |
| `Hawkar-usls/Janus-Demiurge` | 17-Scout TOPA protocol and orchestration integration | `integrations/Janus-Demiurge/` |
| `Hawkar-usls/janus-distributed-ai-swarm` | TOPA claim-envelope validator and runtime integration | `integrations/janus-distributed-ai-swarm/` |
| `Hawkar-usls/Janus-Cosmos`, branch `janus-tesla-sweep` | Tesla Sweep / TOPA Hunt state, inputs and results | `research/tesla-sweep/` |

The exact commit of each upstream snapshot and SHA-256 of imported files are generated into `registry/UPSTREAM-SNAPSHOT.json` and `registry/TOPA-CORPUS-INDEX.json`.

## Copy policy

Imported files are copied as historical/source snapshots. They should not be silently edited to match a later conclusion.

If an imported artifact is wrong or incomplete:

```text
DO NOT rewrite old evidence
→ add correction receipt
→ add new version
→ mark supersession
→ preserve both states
```

This follows the JANUS preservation rule:

> **PRESERVE THE PATH, NOT ONLY THE DESTINATION.**

## Authority policy

A copied artifact does not become more authoritative merely because it now appears in two repositories.

```text
COPY_COUNT != SOURCE_COUNT
MIRROR != INDEPENDENT_REPLICATION
UPSTREAM_SNAPSHOT != NEW_EVIDENCE
```

For exact historical authorship and chronology, the original upstream commit remains part of the evidence chain.

## Fiction boundary

The `Prey (2006)` Art Bell material is retained as a design pattern for information handling. It is explicitly fiction and must never be counted as empirical evidence for real anomaly claims.

## Model boundary

TOPA may use JANUS models and Scouts to route, compare, summarize, attack or synthesize evidence. Those operations do not manufacture new independent observations.

```text
MODEL_OUTPUT = ANALYTICAL CONTEXT
MODEL_OUTPUT != SENSOR RECORD
MODEL_AGREEMENT != WORLD TRUTH
```

## Import automation

`.github/workflows/bootstrap-topa.yml` performs a reproducible snapshot import. It is intentionally narrow:

- copy explicit `JANUS-TOPA-*.json` artifacts from the meta-registry;
- copy the canonical foundation and known TOPA runtime/protocol files;
- copy the `janus-tesla-sweep` research data tree;
- compute source commit IDs and file hashes;
- generate a corpus index;
- commit only when the imported snapshot changes.

The workflow does not score scientific truth. It only consolidates repository state and provenance.
