# C025 — Akinator MACRO-RESTORE-CAP: add-only definitional extension barrier

Status: **INTERNAL EXACT ROUTE-CLOSURE THEOREM**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Question

The proof-carrying elimination selector has a precise stuck condition:

`E_C(F)=empty`,

meaning every current original-variable pivot produces an exact Davis–Putnam elimination state larger than the frozen cap `N^C`.

A tempting repair is:

> add conservative B2 extension definitions, keep all old clauses, then try the same root pivot again.

This note proves that this **add-only** strategy cannot reduce the exact original resolvent frontier of that pivot.

The result does not rule out extension-assisted **replacement/rewrite**. It proves that replacement, quotienting, or another representation-changing operation is mandatory if extensions are to restore capped eliminability.

---

## 1. Frozen elimination convention

For CNF `F` and root pivot `x`, write

- `P_x(F) = {C in F : x in C}`;
- `N_x(F) = {D in F : NOT x in D}`;
- `R_x(F) = F \ (P_x(F) union N_x(F))`.

Let

`Q_x(F)`

be the canonical set of all distinct non-tautological Resolution resolvents

`Res_x(C,D)` for `(C,D) in P_x(F) x N_x(F)`.

The exact elimination state is

`ELIM_x(F) = R_x(F) union Q_x(F)`

with canonical deduplication but **no semantic subsumption deletion or oracle minimization**.

This is the convention frozen in `C025_AKINATOR_PROOF_CARRYING_ELIMINATION_SELECTOR.md`.

---

## 2. Add-only definitional extension

Let `D` be any CNF encoding of fresh extension definitions over fresh extension variables `E`, possibly mentioning original roots including `x`.

Assume only:

1. all variables in `E` are fresh relative to `F`;
2. the transformed state is literally

   `F+ := F union D`;

3. no clause of `F` is removed, shortened, replaced, or renamed before eliminating `x`.

The semantic conservativity/soundness of `D` is irrelevant to the monotonicity theorem below; the theorem is purely syntactic.

---

## 3. Theorem M1 — original pivot resolvents survive add-only extension

For every original pivot `x`,

`Q_x(F) subseteq Q_x(F+)`.

### Proof

Because `F subseteq F+`, every original positive pivot clause remains present:

`P_x(F) subseteq P_x(F+)`.

Likewise

`N_x(F) subseteq N_x(F+)`.

Therefore every original pair

`(C,D) in P_x(F) x N_x(F)`

is still one of the pairs enumerated when eliminating `x` from `F+`.

The resolvent computed from that pair is byte-for-byte the same root clause as before. If it was non-tautological in `F`, adding unrelated clauses cannot make that resolvent syntactically tautological. Canonical deduplication can merge equal copies, but cannot remove the unique canonical representative of an original resolvent.

Hence every clause in `Q_x(F)` remains in `Q_x(F+)`. QED.

---

## 4. Corollary M1.1 — exact resolvent-frontier cardinality cannot decrease

`|Q_x(F+)| >= |Q_x(F)|`.

Thus any cap defined at least partly by exact canonical resolvent count cannot be restored for pivot `x` merely by adding definitions.

In particular, if

`|Q_x(F)| > N^C`,

then

`|Q_x(F+)| > N^C`.

---

## 5. Byte-size statement

For exact serialized **resolvent frontier bytes** (the canonical serialization of `Q_x` alone), every original canonical root resolvent remains a distinct serialized object in `Q_x(F+)`.

Therefore the total bytes occupied by those original frontier members are preserved as a lower bound inside the enlarged frontier, up to fixed container/header conventions.

For total `ELIM_x` bytes, adding definitions may also alter retained clauses and add new resolvents. It cannot erase the original `Q_x(F)` members under the frozen no-subsumption convention.

Hence an `ELIM-CAP_C` failure caused already by the original resolvent frontier cannot be repaired by add-only definitions.

Important precision:

- this theorem does **not** compare semantically minimized CNFs;
- it does **not** claim extension variables never help proof complexity;
- it applies to the exact proof-carrying complete-elimination representation frozen by the Akinator selector.

---

## 6. Stronger stuck-state consequence

Suppose a state `F` is stuck because for every original pivot `x`,

`bytes(Q_x(F)) > N^C`.

Then for every add-only definitional extension state

`F+ = F union D`,

every original pivot remains stuck under the same frontier cap:

`bytes(Q_x(F+)) > N^C`.

Therefore:

`ADD_ONLY_EXTENSION_RESTORES_CAPPED_ORIGINAL_PIVOT = REFUTED`

for this exact stuck condition.

If a state is stuck only because of retained nonpivot clauses rather than `Q_x(F)`, a separate rewrite could change total-state accounting, but add-only extension still does not reduce the original pivot frontier itself.

---

## 7. What a successful macro must now do

An extension-assisted `MACRO-RESTORE-CAP` step must perform at least one representation-changing action **before** the expensive root resolvents are born:

1. replace one or more root clauses by a proof-carrying equisatisfiable/equivalent extended representation;
2. quotient a family of clauses/pairs into a shared symbolic object;
3. change the elimination representation while preserving exact SAT and witness recovery;
4. eliminate a different object whose certified elimination avoids materializing the original frontier.

Merely appending definitions and then running the old complete root-pivot elimination is insufficient.

This matches the independent JANUS architectural law recovered in the historical Tranception P-vs-NP diagnosis:

`DO_NOT_COMPRESS_CHILDREN_AFTER_BIRTH_IF_THEIR_EXACT_ORBIT_CAN_BE_CERTIFIED_AT_THE_PARENT.`

Here the “children” are root-pivot resolvents.

Architecture agreement is not theorem evidence; Theorem M1 above is the mathematical reason in the current selector calculus.

---

## 8. New exact successor — PREBIRTH RESOLVENT QUOTIENT / REPLACEMENT

Define a candidate transformation

`REWRITE_m(F) -> F_m`

with a proof-carrying certificate such that:

1. `SAT(F_m) iff SAT(F)`;
2. every model/witness has a deterministic polynomial lift/project relation as required;
3. bytes of `F_m` plus certificate are `<= N^K` for fixed universal `K`;
4. at least one original root is eliminated in the same atomic certified step, or an immediately following exact capped elimination is guaranteed;
5. the transformation is found by deterministic polynomial enumeration from a frozen candidate language;
6. failed candidate work is also capped in original `N`;
7. no semantic equivalence/SAT oracle is assumed;
8. no backtracking over exponentially many rewrites is hidden.

The key new resource is a **prebirth quotient of the resolvent-pair relation**, not merely a surviving macro.

---

## 9. Candidate quotient object

For pivot `x`, define the bipartite pair relation

`B_x = P_x(F) x N_x(F)`.

Each edge `(C,D)` maps deterministically to either

- `TAUTOLOGY`, or
- canonical root resolvent `Res_x(C,D)`.

The expensive object is therefore a many-to-one map

`q_x : B_x -> Q_x(F) union {TAUTOLOGY}`.

A prebirth quotient certificate should attempt to represent `q_x` without enumerating every edge of `B_x` or every member of an exponentially large `Q_x`.

But a compressed representation is useful only if the next exact elimination/progress operation can consume it directly; otherwise decompression recreates the frontier.

New law:

`SMALL_QUOTIENT_DESCRIPTION + FULL_DECOMPRESSION = NO_COMPLEXITY_GAIN`.

---

## 10. Claim ledger

`ADD_ONLY_DEFINITION_PRESERVES_ORIGINAL_PIVOT_RESOLVENT_SET = PROVED_IN_FROZEN_ELIMINATION_CALCULUS`

`ADD_ONLY_DEFINITION_CAN_REDUCE_EXACT_ORIGINAL_RESOLVENT_FRONTIER = REFUTED`

`ADD_ONLY_EXTENSION_ALONE_SOLVES_MACRO_RESTORE_CAP = REFUTED_FOR_FRONTIER_STUCK_STATES`

`PROOF_CARRYING_REPLACEMENT_OR_PREBIRTH_QUOTIENT = REQUIRED_FOR_THIS_ROUTE`

`UNIVERSAL_PREBIRTH_RESOLVENT_QUOTIENT = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 11. Laws

- `ADDING_NAMES != REMOVING_THE_OLD_FRONTIER`
- `F_SUBSET_F_PLUS_IMPLIES_ORIGINAL_DP_PAIRS_SURVIVE`
- `EXTENSION_POWER_REQUIRES_USING_THE_EXTENSION_IN_THE_REPRESENTATION_NOT_JUST_APPENDING_IT`
- `COMPRESS_BEFORE_RESOLVENT_BIRTH_OR_PAY_THE_FRONTIER`
- `SMALL_QUOTIENT_DESCRIPTION != CHEAP_FULL_DECOMPRESSION`
