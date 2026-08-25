# C025 — Akinator PF5-R1: exact intact-gate congruence reuse

Status: **EXACT LOCAL REWRITE THEOREM / UNIVERSAL COMPRESSION POWER OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

Repeated PF1 factorization creates fresh B2 extension variables. Before introducing stronger semantic quotient machinery, PF5 should remove only redundancy that is already certified by intact B2 definitions.

PF2 forbids reusing stale functional provenance after existential projection. Therefore this lane is deliberately narrow:

> merge only extension variables whose complete current B2 definition triples are simultaneously present and have the same signed inputs.

No semantic-equivalence oracle is used.

---

## 1. Frozen B2 definition

For signed literals `a,b` and fresh extension variable `e`, the intact definition

`e <-> (a AND b)`

is encoded by the three clauses

`(NOT e OR a)`,
`(NOT e OR b)`,
`(e OR NOT a OR NOT b)`.

The input pair is canonically ordered because AND is commutative.

Call the canonical structural key

`K(e) := (AND, min_signed(a,b), max_signed(a,b))`.

A definition is **intact** only when all three canonical clauses occur in the current exact CNF and the original extension-output/input side conditions are met.

---

## 2. Theorem R1 — duplicate intact definitions force equal outputs

Assume the current CNF contains intact definitions

`Def(e;a,b)` and `Def(f;a,b)`

for distinct extension variables `e!=f` and the same signed inputs.

Then every satisfying assignment of the current CNF obeys

`e=f`.

### Proof

Each intact definition is logically equivalent to equality with the same Boolean expression:

`e = (a AND b)` and `f = (a AND b)`.

Therefore `e=f` in every satisfying assignment. QED.

This uses only the frozen B2 definition semantics.

---

## 3. Theorem R2 — exact congruence substitution

Let `F` contain both intact definitions above. Choose the canonical representative

`r := min(e,f)`

and duplicate `d := max(e,f)`.

Construct `F'` by:

1. replacing every literal `d` by `r` and every literal `NOT d` by `NOT r` in all clauses outside `Def(d;a,b)`;
2. deleting the three clauses of `Def(d;a,b)`;
3. canonicalizing the resulting CNF.

Then

`SAT(F') iff SAT(F)`.

Moreover witness maps are deterministic:

- projection `F -> F'`: drop `d` after replacing references with `r`;
- lift `F' -> F`: set `d:=r`.

### Proof

By R1 every model of `F` already has `d=r`, so substitution preserves every nondeleted clause and projection gives a model of `F'`.

Conversely, in a model of `F'`, set `d=r`. The representative's intact definition ensures `r=a AND b`, hence `d=a AND b`, so the deleted duplicate definition is satisfied. Reversing the substitution satisfies every original clause. QED.

---

## 4. Discovery cost

For each intact definition, compute its explicit canonical key `K` and insert it into a deterministic map from key to representative extension ID.

Key comparison is syntactic signed-integer comparison. No hash collision has logical authority; a machine hash may accelerate lookup only if equality is confirmed by the explicit key.

With a balanced ordered map over `g` intact definitions, discovery is polynomial in `g` and identifier bit length. In a hash-table implementation, expected time is engineering-only; the mathematical contract remains explicit-key equality.

All global substitutions and canonicalization work are charged.

Therefore:

`INTACT_DUPLICATE_GATE_DISCOVERY_AND_VERIFICATION = POLYNOMIAL_IN_EXPLICIT_CURRENT_STATE_SIZE`.

This is not yet a polynomial bound in original input `N` if the current state itself is superpolynomial.

---

## 5. Fixpoint congruence closure

Merging one output can make two downstream intact definitions acquire the same structural key. Hence repeat the deterministic pass until no duplicate intact definition remains.

Each successful merge strictly decreases the number of extension variables, so at most `g-1` successful merges occur. Re-scanning naively still gives a polynomial algorithm in explicit current-state size; an indexed incremental implementation is optional.

The resulting fixpoint is exact under the local theorem above.

---

## 6. Critical PF2 firewall

A former B2 gate is **not** eligible merely because the project remembers that it was once defined as `e=a AND b`.

If existential elimination has removed a parent/root and one or more definition clauses were projected away or transformed, the current state may encode only a relation involving `e`. PF2 gave the explicit example

`e <-> (x AND y)`

where after eliminating `x` there is no function `e=h(y)` representing the projection.

Therefore:

`HISTORICAL_GATE_PROVENANCE != CURRENT_INTACT_FUNCTIONAL_DEFINITION`.

Only current-clause verification authorizes structural congruence reuse.

---

## 7. What this lane can and cannot prove

If repeated PF1 created many byte-identical functional subcomputations with fresh output IDs, R1/R2 can remove that redundancy exactly and cheaply relative to the current explicit state.

If the remaining residue consists of genuinely different intact gates or nonfunctional projected correlations, R1 does nothing. That negative result would localize the cost further toward the joint boundary relation rather than repeated syntax.

Thus:

`STRUCTURAL_DUPLICATE_GATE_REUSE = SAFE_CHEAP_FIRST_REPAIR`

but

`STRUCTURAL_DUPLICATE_GATE_REUSE = UNIVERSAL_POLYNOMIAL_BOUND`

is not claimed.

---

## 8. Next finite gate

On the frozen GT12 PF1 residue, measure before/after:

- exact intact-definition count;
- number of duplicate structural keys;
- successful congruence merges;
- substitution/canonicalization work;
- final state units;
- whether the unchanged 20,000-unit handoff cap is crossed.

Run certified subsumption first. Apply intact-gate congruence only if the normalized residue still exceeds the handoff cap.

This ordering prevents adding a stronger operator when an already-frozen cheaper exact operator suffices.

---

## 9. Claim ledger

`DUPLICATE_INTACT_B2_DEFINITIONS_FORCE_EQUAL_OUTPUTS = PROVED`

`INTACT_GATE_CONGRUENCE_SUBSTITUTION_PRESERVES_SAT = PROVED`

`INTACT_GATE_CONGRUENCE_DISCOVERY_POLY_IN_CURRENT_EXPLICIT_STATE = PROVED`

`STALE_PROJECTED_GATE_PROVENANCE_AUTHORIZES_REUSE = REFUTED_BY_PF2`

`GT12_RESIDUE_REDUCTION_BY_INTACT_GATE_CONGRUENCE = NOT_YET_MEASURED`

`UNIVERSAL_POLY_BOUND_AFTER_CONGRUENCE = OPEN`

`P_VS_NP = OPEN`

---

## 10. Laws

- `MERGE_ONLY_INTACT_FUNCTIONAL_DEFINITIONS`
- `SAME_STRUCTURAL_KEY_PLUS_INTACT_DEFINITION => EXACT_CONGRUENCE`
- `HISTORICAL_PROVENANCE != CURRENT_FUNCTIONALITY`
- `POLY_IN_CURRENT_STATE != POLY_IN_ORIGINAL_INPUT`
- `CHEAP_LOCAL_CONGRUENCE != UNIVERSAL_BOUNDARY_QUOTIENT`
