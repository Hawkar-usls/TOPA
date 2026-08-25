# C025 — Akinator U1-E: derivational-rank presentation sensitivity versus semantic quotient hardness

Status: **FIXED_PRESENTATION_RANKS_REFUTED_AS_UNIVERSAL_INVARIANTS / CERTIFIED_QUOTIENT_RANK_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Target

U1-C reduced the polynomial Akinator route to a cheap exact global descent potential. U1-D killed several naive semantic/syntactic potentials. The next idea is a genuinely derivational rank: count remaining proof obligations, chosen-proof depth, unresolved proof nodes, or distance along a frozen goal DAG.

This note closes the strongest naive version of that idea.

A derivational rank tied to one syntactic presentation can be distorted arbitrarily by conservative alias chains that do not change the root problem. Repairing this by quotienting arbitrary B2 macros under exact semantic equivalence reintroduces a coNP-hard problem in the general circuit scope.

This does **not** rule out a proof-carrying/certificate-based quotient or another representation-stable rank.

---

## 1. Frozen alias-chain family

Take root CNF

`F = { (x), (t) }`.

Thus both root literals `x` and `t` are forced true.

Introduce fresh B2 extension variables:

`e_1 <-> (x AND t)`

and for `i >= 2`

`e_i <-> (e_{i-1} AND t)`.

Every definition is legal under the frozen rule because the two operands have distinct variable IDs and each extension uses only earlier variables.

By induction under `F`,

`e_i <-> x`

for every `i`.

Hence all targets `x,e_1,...,e_k` encode the same root truth on every model of `F` plus the definitions.

---

## 2. Exact derivation-chain inflation

The B2 definition for `e_i <-> (a AND t)` contains

`(e_i OR ~a OR ~t)`.

Given unit clauses `(a)` and `(t)`, two Resolution steps derive `(e_i)`:

1. resolve `(e_i OR ~a OR ~t)` with `(a)` -> `(e_i OR ~t)`;
2. resolve with `(t)` -> `(e_i)`.

Starting from root unit `(x)`, deriving `(e_k)` along the chain therefore has an explicit `2k`-step forward derivation (ignoring constant bookkeeping), while the equivalent root target `(x)` is already an axiom.

The semantic root problem is unchanged; only the chosen presentation/alias target has changed.

Thus ranks such as

- depth of the selected derivation DAG,
- number of unresolved nodes on a selected alias chain,
- remaining steps in one preselected proof trace,
- syntactic distance to one chosen target literal,

can be inflated by arbitrary `k` within the permitted serialized state budget without changing the underlying root fact.

Therefore:

**FIXED_PRESENTATION_DERIVATION_LENGTH != PROBLEM_INVARIANT.**

### Claim ceiling

This does not prove such a rank cannot be useful inside one frozen algorithm that never creates decorative aliases. It proves only that raw chosen-presentation depth/count is not automatically a representation-stable global solver potential.

---

## 3. Root-only ranks do not repair extension descent

One could demand that the rank ignore all extensions and depend only on the original root CNF/current root assignment.

But then a pure conservative B2 extension step leaves that root object unchanged, so every such root-only rank has

`mu(S') = mu(S)`

on the extension step.

Therefore a root-only rank cannot provide strict descent on an extension-driven transition unless the transition also changes some separately defined root proof obligation.

This creates a real design tension:

- inspect extension/proof presentation -> risk presentation sensitivity;
- ignore extension presentation -> pure extension steps cannot descend.

---

## 4. Exact semantic quotient is not free

The obvious repair is to identify extension macros whenever they compute the same Boolean function, so all alias chains collapse to one semantic node.

For arbitrary B2 circuits, exact equivalence is coNP-complete.

### Membership

Non-equivalence has a polynomial witness: a root assignment on which the two circuits differ. Both circuits can be evaluated in polynomial time.

### Hardness

B2 AND with signed literals is functionally complete. Given an arbitrary Boolean circuit/CNF `F`, construct a B2 circuit `C_F` for its Boolean function and compare it with the constant-false function (or equivalently test whether `C_F` is identically false). Circuit unsatisfiability/tautology-equivalence gives the standard coNP-hardness reduction.

The earlier D1 semantic-classifier work already records constant/equivalence hardness in this frozen general-circuit scope.

Hence:

**ARBITRARY_EXACT_SEMANTIC_ALIAS_QUOTIENT != CHEAP_CANONICALIZATION.**

Relative equivalence under root constraints is no easier in the general case, since the unconstrained case is a special case.

---

## 5. The new dichotomy

The naive universal derivational-rank repair now faces:

### A. Presentation-sensitive rank

Cheap to compute from the explicit chosen proof/goal DAG, but alias/rewrite choices can change the value without changing the underlying root obligation.

### B. Full semantic quotient rank

Representation-stable in principle, but exact quotienting arbitrary B2 macros requires solving a coNP-hard equivalence problem in general.

Neither route supplies the required cheap universal descent potential for free.

This is not an impossibility theorem for every derivational rank.

---

## 6. Surviving repair — proof-carrying quotient

The promising repair is intermediate:

> merge two proof objects only when the state contains a short, independently checkable equivalence/implication certificate.

For the alias chain above, `(t)` plus the B2 definitions gives such certificates cheaply; no semantic oracle is needed.

Define a **certified quotient graph** whose nodes are proof objects modulo only equivalences currently justified by accepted proof certificates.

A rank over this graph could potentially be:

- cheaper than full semantic equivalence;
- more stable than raw syntax;
- extension-sensitive;
- proof-carrying.

But universal completeness is now a new theorem obligation: every decorative/redundant distinction that would otherwise spoil progress must either be harmless to the rank or admit a polynomially discoverable certificate.

---

## 7. New exact gate — U1-F certified derivational quotient rank

Construct an exact rank `mu_Q(S)` over a proof-carrying quotient of the current derivational state.

Admission requirements:

1. quotient certificates are polynomial-size and polynomial-time verifiable;
2. quotient update is polynomial in original input `N`;
3. no arbitrary circuit-equivalence oracle;
4. rank is polynomially bounded and exactly computable;
5. alias/decorative rewrites with short certificates do not alter rank materially;
6. every nonterminal state has some one-step B2 candidate plus local certificate that strictly lowers rank;
7. rank zero/terminal condition implies exact SAT/UNSAT completion;
8. total state remains polynomial.

First positive control: Cook/PHP-style family-specific extension generator, where each certified reduction stage has a natural decreasing instance-size/stage rank.

First adversarial controls: selector-lift, graph-PHP outside the exact Cook embedding, NW-local hard family, F3D collapse, parity/inner-product reuse, and p-reencoding wrappers.

---

## 8. Current state

`FIXED_PRESENTATION_DERIVATIONAL_RANK = REFUTED_AS_UNIVERSAL_INVARIANT`

`FULL_SEMANTIC_QUOTIENT = coNP_HARD_IN_GENERAL_SCOPE`

`PROOF_CARRYING_QUOTIENT_RANK = OPEN`

`CHEAP_EXACT_GLOBAL_DESCENT_POTENTIAL = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 9. New laws

- `CHOSEN_PROOF_DEPTH != PROBLEM_INVARIANT`
- `ROOT_ONLY_RANK != EXTENSION_DESCENT`
- `SEMANTIC_ALIAS_QUOTIENT != CHEAP_CANONICALIZATION`
- `PRESENTATION_INVARIANCE_MUST_BE_PAID_FOR`
- `PROOF_CARRYING_EQUIVALENCE_MAY_BE_CHEAPER_THAN_FULL_SEMANTIC_EQUIVALENCE`
- `FIXED_PRESENTATION_BARRIER != UNIVERSAL_DERIVATIONAL_RANK_IMPOSSIBILITY`
