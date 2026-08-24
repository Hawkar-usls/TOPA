# TOPA Method

> **ANOMALY IS A QUESTION, NOT A CONCLUSION.**

TOPA is designed for reports that arrive already wrapped in emotionally or culturally loaded labels: *UFO*, *ghost*, *time traveler*, *prophecy*, *entity*, *secret technology*, *impossible signal*, *paranormal event*, and similar language.

The method strips the label away from the evidentiary core without discarding the report itself.

## 1. Preserve before interpreting

For every case, preserve the raw report and its provenance before normalization.

Minimum useful fields are:

```text
claim_id
origin_agent_id
raw_claim_text
claim_text
claim_kind
source_pointers
provenance_channel
firsthand_status
event_time
event_location
alternative_hypotheses
falsification_tests
status
confidence
```

A model may summarize or normalize a claim, but the raw ledger remains immutable evidence context.

## 2. Separate channel from content

TOPA distinguishes at least:

```text
DIRECT_OBSERVATION
FIRSTHAND_REPORT
HEARSAY_REPORT
PEER_MESSAGE
GUEST_CLAIM
LISTENER_EMAIL
HOST_STATEMENT
SYMBOLIC_CONTEXT
MODEL_INFERENCE
```

The same sentence can have radically different evidentiary weight depending on channel. A guest saying that a radar operator saw something is not the same object as the radar operator's log. A model repeating a report is not a new witness.

## 3. Observation ladder

```text
O0 = claim/report exists
O1 = firsthand report + time/location
O2 = multiple witnesses; independence unclear
O3 = independent contemporaneous witnesses or external record
O4 = physical/digital/instrument record
O5 = controlled reproducibility
```

The ladder describes evidence strength only. It does not choose the explanation.

## 4. Split event, observation and interpretation

Example:

```text
REPORT: "A red object followed the aircraft."
OBSERVATION: red light reported at relative bearing X during interval Y.
INTERPRETATION A: another aircraft.
INTERPRETATION B: astronomical or atmospheric source.
INTERPRETATION C: sensor/perceptual artifact.
INTERPRETATION D: unknown physical aerial source.
```

TOPA never allows interpretation D to inherit truth merely because A, B or C fail.

## 5. Attack the strongest mundane model

`MUNDANE_FIRST` means ordinary explanations are tested early because they usually have higher prior probability and are often more directly testable.

It does **not** mean ordinary explanations are protected from falsification.

A conventional model that misses the timing, geometry, sensor characteristics or source record must be weakened or rejected exactly like an extraordinary model.

## 6. Force causal independence

TOPA distinguishes:

```text
MULTI_CHANNEL != MULTI_SOURCE
PUBLICATION_COUNT != SOURCE_COUNT
SAME_PAYLOAD_MULTI_AGENT != INDEPENDENT_REPLICATION
```

Three reports can still reduce to one witness. Three sensors can still depend on one upstream emitter, operator interpretation or downstream summary. A later narrative about a radar return is not the same evidence object as the radar-owner record.

When possible, build a causal graph for each evidentiary leg.

## 7. Freeze predictions before outcomes

If a claim predicts a future event, freeze before the deadline:

```text
claim_text
prediction_timestamp
deadline_or_window
success_criterion
failure_criterion
allowed_tolerance
```

After the deadline, score only against the frozen criteria:

```text
PASS
FAIL
PARTIAL_WITH_PREDECLARED_TOLERANCE
UNSCORABLE_TOO_VAGUE
UNRESOLVED_MISSING_OUTCOME_DATA
```

Post-hoc redefinition is prohibited.

## 8. Closed-belief-loop alarm

If no possible observation, source result or test is named that could lower confidence in the favored interpretation, TOPA raises:

```text
CLOSED_BELIEF_LOOP_WARNING
```

This does not prove the claim false. It means the current belief structure is not falsifiable enough for promotion.

## 9. Adversarial classification

The current falsification layer uses these practical classes:

```text
REFUTED
PROBABLE_CONVENTIONAL
UNRESOLVED_NONEXOTIC
DATA_POOR_SURVIVOR
HARD_SURVIVOR
```

`HARD_SURVIVOR` means only that adequate evidence survived several relevant attacks. It is **not** paranormal confirmation. A hard survivor becomes the first target of the next spiral.

## 10. Spiral policy

```text
TURN 0 — attack the extraordinary interpretation
TURN 1 — attack the strongest conventional explanation
TURN 2 — attack the surviving evidence itself:
         provenance, clock, sensor, geometry, independence
TURN 3 — attempt a predictive or archival killer test
ASCEND — update state, preserve receipts, reattack
```

The goal is not to protect a conclusion. The goal is to make each pass more difficult to fool.

## 11. Supersession is a feature

TOPA preserves previous classifications even when later work changes them.

The RB-47 sequence is canonical: one adversarial pass temporarily classified it as a strong survivor; a later kill pass found enough contradictory sensor-owner documentation and terrestrial-radar compatibility to revoke that status. The historical pass remains in the archive so reviewers can see exactly **why confidence moved**.

## 12. Valid terminal states

TOPA explicitly permits:

```text
FALSIFIED
RESOLVED
LIKELY_CONVENTIONAL
SUPPORTED_WITHIN_BOUND
WEAKENED
UNRESOLVED
INSUFFICIENT_DATA
I_DO_NOT_KNOW
```

A mystery does not need to be converted into a story.

## Machine enforcement

The distributed JANUS implementation includes an executable claim-envelope validator at:

```text
integrations/janus-distributed-ai-swarm/topa_epistemic_router.py
```

Its self-test checks rule enforcement such as provenance requirements, hearsay boundaries and frozen-prediction semantics. A validator pass is a software result, **not world-truth evidence**.
