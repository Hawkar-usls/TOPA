# C025 — Akinator RSPC next gate

Status: **SYNCHRONIZED CURRENT FRONT**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why this file changed

The earlier version of this pointer still named `BC1-A` as NEXT after the bounded-cover theorem. Later TOPA artifacts have already advanced beyond that fork.

Historical notes and failed routes remain preserved. This file is only the **current navigation pointer**.

---

## 1. Fixed-C bounded-cover route is already closed in the stated hard-family scope

`C025_AKINATOR_RSPC_BOUNDED_SUPPORT_ER3_ELIMINATION.md` proves an internal simulation theorem

`ResSize(F) <= ER3Size(pi) * 2^O(K_root(pi))`.

Combined with the frozen Resolution lower bound on the selected hard family, every polynomial-size ER3 escape must contain an extension macro with

`K_root = Omega(N^eta)`

and hence minimum NW-neighborhood cover

`Omega(N^eta / log N)`.

Therefore:

`EVERY_UNIVERSAL_FIXED_C_BOUNDED_COVER_ESCAPE = REFUTED_IN_STATED_ER3_HARD_FAMILY_SCOPE`.

The old BC1 attempt to extend Sokolov's published one-neighborhood functional encoding to fixed unions of neighborhoods is no longer needed to close fixed `C`.

The auxiliary note

`C025_AKINATOR_BC1A_C_LOCAL_SUBSTITUTION_AND_RESTRICTION.md`

still records useful facts:

- C-cover stability under source-shaped restriction is proved;
- a generalized C-hyperlocal functional-form restriction lemma is proved internally;
- direct identity with Sokolov's published encoding for `C>1` is refuted;
- the source single-output kill step does not extend verbatim.

These are boundary clarifications, not the active route.

---

## 2. Large-support exact certificate lanes already explored

The forced large-support macro motivated two exact lanes:

### ROBDD

- exact construction/restriction/survival is polynomial in explicit ROBDD bytes;
- large support can still have a small ROBDD, e.g. parity;
- a bad root order can force exponential residual frontier;
- generic good-order discovery has an external NP-hardness/NP-completeness barrier.

### Deterministic live-width path DP

- the serialized B2 gate trace induces a path decomposition without search;
- exact relation/survival DP costs `poly(T)*2^O(lambda)`;
- `lambda=O(log N)` with a universal constant gives polynomial input-relative work;
- a given redundant DAG can force large live width;
- cheap equivalent low-width rewrite discovery remains open.

Both lanes solve restricted **survival**, not global progress.

---

## 3. Global progress moved to exact variable elimination

`C025_AKINATOR_PROOF_CARRYING_ELIMINATION_SELECTOR.md` freezes proof-carrying Davis–Putnam elimination.

Each accepted pure elimination removes one variable exactly, giving a true well-founded progress rank.

But explicit complete resolvent enumeration can blow the state size, so `ELIM-CAP_C` is only conditionally polynomial if a capped pivot always exists.

The extension-assisted successor was `MACRO-RESTORE-CAP`.

---

## 4. Add-only macro restoration is closed

`C025_AKINATOR_MACRO_RESTORE_CAP_ADD_ONLY_BARRIER.md` proves:

If `F+ = F union D` only appends fresh definitional clauses and keeps every old pivot clause, then for every original pivot `x`,

`Q_x(F) subseteq Q_x(F+)`.

Thus an original exact resolvent frontier cannot be reduced by add-only definitions.

A useful extension must change the representation **before** the expensive frontier is materialized.

`ADD_ONLY_EXTENSION_RESTORES_FRONTIER_STUCK_PIVOT = REFUTED`.

---

## 5. Positive one-step operator — prebirth pivot factorization

`C025_AKINATOR_PREBIRTH_PIVOT_FACTORIZATION.md` proves the exact identity

for pivot clauses `(x OR A_i)` and `(NOT x OR B_j)`:

`exists x . F == R AND ((AND_i A_i) OR (AND_j B_j))`.

Equivalently,

`AND_{i,j}(A_i OR B_j) == (AND_i A_i) OR (AND_j B_j)`.

Therefore the explicit `|P_x|*|N_x|` pair frontier is **not intrinsically required for one pivot**. A B2 factor DAG of size linear in explicit pivot literal volume can represent the same existential projection, and the eliminated `x` value has a deterministic witness lift.

Provider finite replay validates the mechanics only; the theorem is analytic.

---

## 6. New obstruction — function becomes relation under projection

`C025_AKINATOR_PF2_FUNCTION_TO_RELATION_BOUNDARY.md` proves that a live B2 extension variable depending on an eliminated root need not remain a Boolean function of the remaining roots.

Example:

`e <-> (x AND y)`.

After `exists x`, at `y=1` both `e=0` and `e=1` are allowed. The projected object is a relation, not the graph of a function.

With two outputs, independent per-macro survival marginals can also lose exact correlation.

Therefore repeated PF1 must carry an exact **joint projected boundary relation**, eliminate the affected extension cone, or construct a new exact quotient/rewrite.

The existing live-width DP lane supplies one exact representation with explicit cost `2^O(lambda)`.

---

## 7. CURRENT RED POINT — BOUNDARY QUOTIENT

The exact current question is:

> For every nonterminal elimination/proof state, can a deterministic polynomial selector construct a proof-carrying exact quotient of the joint projected boundary relation such that total state, construction, verification, witness recovery, and all failed attempts remain bounded by one universal fixed polynomial in original CNF input length `N`?

A valid step must additionally eliminate at least one original root or decrease the frozen global rank.

Admissible representations include:

- live-width DP tables when `lambda=O(log N)`;
- ROBDDs under a deterministically generated certified order;
- exact orbit/symmetry quotient with polynomial discovery and witness lift;
- another canonical relational DAG with explicit polynomial total-cost bound.

Forbidden:

- stale B2 function semantics after eliminating their root dependency;
- independent macro marginals substituted for a joint relation;
- semantic equivalence/SAT/model-counting oracle;
- heuristic compression score as theorem authority;
- exponential search over orders/decompositions/quotients hidden outside the trace;
- small final artifact after exponential temporary work.

---

## 8. Next micro-gates

### BQ1 — exact boundary object

Freeze the serialized joint-relation interface and canonical witness/provenance rules.

### BQ2 — deterministic quotient constructors

Import only exact candidate constructors available across the JANUS organism:

- syntactic hash-consing;
- deterministic live-width decomposition;
- exact certified orbit generators where available;
- ROBDD construction under a frozen deterministic order.

No cross-repository mechanism gains mathematical authority without an explicit reduction.

### BQ3 — adversarial family sweep

For each constructor, search for a family forcing superpolynomial boundary states/bytes or failed discovery.

### BQ4 — universal progress theorem

If one constructor family always produces a polynomial exact quotient and the global elimination rank decreases, combine total costs into a deterministic polynomial SAT decider.

Only then:

`SAT in P => P = NP`.

---

## 9. Current ledger

`FIXED_C_BOUNDED_COVER_ESCAPE = REFUTED_IN_STATED_ER3_HARD_FAMILY_SCOPE`

`LARGE_SUPPORT_EXACT_CERTIFICATES = POSSIBLE_IN_RESTRICTED_REPRESENTATION_LANES`

`ADD_ONLY_MACRO_RESTORE = REFUTED_FOR_FRONTIER_STUCK_STATES`

`ONE_PIVOT_PREBIRTH_FACTORIZATION = PROVED`

`FUNCTION_TO_RELATION_BOUNDARY = PROVED`

`UNIVERSAL_POLY_BOUNDARY_QUOTIENT = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`
