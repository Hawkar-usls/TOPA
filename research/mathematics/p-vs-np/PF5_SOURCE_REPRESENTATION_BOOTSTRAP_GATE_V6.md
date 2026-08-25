# PF5 — Source Representation Bootstrap Gate v6

Status: **FROZEN SOURCE-LEVEL REPRESENTATION DISCOVERY GATE**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why v6 exists

v5 removed family/language labels from representation selection, but still started from an already-built compact exact OBDD. That leaves a major hidden assumption:

> perhaps the expensive step is obtaining the first compact exact representation from the original formula.

v6 removes the free OBDD bootstrap.

The discovery routine receives only:

- a neutral CNF clause list;
- the declared variable list;
- one frozen variable/projection order.

It receives no family name and no representation tag.

The selected representation must be constructed directly from the CNF, carry repeated existential projection, reconstruct witnesses, and charge recognition/construction/proof cost.

---

## 1. Frozen source widths and controls

Widths are frozen before provider execution:

`N = [4,6,8,10,12,14]`.

At each width the external harness creates three source families. Family labels are unavailable inside bootstrap discovery.

### 1.1 Signed blocked-pair SAT canary

Variables:

`X=(x_1,...,x_n)`, `Y=(y_1,...,y_n)`.

Frozen order:

`x_1,...,x_n,y_1,...,y_n`.

For pair `i`, freeze parity

`p_i = i mod 2`.

Constraint:

`x_i XOR y_i = p_i`.

CNF encoding:

If `p_i=0` (`x_i=y_i`):

`(NOT x_i OR y_i) AND (x_i OR NOT y_i)`.

If `p_i=1` (`x_i=NOT y_i`):

`(x_i OR y_i) AND (NOT x_i OR NOT y_i)`.

The formula contains only `2n` binary clauses and has linear source size, but the same blocked variable order is the known OBDD canary: equality-style correlation can require exponentially many OBDD states under the wrong order.

Clause order is deterministically hash-shuffled before discovery so the recognizer cannot depend on pair adjacency.

### 1.2 Signed parity-cycle UNSAT

Use a contradictory signed cycle on roots `1,2,3`:

`v_1 XOR v_2 = 0`

`v_2 XOR v_3 = 0`

`v_1 XOR v_3 = 1`.

For larger declared widths, remaining roots are connected by additional consistent signed edges only to prevent the contradiction from being encoded as a single direct conflicting pair.

The same source recognizer must derive a canonical contradiction from graph consistency, export no witness, and remain exact under projection.

### 1.3 Wide-OR fallback

One source clause

`(v_1 OR ... OR v_n)`.

The signed-parity recognizer must reject because the source is not entirely a paired binary parity CNF. Exact generic OBDD construction is then allowed as the frozen fallback and must pay its full build/projection cost.

---

## 2. Frozen bootstrap portfolio

Order is frozen:

`SIGNED_PARITY_GRAPH_CNF -> GENERIC_FROZEN_ORDER_OBDD`.

No post-result reorder is permitted.

### 2.1 Signed parity graph recognizer

The recognizer scans the neutral CNF and groups binary clauses by unordered variable pair.

For a pair `{u,v}`:

- clause patterns `(-u,+v)` and `(+u,-v)` certify `u XOR v = 0`;
- clause patterns `(+u,+v)` and `(-u,-v)` certify `u XOR v = 1`.

Acceptance requires:

1. every source clause is binary;
2. every clause belongs to exactly one complete two-clause parity encoding;
3. no pair carries both parity values;
4. rebuilding all accepted edge encodings reproduces the canonical source CNF exactly.

The resulting exact representation is a signed component graph compressed to canonical component coordinates:

`value(v) = value(root_component) XOR offset(v)`.

A deterministic graph traversal assigns offsets and detects inconsistent cycles. An inconsistent cycle yields canonical FALSE.

This is a semantic/source-level recognizer over CNF clauses, not a family-name test.

### 2.2 Generic frozen-order OBDD bootstrap

If the parity recognizer rejects, construct the CNF directly in a BDD manager under the supplied frozen order:

- literal node;
- canonical OR within each clause;
- canonical AND across clauses.

The build itself is inside the cost ledger. A BDD cap hit is a failed representation attempt, not an answer about formula hardness.

---

## 3. Exact projection in signed-component representation

For one consistent component, store:

- canonical root = smallest current member;
- each member's parity offset to that root.

For `exists x`:

### Singleton component

Delete it. Reverse witness chooses canonical `x=0`.

### Non-root member

Delete `x`; remaining relation is unchanged. Proof records

`x = root XOR offset(x)`.

### Root member

Choose the smallest remaining member `r'` as new root.

If old offsets are `p(v)`, define

`p'(v)=p(v) XOR p(r')`.

Proof records

`x = r' XOR p(r')`.

Thus projection remains in the same signed-component language without enumerating assignments.

Reversing the projection records reconstructs every eliminated root. The completed witness is checked directly against the original CNF.

Canonical FALSE remains FALSE under all existential projections.

---

## 4. Exact projection in OBDD fallback

Use the already-audited operation

`restrict(x,0), restrict(x,1), APPLY_OR`.

Every intermediate manager state and proof record is charged. SAT witness is reconstructed only from those projection records and checked against the original CNF.

---

## 5. Source-level equivalence certificates

### Signed parity graph

The certificate must contain:

- canonical source CNF hash;
- consumed clause patterns;
- signed edge list;
- deterministic component traversal transcript;
- cycle-consistency checks;
- canonical component state or contradiction;
- a round-trip clause reconstruction hash exactly matching the source CNF.

### OBDD fallback

Construction is syntax preserving: every source literal, clause OR and formula AND is recorded in the build transcript. The final source witness is checked directly against the CNF.

---

## 6. Accounting

All v0.1 caps remain unchanged; no v6-specific tuned cap is added.

Charge at minimum:

- source CNF serialization bytes;
- clause scan/grouping/canonicalization;
- every failed recognizer operation and failure-certificate byte;
- signed graph construction/traversal/cycle checks;
- round-trip source reconstruction;
- selected representation bytes;
- every repeated projection update and intermediate state;
- projection proof bytes;
- witness reversal and direct CNF verification;
- generic OBDD build cost when fallback is selected.

The external fixture family label is forbidden from the discovery function signature.

---

## 7. Required provider verdicts

Per passing control:

- `SOURCE_INPUT_IS_CNF_ONLY = TRUE`
- `BOOTSTRAP_INPUT_HAS_NO_PREBUILT_OBDD = TRUE`
- `BOOTSTRAP_API_UNLABELED = TRUE`
- `FIXED_BOOTSTRAP_ORDER_USED = TRUE`
- `FAILED_BOOTSTRAP_WORK_CHARGED = TRUE`
- `SOURCE_EQUIVALENCE_CERTIFICATE_EXACT = TRUE`
- `SELECTED_REPRESENTATION_PROJECT_CLOSED = TRUE`
- `STRICT_SOURCE_WITNESS = TRUE`

Global:

- `SIGNED_BLOCKED_PAIR_DISCOVERED_BEFORE_OBDD = TRUE` on all SAT canaries;
- `PARITY_CYCLE_CONTRADICTION_DISCOVERED = TRUE`;
- `WIDE_OR_USES_GENERIC_BOOTSTRAP = TRUE`;
- `FIRST_BASE_CAP_HIT`, if any;
- `GENERIC_OBDD_BAD_ORDER_RECEIPT = PRESERVED_FROM_V0`;
- `UNIVERSAL_SOURCE_REPRESENTATION_DISCOVERY = OPEN`;
- `UNIVERSAL_POLYNOMIAL_BOOTSTRAP = OPEN`;
- `UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN`;
- `GLOBAL_PROGRESS_AMORTIZATION = OPEN`;
- `P_VS_NP = OPEN`.

---

## 8. Interpretation

A full finite PASS removes one more hidden assumption: useful structure can sometimes be discovered and made proof-carrying **directly from the compact source formula**, before constructing a bad generic representation.

It does not prove that arbitrary CNF has a compact signed-parity representation, nor that this finite portfolio discovers every useful representation.

The next genuine front after a full v6 PASS is a connected source CNF whose useful boundary structure is not reducible to paired binary parity constraints — in particular a giant 3-CNF component where representation discovery, separator discovery and source-to-boundary conversion must all be charged together.

---

## 9. Laws

- `COMPACT_SOURCE != FREE_COMPACT_REPRESENTATION`
- `REPRESENTATION_BOOTSTRAP_COST_IS_SOLVER_COST`
- `DISCOVER_STRUCTURE_BEFORE_BAD_GENERIC_COMMITMENT_WHEN_CERTIFIABLE`
- `SIGNED_PARITY_COMPONENTS_ARE_PROJECT_CLOSED`
- `SOURCE_ROUNDTRIP_CERTIFICATE_REQUIRED`
- `BAD_OBDD_ORDER != FORMULA_HARDNESS`
- `FINITE_BOOTSTRAP_PORTFOLIO != UNIVERSAL_BOOTSTRAP_THEOREM`
- `P_VS_NP = OPEN`
