# TOPA Provenance

TOPA is a consolidation and research-routing repository. It does not erase where material came from and it does not turn a copied artifact, model output or linked repository into independent evidence.

## Managed upstream snapshots

The bootstrap process imports exact source snapshots from five JANUS surfaces:

| Source | Role | Import target |
|---|---|---|
| `Hawkar-usls/janus-meta-registry` | historical TOPA receipts, case corpora and falsification passes | `corpus/meta-registry/` |
| `Hawkar-usls/Janus_Genesis` | canonical TOPA epistemic foundation | `protocols/` |
| `Hawkar-usls/Janus-Demiurge` | 17-Scout TOPA protocol and orchestration integration | `integrations/Janus-Demiurge/` |
| `Hawkar-usls/janus-distributed-ai-swarm` | executable TOPA claim-envelope validator and runtime integration | `integrations/janus-distributed-ai-swarm/` |
| `Hawkar-usls/Janus-Cosmos`, branch `janus-tesla-sweep` | Tesla Sweep / TOPA Hunt state, inputs and results | `research/tesla-sweep/` |

Native TOPA research under `data/` and `hunts/` remains TOPA-native rather than being relabelled as upstream imports. Exact source commits and SHA-256 hashes are generated into `registry/UPSTREAM-SNAPSHOT.json` and `registry/TOPA-CORPUS-INDEX.json`.

## Habitat and methodological integrations

| Surface | TOPA role | Authority |
|---|---|---|
| `Hrain` | structural context for unexplained alignment | `authority_delta = 0` |
| `Demi_Head` | adversarial alignment arbitration | cannot promote alignment to causality |
| `AIFC` | independent-future / frozen-prediction evidence gate | protocol only; no retrocausality claim |
| `Echo-Pyramid` | model-versus-measurement acoustic boundary | model is not measurement |
| `tranception` | methodological donor: retrieval, validation, mirror scoring, aggregate-vs-case discipline | no TOPA case evidence authority |
| `SkinGPT` | sensor calibration / ground-truth discipline | private source; private bytes are not mirrored |

The machine-readable topology is in `.janus/TOPA_NODE_MANIFEST.json` and `registry/ACCOUNT-WIDE-TOPA-MAP.json`.

## Copy policy

Imported files are preserved as historical/source snapshots. They must not be silently edited to fit a later conclusion.

```text
DO NOT rewrite old evidence
→ add correction receipt
→ add new version
→ mark supersession
→ preserve both states
```

> **PRESERVE THE PATH, NOT ONLY THE DESTINATION.**

## Authority policy

```text
COPY_COUNT != SOURCE_COUNT
MIRROR != INDEPENDENT_REPLICATION
UPSTREAM_SNAPSHOT != NEW_EVIDENCE
MODEL_OUTPUT != SENSOR_RECORD
MODEL_AGREEMENT != WORLD_TRUTH
HABITAT_LINK != COMMAND_AUTHORITY
```

## Private-source boundary

TOPA is public. Private repositories are therefore not mirrored into it by default. `Hawkar-usls/SkinGPT` is represented only by public-safe role/boundary metadata in `integrations/SkinGPT/PRIVATE_SOURCE_BOUNDARY.json`.

```text
PRIVATE_SOURCE != PUBLIC_MIRROR_PERMISSION
PRIVATE_BYTES_STAY_PRIVATE
CREDENTIALS_NEVER_ENTER_HABITAT
```

## Upstream-derived repository boundary

```text
OWNED_REPOSITORY != ORIGINAL_AUTHORSHIP_OF_ALL_CONTENT
UPSTREAM_MIRROR != JANUS_ORIGINAL_RESEARCH
```

`tranception` is a canonical example: TOPA imports methodological lessons only. Its underlying protein-language-model research remains upstream work.

## Fiction and symbolic boundary

```text
FICTIONAL_DESIGN_PATTERN != EMPIRICAL_EVIDENCE
SYMBOLIC_CONTEXT != PHYSICAL_MEASUREMENT
ORACLE_OUTPUT != INDEPENDENT_WITNESS
```

## Import automation

`.github/workflows/bootstrap-topa.yml` performs a reproducible managed snapshot import and validates the Habitat contract before ingestion.

It preserves native `data/` and `hunts/`, rebuilds only managed upstream copies, indexes the local Habitat/integration surface, and never treats workflow success as scientific truth or mathematical proof.
