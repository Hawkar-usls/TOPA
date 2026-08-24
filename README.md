<div align="center">

# TOPA
### JANUS anomaly research laboratory · provenance · falsification · reproducible case files

![Status](https://img.shields.io/badge/status-ACTIVE__PROTOTYPE-2ea043)
![Method](https://img.shields.io/badge/method-falsification--first-1f6feb)
![Evidence](https://img.shields.io/badge/evidence-provenance--bound-8250df)
![World truth](https://img.shields.io/badge/world%20truth-not%20implied-8c959f)

**NOTHING SUPERNATURAL — ONLY NATURE NOT YET UNDERSTOOD. 🌀**

</div>

## Status

**ACTIVE_PROTOTYPE.** TOPA is the dedicated JANUS research surface for unusual, anomalous, paranormal-labelled and otherwise unexplained reports.

The method, machine-readable foundation, case corpus and epistemic validator are implemented. Individual cases remain bounded by their evidence. Repository presence, source count, model agreement or a surviving anomaly **does not establish paranormal, extraterrestrial, prophetic, retrocausal or other extraordinary world-truth claims**.

## Abstract

TOPA does not begin by deciding whether a strange report is true, false, mundane or extraordinary. It begins by preserving exactly **what was reported**, **who or what the source was**, **when and where it allegedly happened**, and **which parts are observation versus interpretation**.

Then both the extraordinary explanation **and the strongest conventional explanation** are attacked.

```text
REPORT
  → PRESERVE RAW PROVENANCE
  → CLASSIFY CHANNEL / FIRSTHAND / HEARSAY
  → FREEZE TIME + LOCATION + CLAIM
  → SPLIT OBSERVATION FROM INTERPRETATION
  → BUILD COMPETING HYPOTHESES
  → TEST MUNDANE MODELS EARLY
  → DEFINE FALSIFIERS
  → CHECK SOURCE + SENSOR INDEPENDENCE
  → ATTACK BOTH SIDES
  → UPDATE CONFIDENCE
  → RESOLVE / FALSIFY / KEEP UNRESOLVED
  → SPIRAL AND REATTACK
```

The core law is deliberately simple:

```text
ANOMALY IS A QUESTION, NOT A CONCLUSION.
UNKNOWN != SUPERNATURAL
NOT_REFUTED != TRUE
MULTI_CHANNEL != MULTI_SOURCE
MISSING_DATA_STAYS_MISSING
I_DO_NOT_KNOW = VALID OUTPUT
```

## Evidence ladder

TOPA uses an observation ladder as an **evidence-strength annotation**, not as an automatic explanation selector.

| Level | Meaning |
|---|---|
| `O0` | a claim/report exists |
| `O1` | firsthand report with time/location |
| `O2` | multiple witnesses; independence unclear |
| `O3` | independent contemporaneous witnesses or external record |
| `O4` | physical, digital or instrument record |
| `O5` | controlled reproducibility |

A high ladder position can establish that an event was well documented while still leaving its cause unresolved.

## Current TOPA corpus

The repository is bootstrapped from the already-existing JANUS TOPA lineage and keeps exact upstream snapshots with provenance.

| Family | Current role |
|---|---|
| **TOPA Foundation v1.2** | canonical epistemic laws, claim pipeline, promotion gates and prediction freeze rules |
| **Art Bell real-caller corpus v1.2** | living archival corpus with **136 sourceable caller records**; a call occurring proves the report was made, not the claim |
| **Art Bell / Prey observer node** | fictional information-handling reference pattern; explicitly **not empirical evidence** |
| **Donald E. Keyhoe evidence audit** | biography, major case audit, evidence ladder and Egypt cross-reference pass |
| **RB-47 / Kinross / Ras el-Kanayis forensic triad** | minute-level source/sensor/geometry reconstruction with open gates |
| **Adversarial falsification pass** | attempts to destroy both extraordinary and conventional explanations before promotion |
| **RB-47 kill pass** | later attack that revoked the earlier hard-survivor ranking and demoted the case to `UNRESOLVED_NONEXOTIC_HIGH_VALUE` |
| **Tesla Sweep / TOPA Hunt** | open-signal anomaly search in `Janus-Cosmos`, including preregistration, states, inputs and results |
| **J1832 mechanism handoff** | natural-mechanism synthesis for the ultralong-period neutron-star candidate; favored synthesis remains **not proven** |
| **Kenshi × 17 Scouts** | distributed provenance discipline: synchronize state, never collapse identity or evidence independence |

The RB-47 sequence is an important design test for TOPA itself: an earlier pass ranked it highly, then the next adversarial pass found a sensor-owner contradiction, terrestrial-radar compatibility and missing raw-channel independence strong enough to **lower** the classification. TOPA is working correctly when new evidence can damage its own favorite hypothesis.

## Repository layout

```text
TOPA/
├── README.md
├── PROJECT_STATUS.json
├── docs/
│   ├── METHOD.md
│   ├── STATUS.md
│   └── PROVENANCE.md
├── protocols/
│   └── TOPA_FOUNDATION.json
├── corpus/
│   └── meta-registry/          # exact JANUS-TOPA-* archival artifacts
├── research/
│   └── tesla-sweep/            # exact Janus-Cosmos janus-tesla-sweep data snapshot
├── integrations/
│   ├── Janus-Demiurge/
│   └── janus-distributed-ai-swarm/
├── registry/
│   ├── TOPA-CORPUS-INDEX.json
│   └── UPSTREAM-SNAPSHOT.json
└── .github/workflows/
    └── bootstrap-topa.yml
```

Imported material is preserved as an upstream snapshot. TOPA-specific interpretation should be added as a new version or receipt rather than silently rewriting historical evidence.

## Reviewer path

For a fast audit, read in this order:

1. [`protocols/TOPA_FOUNDATION.json`](protocols/TOPA_FOUNDATION.json) — canonical laws.
2. [`docs/METHOD.md`](docs/METHOD.md) — how claims are admitted, attacked and demoted.
3. [`docs/STATUS.md`](docs/STATUS.md) — current case map and supersession notes.
4. [`registry/TOPA-CORPUS-INDEX.json`](registry/TOPA-CORPUS-INDEX.json) — machine-readable imported corpus index.
5. [`corpus/meta-registry/`](corpus/meta-registry/) — exact historical receipts and case dossiers.
6. [`research/tesla-sweep/`](research/tesla-sweep/) — current signal-hunt branch snapshot.
7. [`integrations/janus-distributed-ai-swarm/topa_epistemic_router.py`](integrations/janus-distributed-ai-swarm/topa_epistemic_router.py) — executable claim-envelope validator.

Run the validator self-test with:

```bash
python integrations/janus-distributed-ai-swarm/topa_epistemic_router.py
```

Expected terminal marker:

```text
JANUS_TOPA_EPISTEMIC_ROUTER_V1_2_SELF_TEST=PASS
```

That pass validates the **epistemic envelope rules only**. It does not validate the truth of any case in the corpus.

## Promotion boundary

A TOPA claim may not be promoted merely because:

- many people repeated it;
- many JANUS agents saw the same source;
- a witness had high institutional status;
- a source identified itself as an insider, alien, time traveler, oracle, government employee or similar;
- the conventional explanation failed;
- the case remains unexplained;
- a model produced a coherent story;
- an archive is incomplete;
- multiple channels ultimately depend on the same source or sensor chain.

A promoted interpretation must remain vulnerable to a named observation or test that could lower confidence. If no such route exists, TOPA raises `CLOSED_BELIEF_LOOP_WARNING`.

## Preservation law

> **PRESERVE THE PATH, NOT ONLY THE DESTINATION.**

Failed predictions, ordinary resolutions, corrections, missing-source gates, contradictory records, negative results and demoted survivors remain part of the corpus. Historical artifacts are not rewritten to make the current theory look cleaner.

## Upstream lineage

TOPA currently consolidates material from:

- [`Hawkar-usls/janus-meta-registry`](https://github.com/Hawkar-usls/janus-meta-registry) — archival TOPA receipts and case corpora;
- [`Hawkar-usls/Janus_Genesis`](https://github.com/Hawkar-usls/Janus_Genesis) — canonical TOPA foundation;
- [`Hawkar-usls/Janus-Demiurge`](https://github.com/Hawkar-usls/Janus-Demiurge) — 17-Scout epistemic protocol;
- [`Hawkar-usls/janus-distributed-ai-swarm`](https://github.com/Hawkar-usls/janus-distributed-ai-swarm) — executable epistemic router;
- [`Hawkar-usls/Janus-Cosmos`](https://github.com/Hawkar-usls/Janus-Cosmos/tree/janus-tesla-sweep) — Tesla Sweep / TOPA Hunt research branch.

Exact source commits and imported-file hashes are recorded in [`registry/UPSTREAM-SNAPSHOT.json`](registry/UPSTREAM-SNAPSHOT.json).

## Claim discipline

```text
REPORT != EVENT TRUTH
ARCHIVE OCCURRENCE != CLAIM VALIDATION
SCHEMA_VALID != SCIENTIFICALLY_TRUE
MODEL CONSENSUS != INDEPENDENT REPLICATION
CORRELATION != CAUSATION
UNIDENTIFIED != EXTRAORDINARY
MUNDANE != AUTOMATICALLY TRUE
FICTIONAL DESIGN PATTERN != EMPIRICAL EVIDENCE
```

TOPA is intentionally allowed to end with **UNRESOLVED**.

## License and presentation

See [`LICENSE`](LICENSE). Presentation follows the account's public-repository standard: restrained academic/laboratory style, explicit evidence boundaries, visible negative results and machine-readable status. No institutional affiliation or endorsement is implied.
