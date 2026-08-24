# TOPA Method — Strict Science Edition

> **ANOMALY IS A QUESTION, NOT A CONCLUSION.**

TOPA preserves unusual reports without granting their labels evidentiary authority. The active method is now governed by `protocols/TOPA_STRICT_SCIENCE_GATE_V1_0.json`.

Historical heuristic labels remain in Git history and archived receipts for provenance, but they are **not valid upstream evidence for new active claims**.

## 1. Preserve before interpreting

For every case preserve the raw report and provenance before normalization.

Minimum active fields:

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
evidence_objects
evidence_class
status
```

Optional probability/confidence fields are allowed only when accompanied by a defined, reproducible statistical or probabilistic model and its calibration/validation method.

A model may normalize a claim, but the raw ledger remains immutable.

## 2. Scientific authority classes

Every active evidentiary object must be one of:

```text
SOURCE_FACT
FORMAL_DERIVATION
REPRODUCIBLE_EXPERIMENT
STATISTICAL_INFERENCE
HYPOTHESIS_ONLY
```

`HYPOTHESIS_ONLY` has zero evidentiary authority. It exists only to generate falsifiable tests.

Uncalibrated scores, rankings, model votes, narrative coherence, visual impressiveness and survivor labels are not evidence classes.

## 3. Separate channel from content

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

A report being well sourced proves that the report occurred; it does not prove the report's interpretation. A model repeating a source is not a new witness.

The former ordinal observation ladder `O0..O5` is deprecated as an active scientific weight. Historical records may retain it, but no numerical or ordinal evidentiary inference may be derived from it without a separately validated measurement model.

## 4. Split report, measurement and interpretation

Example:

```text
REPORT: "A red object followed the aircraft."
SOURCE-BOUND OBSERVATION: source S reports a red light at bearing X during interval Y.
MEASUREMENT: instrument record R contains values Z with stated calibration/uncertainty.
HYPOTHESIS A: another aircraft.
HYPOTHESIS B: astronomical/atmospheric source.
HYPOTHESIS C: sensor/perceptual artifact.
HYPOTHESIS D: unknown physical aerial source.
```

Failure of A, B or C does not establish D. Exhausting a list of hypotheses is not proof that an unlisted explanation is impossible.

## 5. Test tractable conventional explanations early — without heuristic priors

TOPA may test ordinary mechanisms early when they are directly measurable, source-checkable or inexpensive to falsify.

The method no longer uses an undefined statement such as "usually higher prior probability" as scientific evidence. A prior probability may be used only inside an explicit probabilistic model with a defined reference class and calibration/validation assumptions.

Every conventional and extraordinary hypothesis remains equally vulnerable to falsification at the level of its actual predictions.

## 6. Force causal independence

```text
MULTI_CHANNEL != MULTI_SOURCE
PUBLICATION_COUNT != SOURCE_COUNT
SAME_PAYLOAD_MULTI_AGENT != INDEPENDENT_REPLICATION
```

When independence matters, construct an explicit provenance/causal dependency graph. Independence is a property to establish, not a score to assign by impression.

## 7. Freeze predictions before outcomes

When a claim predicts a future testable outcome, freeze:

```text
claim_text
prediction_timestamp
deadline_or_window
success_criterion
failure_criterion
allowed_tolerance
analysis_rule
```

After the deadline use only the frozen rule:

```text
PASS
FAIL
PARTIAL_WITH_PREDECLARED_TOLERANCE
UNSCORABLE_TOO_VAGUE
UNRESOLVED_MISSING_OUTCOME_DATA
```

Post-hoc redefinition is prohibited.

## 8. Closed-belief-loop gate

If no possible observation, source result or test is named that could disconfirm a hypothesis, raise:

```text
CLOSED_BELIEF_LOOP_WARNING
```

Effect: the object remains `HYPOTHESIS_ONLY` or `UNRESOLVED`. No uncalibrated "confidence lowering" operation is required or permitted as a substitute for falsifiability.

## 9. Active scientific statuses

The active status vocabulary is:

```text
SOURCE_BOUND_FACT
PROVED_IN_SCOPE
REFUTED
CONDITIONAL
REPRODUCED_FINITE_MECHANICS
SUPPORTED_BY_STATISTICAL_INFERENCE_WITH_MODEL
HYPOTHESIS_ONLY
UNRESOLVED
INSUFFICIENT_DATA
```

Historical statuses such as

```text
PROBABLE_CONVENTIONAL
UNRESOLVED_NONEXOTIC
DATA_POOR_SURVIVOR
HARD_SURVIVOR
LIKELY_CONVENTIONAL
```

are deprecated for new active scientific claims. They may remain only as provenance describing what an earlier pass said.

## 10. Spiral policy without heuristic promotion

```text
TURN 0 — freeze the exact claim and admissible evidence classes
TURN 1 — verify provenance/object identity/measurement semantics
TURN 2 — construct competing falsifiable hypotheses
TURN 3 — run the strongest reproducible source, experiment or derivation attack available
TURN 4 — audit alternative explanations and negative controls
TURN 5 — audit representation, selection, multiplicity and hidden-cost assumptions
ASCEND — preserve receipts, classify by strict status, reattack
```

No turn may promote a claim because it "looks strongest". Selection of the next test may be pragmatic, but test selection itself is not evidence.

## 11. Supersession and negative results

TOPA preserves all earlier states. A later source, derivation or experiment may supersede a previous status, but the earlier receipt remains visible with its exact failure mode.

Failed preregistered runs remain failed. Negative results are not deleted. A later successful run does not rewrite the earlier run.

## 12. Mathematics-specific firewall

A mathematical promotion requires one of:

```text
CHECKABLE_DERIVATION
CHECKABLE_COUNTEREXAMPLE_OR_COUNTERFAMILY
PROVED_REDUCTION_OR_SIMULATION
CONDITIONAL_THEOREM_WITH_ALL_OPEN_PREMISES_NAMED
```

Executable CI can validate finite mechanics and implementation parity. It cannot by itself establish a universal asymptotic theorem.

Every polynomial-time statement must identify original encoded input length `N`. If a result is only polynomial in current state/cache/proof size `L`, `M`, `K`, `S` or `|pi|`, the missing bound to `N` stays explicit.

A statement `S^f(N)` is not called polynomial unless `f(N)` is bounded by a universal fixed constant.

See:

```text
research/mathematics/p-vs-np/C025_HIDDEN_EXPONENT_AUDIT_2026-08-24.md
```

## 13. Statistical claims

A statistical claim must state, as applicable:

```text
population/sample
sampling or acquisition process
estimand/test target
model and assumptions
effect size
uncertainty interval or exact test quantity
multiple-testing/selection handling
calibration/validation procedure
```

A bare probability, confidence percentage or model score is not a scientific result.

## 14. Valid terminal states

```text
REFUTED
PROVED_IN_SCOPE
CONDITIONAL
SOURCE_BOUND_FACT
REPRODUCED_FINITE_MECHANICS
SUPPORTED_BY_STATISTICAL_INFERENCE_WITH_MODEL
HYPOTHESIS_ONLY
UNRESOLVED
INSUFFICIENT_DATA
I_DO_NOT_KNOW
```

A mystery does not need to become a story, and a useful hypothesis does not need to become evidence.

## Machine enforcement

The distributed JANUS implementation includes an executable claim-envelope validator at:

```text
integrations/janus-distributed-ai-swarm/topa_epistemic_router.py
```

That validator now requires a follow-on update to enforce the Strict Science Gate vocabulary and reject uncalibrated heuristic authority. Until that update is provider-replayed, the **documented gate is canonical policy but runtime enforcement is not yet claimed complete**.
