# TOPA Sacred Scriptures

This branch contains the TOPA/JANUS sacred-text research surface.

Start here:

- [`research/sacred-scriptures/README.md`](research/sacred-scriptures/README.md)
- [`research/sacred-scriptures/CORPUS_MANIFEST.v0.1.json`](research/sacred-scriptures/CORPUS_MANIFEST.v0.1.json)
- [`research/sacred-scriptures/JANUS_COUNCIL_PROTOCOL.v0.1.json`](research/sacred-scriptures/JANUS_COUNCIL_PROTOCOL.v0.1.json)
- [`research/sacred-scriptures/INDEPENDENT_RESIDUAL_PROTOCOL.v0.1.json`](research/sacred-scriptures/INDEPENDENT_RESIDUAL_PROTOCOL.v0.1.json)
- [`research/sacred-scriptures/FLOOD_STEMMA_BLIND_TEST.v0.1.json`](research/sacred-scriptures/FLOOD_STEMMA_BLIND_TEST.v0.1.json)
- [`research/sacred-scriptures/FLOOD_SOURCE_GATES.v0.2.json`](research/sacred-scriptures/FLOOD_SOURCE_GATES.v0.2.json) — current source-gate authority
- [`research/sacred-scriptures/PRESCORE_SOURCE_FREEZE.v0.2.json`](research/sacred-scriptures/PRESCORE_SOURCE_FREEZE.v0.2.json) — current prescore authority
- [`research/sacred-scriptures/ANCIENT_WRITING_METHOD_BRIDGE.v0.2.json`](research/sacred-scriptures/ANCIENT_WRITING_METHOD_BRIDGE.v0.2.json) — current Linear A / Egyptian-record canary authority
- [`research/sacred-scriptures/PHILOLOGY_BASELINE.v0.1.json`](research/sacred-scriptures/PHILOLOGY_BASELINE.v0.1.json)
- [`research/sacred-scriptures/GRETIL_PROVENANCE_CORRECTION.v0.1.json`](research/sacred-scriptures/GRETIL_PROVENANCE_CORRECTION.v0.1.json)
- [`research/sacred-scriptures/CURRENT_SPRINT.v0.2.json`](research/sacred-scriptures/CURRENT_SPRINT.v0.2.json)
- [`research/sacred-scriptures/TOPA_FIRST_PASS.v0.1.json`](research/sacred-scriptures/TOPA_FIRST_PASS.v0.1.json)
- [`research/sacred-scriptures/JANUS_EXISTING_LINEAGE.v0.1.json`](research/sacred-scriptures/JANUS_EXISTING_LINEAGE.v0.1.json)
- [`research/sacred-scriptures/SOURCE_DISCOVERY_RECEIPTS.v0.1.json`](research/sacred-scriptures/SOURCE_DISCOVERY_RECEIPTS.v0.1.json)
- [`research/sacred-scriptures/PROVENANCE_AND_RIGHTS.md`](research/sacred-scriptures/PROVENANCE_AND_RIGHTS.md)

Historical `v0.1` prescore/source-gate/ancient-writing bridge artifacts remain preserved as superseded receipts and are not current authority.

Validators:

```bash
python tools/sacred_scripture_corpus_check.py
python tools/sacred_scripture_prescore_gate.py
```

The second validator is intentionally expected to report `PASS_LOCKED` while source-byte hashes and Linear A / Egyptian-record canary executions remain pending. A structurally valid freeze is **not** permission to SCORE.

The research target is open-ended. This branch does **not** claim that every sacred tradition, manuscript, oral lineage, canon or translation has already been captured.

```text
SACRED != SCIENTIFICALLY_PROVEN
OLD != INDEPENDENT
SIMILAR != SAME_SOURCE
DIFFERENT != CONTRADICTION
TRANSLATION != ORIGINAL
STRUCTURAL_SURVIVOR != TRANSLATION
STRONG_INTERNAL_SIGNAL != ADMITTED_RESULT
UTTERANCE_NUMBER != PARAGRAPH_NUMBER
UNKNOWN = VALID RESULT
```
