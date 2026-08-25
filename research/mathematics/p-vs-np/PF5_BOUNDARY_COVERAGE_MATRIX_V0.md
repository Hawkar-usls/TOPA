# PF5 — Proof-Carrying Boundary Coverage Matrix v0

**Status:** `FROZEN_FINITE_COVERAGE_PROTOCOL__UNIVERSAL_GATE_OPEN`  
**Claim ceiling:** `P_VS_NP = OPEN`

## 1. Question

This experiment does **not** ask which solver wins.

It asks a stricter representation question:

> Which proof-carrying state representation is simultaneously exact, compact on the tested control, and closed under the **next existential projection** without hiding decompression, search, witness recovery, or intermediate bytes?

The target contract for a primary lane is

```text
BUILD(F) -> S_0
PROJECT(S_t, x_t) -> S_{t+1}
...
FINALIZE(S_k) -> TRUE/FALSE
BACK_WITNESS -> assignment to original roots when SAT
```

Every accepted transition must be replayable from explicit certificate/provenance data.

A small representation that cannot perform the next exact `exists x` update directly is **not** counted as closed.

A cheap update whose discovery searched exponentially many candidate representations is **not** counted as cheap.

---

## 2. Typed cost ledger

The matrix keeps bytes and operations separate; it does not manufacture a misleading scalar by adding unlike units.

For every lane/control pair record:

```text
representation_bytes_current
representation_bytes_peak
cumulative_state_bytes
proof_bytes
witness_bytes
build_ops
failed_discovery_ops
root_projection_ops
terminal_finalize_ops
verification_ops
witness_ops
```

The PF5 global accounting law remains

```text
Q_total = Q_state + Q_proof + Q_discovery + Q_witness
```

but this finite matrix exposes the typed components before any aggregate interpretation.

`next_update` cost is mandatory. `cumulative_state_bytes` includes intermediate states, not only the final compact object.

---

## 3. Primary representation lanes

### A. `RAW_B2_SHANNON`

State: canonical hash-consed `AND/NOT` DAG over roots.

Projection rule:

```text
exists x . C = C[x=0] OR C[x=1]
```

with OR represented by De Morgan in the same language. Restriction, simplification and hash-consing are deterministic. A projection record keeps enough pre-state provenance to choose a valid eliminated bit during reverse witness reconstruction.

This lane is exact but receives **no** assumed global polynomial DAG-size theorem.

### B. `FROZEN_ORDER_OBDD`

State: reduced ordered BDD under an explicit control-provided order.

Projection is direct:

```text
exists x . D = OR(RESTRICT(D,x=0), RESTRICT(D,x=1))
```

using deterministic memoized Apply and reduction.

No order search is permitted. The experiment deliberately contains the same equality semantics under interleaved and blocked orders to expose order sensitivity rather than hide it.

### C. `LIVE_WIDTH_FACTOR_DP`

State: exact local Boolean factors obtained from the B2 gate constraints plus the asserted output.

Projection eliminates a variable by joining **only** factors that contain it, existentially deleting that variable, and retaining the resulting exact boundary factor. The witness table records a canonical eliminated bit for every surviving boundary row.

This is a direct proof-carrying boundary-relation lane. Bucket scope and table growth are charged explicitly. After all original roots are projected, the remaining extension variables are also eliminated under a frozen deterministic order so terminal SAT/UNSAT is not hidden behind an unevaluated residual relation.

### D. `TRANCEPTION_ORBIT_TEMPLATE`

State: restricted exact symbolic quotient for families with a frozen recognized generator/template.

v0 admits only two revealed positive-control templates:

- parity-chain relation;
- equality-pair relation.

Projection updates the symbolic template directly and stores an exact reverse witness rule. Unsupported controls fail closed. No semantic-equivalence oracle and no post-hoc generator search are allowed.

This lane operationalizes the already-preserved JANUS lesson:

```text
DO_NOT_COMPRESS_CHILDREN_AFTER_BIRTH_IF_THEIR_EXACT_ORBIT_CAN_BE_CERTIFIED_AT_THE_PARENT
```

without pretending that equality-family coverage is universal coverage.

---

## 4. C2G-LAMINAR is deliberately not a primary representation lane

`C2G_LAMINAR` is included in the matrix because it is part of the JANUS portfolio, but its proven object is a **progress/amortization sidecar**: a laminar ledger of short proof-carrying conflict cubes.

It does not by itself encode an arbitrary projected boundary relation and therefore does not receive a fake `PROJECT` implementation.

Matrix role:

```text
C2G_LAMINAR.role = PROGRESS_SIDECAR
C2G_LAMINAR.primary_boundary_representation = false
C2G_LAMINAR.composition = allowed_if_short_reason_is_supplied
C2G_LAMINAR.universal_short_reason_discovery = OPEN
```

This distinction is intentional. A representation lane may later be paired with C2G to pay for globally repeated progress events, but the two obligations remain separate until a theorem composes them.

---

## 5. Frozen controls

All controls are declared before result inspection.

### `PARITY_CHAIN_12`

Twelve roots, parity-equals-one circuit. Positive control for large support with tiny sequential state.

Projection order: roots `1..12`.

### `EQ_PAIRS_INTERLEAVED_8`

Sixteen roots representing eight equality pairs

```text
(x_i <-> y_i), i=1..8.
```

OBDD order:

```text
x1,y1,x2,y2,...,x8,y8
```

Projection order remains canonical root-ID order `1..16`.

### `EQ_PAIRS_BLOCKED_8`

**Same Boolean function and same projection order** as the previous control.

Only the frozen OBDD order changes to

```text
x1,...,x8,y1,...,y8.
```

This is an order-resource control, not a different semantic problem.

### `FANOUT_PAIR_ARCH_6`

Roots `(x_i,y_i)`, first layer `e_i=x_i AND y_i`, all pair gates `g_ij=e_i AND e_j`, then one AND aggregation tree.

This is a representation-architecture control for boundary/fan-out pressure. No claim is made that its final Boolean function is intrinsically hard.

Projection order: canonical root IDs.

### `RANDOM3SAT_CAL_12`

A revealed finite calibration formula with `n=12`, `m=floor(4.30*n)=51`, three distinct variables per clause, independent deterministic pseudorandom signs, duplicate canonical clauses rejected.

Seed is frozen as the first 64 bits of

```text
SHA256("PF5-MATRIX-RANDOM3SAT-CAL-V0|n=12")
```

No seed skipping or post-hoc regeneration is allowed.

This calibration control is **not** substituted for the separately frozen PF5 red benchmark suite and carries no proof-complexity lower-bound claim.

---

## 6. Frozen finite resource caps

The v0 caps are engineering limits for a reproducible finite comparison, not asymptotic theorems:

```text
RAW_MAX_INTERNED_NODES       = 5000
OBDD_MAX_NONTERMINAL_NODES   = 192
FACTOR_MAX_BUCKET_SCOPE      = 16
MAX_PRIMARY_STATE_BYTES      = 250000
MAX_PROOF_BYTES              = 750000
MAX_CUMULATIVE_STATE_BYTES   = 3000000
MAX_OPERATION_COUNT          = 3000000
```

A cap hit yields `CAP_HIT`, never a guessed semantic answer and never evidence for `P!=NP`.

The OBDD node cap is intentionally modest because this is a finite **coverage** matrix: the object being measured is whether the frozen lane stays compact under a common budget. The raw node, factor-scope and byte caps are frozen at the same time, before the first v0 run.

---

## 7. PASS contract

A primary lane/control cell is `PASS_EXACT_CLOSED` only if all of the following hold under the frozen caps:

1. deterministic representation construction completes;
2. every root existential projection completes in the same representation family;
3. terminal evaluation completes rather than leaving a hard residual object unevaluated;
4. replayed result agrees with an independent finite reference SAT classification;
5. if SAT, reverse witness recovery returns an assignment satisfying the original control;
6. serialized proof/provenance and all typed costs are reported.

`UNSUPPORTED` is a legitimate fail-closed result for a restricted lane.

`CAP_HIT` is a legitimate finite coverage failure.

---

## 8. Portfolio interpretation

For one control, define

```text
PRIMARY_REPRESENTATION_COVERED
```

iff at least one of

```text
RAW_B2_SHANNON
FROZEN_ORDER_OBDD
LIVE_WIDTH_FACTOR_DP
TRANCEPTION_ORBIT_TEMPLATE
```

returns `PASS_EXACT_CLOSED`.

A control with no passing primary lane is a **finite portfolio representation-coverage witness under v0 caps**.

It is not a proof that no polynomial representation exists.

Even if every frozen control is covered, universal coverage is not established.

C2G is reported separately as a possible progress sidecar and is never counted as primary representation coverage.

---

## 9. What success would have to become

The actual theorem target is stronger than this matrix:

> For every polynomial-size CNF of encoded length `N`, a deterministic controller constructs a proof-carrying representation `S`, performs every required existential projection/update directly on `S`, verifies all transitions, recovers witnesses, and pays polynomial total state/proof/discovery/witness cost in one fixed universal polynomial of `N`.

If this process projects all SAT variables and terminates with the correct Boolean value, SAT is in P and therefore `P=NP`.

No finite matrix establishes that theorem.

The matrix exists to expose **where** the portfolio fails before attempting a universal proof.

---

## 10. Frozen laws

- `DO_NOT_SEARCH_FOR_ANOTHER_PRETTY_SOLVER`
- `SEARCH_FOR_PROOF_CARRYING_REPRESENTATION_CLOSED_UNDER_NEXT_EXISTENTIAL_PROJECTION`
- `SMALL_STATE_WITHOUT_CHEAP_PROJECT_IS_NOT_CLOSED`
- `CHEAP_VERIFICATION_WITH_EXPENSIVE_DISCOVERY_IS_NOT_CHEAP_CONSTRUCTION`
- `FINAL_SMALL_STATE_DOES_NOT_ERASE_CUMULATIVE_INTERMEDIATE_BYTES`
- `REPRESENTATION_COVERAGE != GLOBAL_PROGRESS_AMORTIZATION`
- `C2G_LAMINAR_IS_A_PROGRESS_SIDECAR_NOT_A_BOUNDARY_LANGUAGE`
- `FINITE_PORTFOLIO_COVERAGE != UNIVERSAL_POLYNOMIAL_COVERAGE`
- `P_VS_NP = OPEN`
