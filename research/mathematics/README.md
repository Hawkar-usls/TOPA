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

## Current front

```text
C024_CONDITIONAL_BRIDGE_THEOREM              = PROVED
C024_POLICY0A_RESIDUAL_COUNT_#211            = REFUTED_FOR_CURRENT_POLICY0A
C024_STATE_SIZE_#212                         = OPEN

C025_A_FAIR_NONSTARVABLE_SCHEDULER           = PROVED_IN_CURRENT_STATE_SIZE / CI PASS
C025_B_PLAIN_RESOLUTION_REASON                = PROVED_IN_SCOPE / PROVIDER PASS
C025_C1_EXISTING_REASON_QUERY                 = PROVED_IN_EXPLICIT_CACHE_VOLUME M
C025_E1_PLAIN_RESOLUTION_CERTIFICATE_SIZE     = REFUTED_AS_UNIVERSAL_POLY_LANGUAGE
C025_B2_EXTENSION_AWARE_REASON_V0             = PROVED_IN_SCOPE / STRENGTHENED PROVIDER PASS
C025_E2_UNIVERSAL_EXTENSION_AWARE_PROOF_SIZE  = OPEN_ACTIVE
C025_C2_EXTENSION_DEFINITION_DISCOVERY        = OPEN_ACTIVE
C025_C2_GLOBAL_DETERMINISTIC_PROOF_SEARCH     = OPEN_ACTIVE
C025_E_TOTAL_ACTIVE_REPRESENTATION             = OPEN / COUPLED_TO_#212

P_VS_NP                                       = OPEN
```

Provider work:

- `Hawkar-usls/Janus-Fundamentum` draft PR #214 — C025 Policy-0B
- Issue #212 — universal state/representation size
- Issue #213 — C025 umbrella
- Issue #215 — deterministic reason discovery and proof-search cost
- Issue #216 — stronger standalone-verifiable reason language / E2 proof-size front

## C024 — how Policy-0A died

Issue #211 was refuted by the polynomial-size family

```text
H_n = GT_n AND BOOST_n AND SINK_n
```

where a smallest-id independent pivot consumes the frozen global local-Resolution attempt budget on tautological pairs while uniform boosters keep branching in the theorem-matched directed `GT_n` core.

The result kills **Policy-0A's first bridge premise**, not P-vs-NP.

Canonical receipt:

- `../../data/TOPA-P-VS-NP-ISSUE-211-REFUTATION-FINAL-2026-08-24-v1.0.json`

## C025-A — scheduler repair

A complete frozen one-layer scan has

```text
A(K) = sum_x p_x q_x <= L^2/4
```

pair attempts in current representation size `L`, so no irrelevant early pivot can starve later pivots merely by consuming one global cutoff.

This repairs starvation only; it does not prove polynomial state size or polynomial SAT.

## C025-B — portable plain-Resolution reasons

Returned UNSAT reasons are self-contained objects

```text
R = (root_fingerprint, advertised_clause C, final_node, reachable Resolution-DAG pi)
```

with root clauses as the only proof axioms.

```text
VERIFY(F0,R)=PASS
AND rho falsifies C
=> UNSAT(F0 | rho).
```

Provider replay established portability, cross-context reuse, branch composition, reverse unit-conflict lifting, root binding and tamper rejection.

TOPA also caught a post-CI locality bug in the first version: `(root_hash, local_node_id)` was not genuinely portable. Portable-v1 carries its own reachable proof DAG.

## C025-C1 — existing certified-reason query

For partial assignment `rho`, a cached clause reason `C` applies exactly when

```text
C subseteq FALSE(rho).
```

Per-clause false counters plus literal occurrence lists maintain exact applicability in total work polynomial in explicit cache literal volume `M` along a monotone path, with exact rollback.

```text
FAST_QUERY_IN_M != M_IS_POLYNOMIAL_IN_INPUT_N
```

So query mechanics are no longer the main unknown; cache size and new-proof discovery are.

## C025-E1 — plain Resolution certificate-size barrier

At the empty root context, any applicable clause reason must be the empty clause. A root-level C025-B certificate is therefore a Resolution refutation.

Known Resolution proof-size lower bounds on explicit polynomial-size CNF families imply that the plain-Resolution reason language cannot have a universal polynomial-size root certificate for all CNFs.

Therefore:

```text
PLAIN_RESOLUTION_REASON_SOUNDNESS = PROVED
UNIVERSAL_POLY_PLAIN_RESOLUTION_CERT_SIZE = REFUTED
```

This does not imply `P != NP`; it only kills that certificate language as a universal polynomial proof-carrying layer.

## C025-B2 — extension-aware portable reason v0

The successor language admits fresh extension definitions

```text
e <-> (a AND b)
```

with exact definitional CNF

```text
(~e OR a)
(~e OR b)
(e OR ~a OR ~b)
```

under strict freshness/topological rules.

Internal proof clauses may use extension variables, but the advertised reusable clause must contain original/root variables only.

The conservative-extension theorem gives

```text
VERIFY_EXT(F0,R)=PASS
AND advertised C uses root variables only
=> F0 |= C
```

and therefore any root-variable context falsifying `C` is UNSAT.

TOPA found a second post-PASS accounting hole: unreachable proof nodes were rejected, but unused extension definitions could still be serialized. The strengthened verifier now requires the exact transitive definition closure of the reachable proof, and the exporter prunes unused definitions.

Authoritative provider replay after that repair:

```text
run = 32720170819
job = 97409694435
head = 736f4b7e532ee285bcb6f05b48e47c483a2c0613
conclusion = SUCCESS
```

Positive replay includes verifier soundness, original-clause reuse, an extension-participating derivation, definition closure and unused-definition pruning.

Negative replay rejects:

- root collisions;
- duplicate/nonfresh and descending extension ids;
- forward and cyclic dependency attempts;
- extension-variable leakage;
- extension-axiom clause/slot tampering;
- Resolution tampering;
- advertised-clause tampering;
- wrong root binding;
- unreachable proof-node garbage;
- unused extension-definition garbage.

Canonical receipt:

- `../../data/TOPA-C025-B2-EXTENSION-AWARE-REASON-PROVIDER-PASS-2026-08-24-v1.0.json`

## New active front — E2 × C2

B2 closes the **soundness/interface** layer for the frozen extension-aware language. It does not close the complexity layer.

The remaining questions are now deliberately split:

```text
C025-E2:
  Is total extension-aware certificate / active representation universally poly(N)?

C025-C2:
  Can a deterministic policy discover useful extension definitions and proofs
  in poly(N) total work on every CNF?
```

Neither follows from verifier soundness or from the existence of a short proof on one family.

## Hard laws carried forward

```text
SOUNDNESS != CERTIFICATE_SIZE
CERTIFICATE_SIZE != CACHE_SIZE
CACHE_SIZE != PROOF_DISCOVERY
PROOF_DISCOVERY != TOTAL_RUNTIME
CHEAP_REASON_CHECK != CHEAP_REASON_DISCOVERY
FAST_INDEX != SMALL_CACHE
SHORT_PROOF_EXISTS != DETERMINISTIC_POLICY_FINDS_IT_IN_POLYTIME
POLY_WORK_IN_TRACE_OR_CERT_SIZE != POLY_WORK_IN_ORIGINAL_INPUT_N
DAG_SHARING != POLY_TOTAL_DAG_SIZE_WITHOUT_A_BOUND
FINITE_REPLAY != UNIVERSAL_ASYMPTOTIC_THEOREM
```

TOPA Mathematical Research Mode remains broader than P vs NP: theorem-object identity, encoding/reduction audits, hidden parameter conversion, cost leakage, adversarial padding, proof-system simulation scope, certificate portability, data-structure complexity, finite-vs-asymptotic gates and independent replay are reusable elsewhere.
