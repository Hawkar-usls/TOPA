# C025 — Akinator: proof-carrying elimination selector with a uniform polynomial cap

Status: **GLOBAL-PROGRESS SKELETON PROVED / UNIVERSAL CAP AVAILABILITY OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why this gate is different

The previous RSPC lanes solved exact **survival** for restricted representations:

- fixed-cover truth tables;
- ROBDDs;
- deterministic live-width path DP.

But a definitional extension macro is a conservative extension. Introducing it does not change the set of satisfying assignments on the original roots. Therefore survival/nonconstancy of a macro is not itself global SAT progress.

This note freezes the first selector whose accepted step has an exact, well-founded, polynomially bounded **global progress potential**.

The operation is proof-carrying Davis–Putnam variable elimination.

---

## 1. Exact elimination operator

Let `F` be a CNF and `x` one current variable.

Partition clauses into:

- `P_x = {C in F : x in C}`;
- `N_x = {D in F : NOT x in D}`;
- `R_x = F \ (P_x union N_x)`.

For every pair `(C,D) in P_x x N_x`, form the Resolution resolvent

`Res_x(C,D) = (C \ {x}) union (D \ {NOT x})`.

Discard tautological resolvents and deduplicate canonically.

Define

`ELIM_x(F) := R_x union {all distinct non-tautological Res_x(C,D)}`.

The variable `x` no longer occurs.

---

## 2. Theorem F — exact satisfiability preservation

For every assignment `alpha` to variables other than `x`:

`alpha satisfies ELIM_x(F)`

iff

`alpha` has an extension by some value of `x` satisfying `F`.

Equivalently:

`ELIM_x(F) == existentially_quantify_x(F)`

as a Boolean relation on the remaining variables.

### Proof

Forward direction from `F` to every resolvent is ordinary Resolution soundness.

For the converse, suppose `alpha` satisfies `ELIM_x(F)` but neither value of `x` satisfies `F`.

- Failure at `x=0` means some positive clause `(x OR A)` has `A(alpha)=0`, so that clause requires `x=1`.
- Failure at `x=1` means some negative clause `(NOT x OR B)` has `B(alpha)=0`, so that clause requires `x=0`.

Then the resolvent `A OR B` is false under `alpha`. It cannot be tautological when falsified. Therefore it is present in the complete non-tautological resolvent set, contradicting satisfaction of `ELIM_x(F)`.

Hence some value of `x` extends `alpha` to a model of `F`.

Thus elimination is exact and requires no semantic oracle.

---

## 3. Proof-carrying elimination certificate

A certificate for eliminating `x` contains:

- fingerprint of input CNF state;
- pivot variable `x`;
- canonical IDs of `P_x`, `N_x`, and retained `R_x` clauses;
- for every pair in `P_x x N_x`, either:
  - the canonical non-tautological resolvent; or
  - a tautology witness showing a complementary literal pair;
- canonical dedup map;
- fingerprint of exact output CNF.

A verifier recomputes every pair locally and checks exact set equality.

Verification time is polynomial in the explicit input state and explicit pair/certificate bytes.

No SAT solver, model counter, heuristic score, or proof-search oracle is used.

`COMPLETE_RESOLVENT_ENUMERATION_IS_A_LOCAL_PROOF_CERTIFICATE`.

---

## 4. True global progress potential

For pure elimination with no new variables introduced during the run, define

`Phi(F_t) := number of variables remaining in F_t`.

Every accepted elimination step removes its pivot and introduces no variable, so

`Phi(F_{t+1}) = Phi(F_t) - 1`.

Since `Phi(F_0) <= N` for any reasonable explicit encoding, the number of accepted steps is at most `N`.

This is a genuine globally well-founded polynomially bounded progress measure.

No semantic notion such as “confidence,” “survival score,” or “likely usefulness” appears.

---

## 5. The hidden exponent: state-size degree drift

Let `M_t` be the number of explicitly stored distinct clauses at step `t`.

For a pivot `x`, at most

`|P_x| * |N_x| <= M_t^2`

raw pair resolvents are generated, so a naive bound is

`M_{t+1} <= M_t + M_t^2 <= 2*M_t^2`.

Ignoring constants, repeated application allows

`M_t <= N^(2^t)`

under the crude worst-case recurrence.

Therefore the statement

> every elimination step is polynomial in the current state

is **not** a polynomial-time theorem in the original input length.

The polynomial degree itself can grow with the number of steps.

New law:

`POLY_IN_CURRENT_STATE_AT_EACH_STEP != UNIFORM_POLY_IN_ORIGINAL_INPUT`.

This is an exact instance of the hidden-exponent firewall.

---

## 6. Uniform cap selector ELIM-CAP_C

Freeze one universal constant `C` before seeing the input.

Let the original encoded CNF length be `N` and define a byte/record cap

`CAP(N) := N^C`.

At each state:

1. enumerate current variables in canonical ID order;
2. for each candidate pivot `x`, stream the exact complete elimination result;
3. deduplicate canonically;
4. abort this candidate as soon as its exact serialized output would exceed `CAP(N)`;
5. accept the first pivot whose complete exact output fits the cap;
6. replace the current CNF by that output.

Because the current state is itself capped, all pivot candidates and clause pairs are polynomially enumerable in original `N`.

The failed candidate computation is also capped; no candidate may materialize super-cap bytes and then claim the work was free.

No backtracking is allowed: once the first admissible pivot is accepted, the selector does not later undo it.

---

## 7. Conditional polynomial-Akinator theorem

Fix universal constant `C`.

Assume that for every input CNF `F` of encoded length `N`, every nonterminal state reached by deterministic `ELIM-CAP_C` has at least one pivot whose exact output fits `N^C`.

Then:

- at most `N` accepted pivots occur;
- at each state at most `N` variables are scanned, or more generally at most the capped explicit-variable count;
- each candidate enumerates at most `N^(2C)` clause pairs before cap/acceptance, up to fixed encoding factors;
- every certificate is locally verifiable;
- state bytes never exceed `N^C`;
- no semantic oracle/backtracking is used;
- after all variables are eliminated, the remaining CNF is either empty/satisfied or contains the empty clause, deciding SAT.

Therefore `ELIM-CAP_C` decides CNF-SAT in deterministic polynomial time.

Hence the universal availability assumption implies

`P = NP`.

This is a **conditional bridge theorem**, not a proof that such a universal `C` or pivot always exists.

Current status:

`UNIVERSAL_ELIM_CAP_C_AVAILABILITY = OPEN`.

`P_VS_NP = OPEN`.

---

## 8. Exact structural sufficient condition: elimination boundary width

At state `F_t` and pivot `x`, define the pivot boundary

`B_t(x) := union of variables appearing with x or NOT x in pivot clauses, excluding x`.

Let

`w_t(x) := |B_t(x)|`.

Every generated resolvent is a non-tautological clause over `B_t(x)`.

A clause over `w` Boolean variables has at most three choices per variable:

- absent;
- positive;
- negative.

Thus the number of distinct non-tautological resolvents is at most

`3^w`.

For an elimination order with dynamic maximum boundary width `w`, the total number of distinct clauses ever generated is bounded by

`N + n*3^w`

up to canonical retention/encoding factors, and total elimination work is

`poly(N,n) * 3^O(w)`.

Therefore a universal bound

`w = O(log N)`

with a fixed hidden constant is sufficient for deterministic polynomial elimination.

Important ceiling:

High boundary width does **not** imply `3^w` resolvents are actually generated. The exact resource is the distinct resolvent frontier/state bytes; boundary width is a safe structural upper bound, not an exact lower bound.

---

## 9. Exact next resource: minimum capped elimination frontier

For a current explicit state `F`, define

`E_C(F) := {x : bytes(ELIM_x(F)) <= N^C}`.

The selector succeeds locally iff `E_C(F)` is nonempty.

Define the exact minimum next-state size

`mu(F) := min_x bytes(ELIM_x(F))`.

`mu(F)` is computable from an already capped explicit state by polynomially scanning all pivots and streaming each exact elimination result with an appropriate comparison cap.

The global open question becomes:

> Does there exist a fixed universal `C` such that along the deterministic no-backtracking first-fit run, `mu(F_t) <= N^C` at every nonterminal state for every CNF input?

This is now a concrete, falsifiable selector claim.

---

## 10. Why macro extensions re-enter exactly here

If pure elimination reaches a state where

`E_C(F_t) = empty`,

then the next structural macro layer has a precise task:

> introduce a proof-carrying conservative extension/rewrite which restores at least one capped elimination pivot **without violating a global polynomial extension/state budget**.

This is much narrower than “invent a useful macro.”

A macro candidate must now certify:

1. conservative extension/equisatisfiable rewrite;
2. total state remains under a fixed polynomial cap;
3. after the rewrite, some pivot has exact capped elimination output;
4. the macro/rewrite itself is deterministically discoverable from a polynomial candidate language;
5. no semantic oracle;
6. no backtracking.

This is the next true `PROOF-CARRYING STRUCTURAL SELECTOR` gate.

---

## 11. Extension-assisted progress potential

If structural steps may introduce extensions, fix a universal extension budget

`K_max(N) <= N^k`

for fixed `k`.

Let

- `r` = remaining original root variables;
- `v` = total currently live variables, bounded by `n + K_max`.

Set

`B := n + K_max + 1`

and define lexicographic rank encoded as

`Phi_ext := r*B + v`.

A macro-assisted accepted step is required to:

- introduce any allowed extensions within the remaining budget;
- eliminate at least one original root variable in the same atomic certified step.

Since `v < B`, decreasing `r` by one decreases `Phi_ext` even if the step introduces extensions up to the global budget.

After all roots are eliminated, extension variables are eliminated without introducing new ones, decreasing `v`.

Thus `Phi_ext` is polynomially bounded when `K_max` is polynomial with a universal fixed exponent.

This provides a rigorous progress rank for future macro-assisted elimination.

It does not prove capped macro availability.

---

## 12. Next gate — MACRO-RESTORE-CAP

Freeze a polynomially enumerable macro schema language `L_C`.

At a stuck state `E_C(F)=empty`, require the selector to find in deterministic polynomial time a candidate `m in L_C` with a proof-carrying certificate such that the atomic transformed state:

- preserves SAT;
- stays within state/extension cap;
- eliminates at least one original root;
- ends with state bytes `<=N^C`;
- decreases `Phi_ext`.

If such a candidate exists at every stuck state, the full macro-assisted selector is a deterministic polynomial SAT algorithm.

If not, the first stuck state gives the exact next obstruction:

- minimum elimination frontier size;
- required extension count;
- rewrite search width;
- live/residual boundary width;
- or certificate bytes.

---

## 13. Claim ledger

`DAVIS_PUTNAM_ELIMINATION_SAT_PRESERVATION = PROVED_IN_SCOPE`

`COMPLETE_ELIMINATION_CERTIFICATE_VERIFICATION = POLYNOMIAL_IN_EXPLICIT_PAIR_BYTES`

`PURE_ELIMINATION_VARIABLE_COUNT_PROGRESS = EXACT_DECREASE_BY_ONE`

`PER_STEP_POLY_IN_STATE_DOES_NOT_GIVE_UNIFORM_POLY_IN_N = PROVED_BY_EXPONENT_DRIFT_RECURRENCE`

`ELIM_CAP_C_PLUS_UNIVERSAL_AVAILABILITY_IMPLIES_P_EQ_NP = CONDITIONAL_THEOREM`

`UNIVERSAL_ELIM_CAP_C_AVAILABILITY = OPEN`

`BOUNDARY_WIDTH_O_LOG_N_IS_A_SUFFICIENT_POLY_ELIMINATION_REGIME = PROVED_IN_SCOPE`

`HIGH_BOUNDARY_WIDTH_IMPLIES_EXPONENTIAL_ACTUAL_FRONTIER = NOT_PROVED`

`MACRO_RESTORE_CAP_UNIVERSAL_AVAILABILITY = OPEN`

`P_VS_NP = OPEN`

---

## 14. Laws

- `CONSERVATIVE_EXTENSION_SURVIVAL != GLOBAL_PROGRESS`
- `VARIABLE_ELIMINATION_GIVES_AN_EXACT_WELL_FOUNDED_PROGRESS_STEP`
- `POLY_IN_CURRENT_STATE_AT_EACH_STEP != UNIFORM_POLY_IN_ORIGINAL_INPUT`
- `UNIVERSAL_FIXED_CAP != INPUT_DEPENDENT_POLYNOMIAL_DEGREE`
- `BOUNDARY_WIDTH_IS_AN_UPPER_BOUND_RESOURCE_NOT_AN_AUTOMATIC_LOWER_BOUND`
- `A_USEFUL_MACRO_MUST_RESTORE_CAPPED_ELIMINABILITY_NOT_MERELY_SURVIVE`
