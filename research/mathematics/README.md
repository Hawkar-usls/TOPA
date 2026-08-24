# TOPA Mathematical Research

TOPA's mathematical lane applies the same falsification-first discipline used elsewhere in the project to formal theorem/counterexample work.

```text
GENERATE FREELY
→ TYPE THE CLAIM
→ VERIFY THE OBJECT
→ VERIFY THE PARAMETER
→ PROVE OR BREAK
→ REPLAY
→ PROMOTE ONLY THE DERIVATION
```

## Authority split

- **TOPA** — active scout, adversary, gap finder, invariant/counterfamily generator, full process memory.
- **Janus-Fundamentum** — canonical mathematical proof-provider for the current P-vs-NP / proof-complexity line.
- **janus-meta-registry** — long-term lineage/provenance memory.

A TOPA result may originate here and later be mirrored into Fundamentum. Mirroring does not create mathematical authority; the proof/replay gate does.

## Active front: C024 residual-cache bridge

Parent:

- `Hawkar-usls/Janus-Fundamentum` draft PR #210
- Issue #211 — universal polynomial residual count
- Issue #212 — universal polynomial residual size

Current bridge state:

```text
CONDITIONAL_BRIDGE_THEOREM             = PROVED
POLICY0A_CORRECTNESS                   = PROVED
POLYNOMIAL_RECURSION_DEPTH             = PROVED
CALLS_FROM_POLY_STATE_COUNT            = PROVED
LOCAL_BUDGET_IN_CURRENT_STATE_SIZE     = PROVED

ISSUE_211_POLY_RESIDUAL_COUNT           = STRONG_REFUTATION_CANDIDATE
ISSUE_212_POLY_RESIDUAL_SIZE            = OPEN
P_VS_NP                                 = OPEN
```

## #211 attack lineage

### A0 — theorem-object repair

The older compact tournament-style GT proxy was not literally the `GT_n` object used in the Formula-Caching theorem. The line was repaired to the directed source encoding before further theorem transfer.

Artifacts:

- `p-vs-np/source_gt.py`

### A1.1 — incomparability signature

For theorem-matched source `GT_n`, the original totality clause for `{i,j}` survives an augmented exact key iff the pair remains incomparable after exhaustive unit propagation. Thus exact key equality preserves the incomparability graph even with inherited local resolvents.

Artifact:

- `p-vs-np/C024_A1_ANNOTATED_PRUNE_INVARIANT.md`

This is useful but does not recover orientation and therefore does not by itself transfer the full historical `prune` lower bound.

### A1.2 / stronger route — resolution-sink padding

Instead of proving that the local Resolution layer is harmless, construct a polynomial-size padding gadget that forces the deterministic pass to spend its complete attempt budget on tautological resolvents at the smallest-id pivot. Uniform private boosters keep branching inside the GT core.

Candidate consequence after replay:

```text
S(H_n) >= 2^(n-2)
N_n = O(n^4 log n)
⇒ universal S(F) <= N^c is false for current Policy-0A.
```

Artifacts:

- `p-vs-np/C024_ISSUE_211_RESOLUTION_SINK_COUNTERFAMILY.md`
- `p-vs-np/policy0a_padded_gt_counterfamily.py`
- `../../data/TOPA-P-VS-NP-ISSUE-211-RESOLUTION-SINK-COUNTERFAMILY-2026-08-24-v1.0.json`

## Research law after a failed route

If #211 is confirmed refuted, TOPA does not infer `P != NP`. The exact conclusion is only:

```text
THIS POLICY0A CANNOT SATISFY THE FIRST PREMISE OF THE POSITIVE BRIDGE.
```

The counterfamily then becomes a design requirement for the next calculus. In particular, a future local-inference schedule must not be starvable by irrelevant early pivots whose attempted resolvents carry no proof information.

## General reuse

The mathematical mode is intentionally broader than P vs NP. Reusable checks include:

- theorem-object identity;
- encoding equivalence/reduction;
- hidden parameter conversion;
- amortized cost leakage;
- adversarial padding;
- proof-system simulation strength;
- finite-vs-asymptotic claim ceilings;
- exact negative controls;
- independent replay before promotion.

See `../../data/TOPA-MATHEMATICAL-RESEARCH-MODE-2026-08-24-v1.1.json`.
