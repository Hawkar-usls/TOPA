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
→ PRESERVE EVERY FAILURE
```

## Authority split

- **TOPA** — canonical process home: active scout, adversary, gap finder, invariant/counterfamily generator, executable probes and full research memory.
- **Janus-Fundamentum** — mathematical proof-provider for the current P-vs-NP / proof-complexity line.
- **janus-meta-registry** — long-term lineage/provenance memory; historical TOPA artifacts remain preserved there rather than deleted.

Canonical-home policy: `../registry/TOPA-CANONICAL-HOME-MIGRATION-2026-08-24-v1.0.json` from repository root (`registry/...`).

## Current front

```text
C024_CONDITIONAL_BRIDGE_THEOREM          = PROVED
C024_POLICY0A_RESIDUAL_COUNT_#211        = REFUTED_FOR_CURRENT_POLICY0A
C024_STATE_SIZE_#212                     = OPEN

C025_A_FAIR_NONSTARVABLE_SCHEDULER       = PROVED_IN_CURRENT_STATE_SIZE / CI PASS
C025_B_PORTABLE_PROOF_CARRYING_REASON     = PROVED_IN_SCOPE / PROVIDER CI PASS
C025_C_REASON_DISCOVERY_AND_PROOF_SEARCH  = OPEN_ACTIVE
C025_E_TOTAL_REASON_CACHE_AND_DAG_SIZE    = OPEN / COUPLED_TO_#212

P_VS_NP                                   = OPEN
```

Provider work:

- `Hawkar-usls/Janus-Fundamentum` draft PR #214 — C025 Policy-0B
- Issue #212 — universal state/representation size
- Issue #213 — C025 umbrella
- Issue #215 — deterministic reason discovery and proof-search cost

## C024 — how Policy-0A died

Issue #211 was refuted by the polynomial-size family

```text
H_n = GT_n AND BOOST_n AND SINK_n
```

where a smallest-id independent pivot consumes the frozen global local-Resolution attempt budget on tautological pairs while uniform boosters keep branching in the hard theorem-matched directed `GT_n` core.

The final theorem route gives

```text
S(H_n) >= 2^(n-2)
N_n = O(n^4 log n)
```

so the residual count is superpolynomial in actual input length.

This kills **Policy-0A's first bridge premise**, not P-vs-NP.

Canonical receipt:

- `../../data/TOPA-P-VS-NP-ISSUE-211-REFUTATION-FINAL-2026-08-24-v1.0.json`

Supporting artifacts:

- `p-vs-np/source_gt.py`
- `p-vs-np/C024_A1_ANNOTATED_PRUNE_INVARIANT.md`
- `p-vs-np/C024_ISSUE_211_RESOLUTION_SINK_COUNTERFAMILY.md`
- `p-vs-np/C024_ISSUE_211_SECOND_DERIVATION_REVIEW.md`
- `p-vs-np/policy0a_padded_gt_counterfamily.py`

## C025-A — scheduler repair

A complete frozen one-layer scan has

```text
A(K) = sum_x p_x q_x <= L^2/4
```

pair attempts in current representation size `L`, so no irrelevant early pivot can starve later pivots merely by consuming one global cutoff.

The first scheduler CI failure was preserved: the fixture had two adversarial eligible pivots (`d` and `a`), not one. Correcting the accounting — not the lemma — produced a green replay.

Artifacts:

- `p-vs-np/C025_POLICY0B_FAIR_REASON_CALCULUS.md`
- `p-vs-np/policy0b_fair_scheduler_probe.py`
- `../../data/TOPA-C025-FAIR-SCHEDULER-FAILURE-REPAIR-2026-08-24-v1.0.json`

## C025-B — portable context-independent reasons

Returned UNSAT reasons are now frozen as self-contained objects

```text
R = (root_fingerprint, advertised_clause C, final_node, reachable Resolution-DAG pi)
```

with root clauses as the only proof axioms. Decision assumptions are never proof axioms.

The core theorem is:

```text
VERIFY(F0,R)=PASS
AND current context rho falsifies C
=> UNSAT(F0 | rho).
```

Provider CI passed portability and adversarial checks including:

- verification without shared producer `ProofStore`;
- cross-context reuse;
- same-root/different-store node-number independence;
- branch composition;
- reverse unit-conflict lifting;
- wrong-root rejection;
- advertised-clause tamper rejection;
- internal proof tamper rejection;
- unreachable proof-garbage rejection.

TOPA found a post-CI gap in the first version: a `(root_hash, local_node_id)` reference was sound inside one ledger but not genuinely portable. Portable-v1 contains its own reachable proof DAG.

A second cost correction also survives:

```text
ONE_NEW_LOGICAL_RESOLUTION_NODE
!=
CONSTANT_PORTABLE_CERTIFICATE_BYTES
```

Standalone materialization must charge the reachable proof sub-DAG.

Artifacts:

- `p-vs-np/C025_B_CONTEXT_INDEPENDENT_PROOF_CARRYING_REASON.md`
- `p-vs-np/proof_carrying_reason.py`
- `../../data/TOPA-C025-B-PROOF-CARRYING-REASON-2026-08-24-v1.1.json`

## C025-C — current active attack

C025-B makes a supplied reason safe. It does not make reason discovery free.

For partial assignment `rho`, a cached clause reason `C` applies exactly when

```text
C subseteq FALSE(rho).
```

This turns existing-reason lookup into a dynamic subset query.

With per-clause false counters and literal occurrence lists, exact applicability can be maintained in total `O(M)` counter updates along a monotone assignment path, where

```text
M = total literal volume of the explicit reason cache.
```

This is useful but conditional:

```text
FAST_QUERY_IN_M != M_IS_POLYNOMIAL_IN_INPUT_N
```

So the front is now explicitly split:

```text
C025-C1 existing-reason query          = polynomial in explicit cache volume
C025-C2 deterministic new-reason search = OPEN in original input N
C025-E  total cache/proof representation = OPEN in original input N
```

Artifact:

- `p-vs-np/C025_C_REASON_DISCOVERY_AND_PROOF_SEARCH.md`

## Hard laws carried forward

```text
CHEAP_REASON_CHECK != CHEAP_REASON_DISCOVERY
FAST_INDEX != SMALL_CACHE
SMALL_CACHE != FAST_PROOF_SEARCH
SHORT_PROOF_EXISTS != DETERMINISTIC_POLICY_FINDS_IT_IN_POLYTIME
POLY_WORK_IN_TRACE_SIZE != POLY_WORK_IN_ORIGINAL_INPUT_N
DAG_SHARING != POLY_TOTAL_DAG_SIZE_WITHOUT_A_BOUND
FINITE_REPLAY != UNIVERSAL_ASYMPTOTIC_THEOREM
```

## General reuse

TOPA Mathematical Research Mode is broader than P vs NP. Reusable attacks include theorem-object identity, encoding/reduction audits, hidden parameter conversion, cost leakage, adversarial padding, proof-system simulation scope, certificate portability, data-structure complexity, finite-vs-asymptotic gates and independent replay.

Current mode: `../../data/TOPA-MATHEMATICAL-RESEARCH-MODE-2026-08-24-v1.2.json`.
