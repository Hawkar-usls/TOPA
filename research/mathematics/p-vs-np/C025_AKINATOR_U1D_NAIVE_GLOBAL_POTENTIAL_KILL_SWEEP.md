# C025 — Akinator U1-D: naive global descent potentials fail

Status: **MULTIPLE_NAIVE_POTENTIALS_REFUTED / DERIVATIONAL_POTENTIAL_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Target

U1-C reduced deterministic B2 selection to a single strong object: a polynomial-range, polynomial-time exact global potential `mu(S)` such that every nonterminal state has some legal one-step B2 move with strictly smaller potential.

This note attacks the most natural candidate potentials before any attempt to elevate them.

The result is negative but highly local: several candidates fail on a single conservative extension step or on tiny formulas.

---

## 1. Free root variables

Candidate:

`mu_free(S) = number of unassigned root variables`.

A pure B2 extension

`e <-> (a AND b)`

does not assign any root variable. Therefore

`mu_free(S') = mu_free(S)`

for every pure extension step.

So it cannot certify strict descent for extension-driven states.

**FREE_ROOT_COUNT = NO_UNIVERSAL_B2_DESCENT.**

Branching can decrease this quantity along one branch, but the earlier branch-mass theorem shows this does not pay for the total search tree.

---

## 2. Clause count and literal volume

A fresh B2 definition contributes the clauses

`(~e OR a)`, `(~e OR b)`, `(e OR ~a OR ~b)`.

Absent simultaneous justified deletion/strengthening elsewhere, this adds three clauses and seven literal occurrences under the ordinary explicit count.

Thus naive

`mu_clause = #clauses`

and

`mu_lit = total literal occurrences`

increase rather than decrease on the basic extension move.

Allowing deletion does not repair universality unless a separate theorem proves enough safe deletion on every step; that theorem would be a new obligation, not a property of the raw counts.

---

## 3. Number of variables/macros and one-step candidates

A B2 extension increases the variable count from `V` to `V+1`.

The complete ordered legal-pair candidate count is

`4 V(V-1)`

under the current `abs(a)!=abs(b)` signed-pair mechanics, before optional canonical commutative deduplication.

After adding a variable this becomes

`4(V+1)V`,

which is larger.

Hence neither

`mu_V = V`

nor raw next-candidate count is a descent measure.

---

## 4. Exact model count is invariant under conservative definitions

Let `F(x)` be a root CNF and introduce a fresh definitional extension

`e <-> g(x)`.

For every root assignment `alpha`, there is exactly one value of `e` satisfying the definition, namely `e=g(alpha)`.

Therefore projection from models of

`F(x) AND Def(e,g)`

to root assignments is a bijection with models of `F`.

Consequently:

`#Models_root(F AND Def(e,g)) = #Models(F)`

and the number of full models over `(x,e)` is the same as the number of root models because the extension bit is uniquely determined.

So exact model count does not descend on a pure extension step at all.

In addition, computing exact `#SAT(F)` for arbitrary CNF is #P-complete, so treating model count as a cheap potential would independently violate the no-hidden-oracle rule.

Thus:

**MODEL_COUNT = EXPENSIVE_AND_EXTENSION_INVARIANT.**

---

## 5. Support-coverage deficit reaches zero without solving

Candidate:

`mu_support = n - max_e |support(e)|`.

This appears to reward globally mixed macros.

But on the satisfiable nonterminal formula

`F(x1,x2) = (x1 OR x2)`

we can introduce

`e <-> (x1 AND x2)`.

Then `support(e)={x1,x2}`, so

`mu_support = 0`,

while the solver has not produced a particular satisfying assignment nor an UNSAT certificate. The formula still has three satisfying root assignments.

Thus zero support deficit is not a terminal correctness condition.

More generally, a linear-size AND/parity-style circuit can cover all root variables long before the proof obligation is resolved.

This agrees with earlier class-count/reuse barriers:

`GLOBAL_SUPPORT != PROOF_PROGRESS.`

---

## 6. F3 structural complexity is not a descent potential

Negative-frontier width `b`, inversion depth `d`, crossing count, support cover, etc. are lower-bound/escape resources, not monotone solver-distance measures.

Earlier F3D.D0 constructs arbitrarily large pre-restriction `(b,d)` that collapse after one root restriction. Conversely an extension can intentionally increase crossing complexity because escaping the NW-local barrier requires doing so.

Therefore neither increasing nor decreasing raw F3 structural complexity is universally synonymous with approach to terminal SAT/UNSAT.

---

## 7. Shortest-proof length is ideal-looking but hides proof search

The quantity

`mu_proof(S) = length of a shortest valid proof from S`

would have a natural descent property along an optimal proof.

But it is not admitted as a cheap potential merely by definition.

External result: Atserias–Müller, **Automating Resolution is NP-Hard** (JACM 2020), proves that finding a Resolution proof polynomially related to a shortest one is NP-hard.

Thus even in weaker Resolution, generic access to shortest-proof guidance contains the very proof-search difficulty we are trying to eliminate.

For full B2/ER the exact unconditional analogue is not claimed here.

---

## 8. What survives

The sweep eliminates these naive classes:

- remaining-variable counts;
- raw formula-size counts;
- raw extension/candidate counts;
- exact model count;
- support/globality deficit;
- raw F3 crossing/width-depth complexity;
- shortest-proof distance treated as a free oracle.

The potential must instead track a **derivational obligation** that:

1. is polynomially represented;
2. is polynomially and exactly computable;
3. is not invariant under conservative extension;
4. is not trivially manipulable by decorative macros;
5. cannot hit zero before exact termination;
6. provably has a decreasing B2 move at every nonterminal state;
7. has polynomial initial range in original input `N`.

---

## 9. New exact gate — U1-E derivational rank

We now search for a proof-relative rank rather than a semantic/model-set size.

A candidate must come with:

- a frozen canonical obligation graph or obligation multiset;
- an exact rank function over that object;
- polynomial update under one B2 extension/reason step;
- invariance against decorative proof rewrites/aliases;
- a universal descent lemma;
- terminal equivalence with exact SAT/UNSAT completion.

The first adversarial tests must include:

- selector-lift instances;
- graph-PHP/Cook positive control;
- NW-local hard family;
- F3D one-bit semantic collapse;
- parity/inner-product reuse counterfamilies;
- proof-reencoding `F <->_p Def(G_F) AND G_F` barrier.

Current status:

`NAIVE_GLOBAL_POTENTIALS = MULTIPLE_ROUTES_REFUTED`

`U1_E_DERIVATIONAL_RANK = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 10. New laws

- `CONSERVATIVE_EXTENSION_PRESERVES_MODEL_COUNT`
- `GLOBAL_SUPPORT != TERMINAL_PROGRESS`
- `FORMULA_SIZE != SOLVER_DISTANCE`
- `CANDIDATE_COUNT != SOLVER_DISTANCE`
- `LOWER_BOUND_RESOURCE != DESCENT_POTENTIAL`
- `SHORTEST_PROOF_DISTANCE != CHEAP_COMPUTABLE_RANK`
- `THE_NEXT_POTENTIAL_MUST_BE_DERIVATIONAL_NOT_MERELY_SEMANTIC_OR_SYNTACTIC`
