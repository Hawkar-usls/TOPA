# C025-B — Context-Independent Proof-Carrying Reason

**Status:** reason semantics and soundness route frozen; standalone verifier/probe required for promotion.

**Claim ceiling:** this closes a soundness/interface problem for returned UNSAT reasons. It does **not** prove polynomial-time SAT, polynomial proof search, polynomial cache lookup, polynomial state size, `P=NP`, or `P!=NP`.

## 1. Why a Boolean cache is insufficient

An exact cache entry of the form

```text
residual K -> UNSAT
```

is sound only for that exact residual key. C025 needs a reusable object that remains valid under a different decision context without relying on residual similarity, hash collisions, or an unproved subsumption heuristic.

The first Policy-0B reason language is deliberately stricter than the formula-level returned reasons used by `FCW_reason` in Beame–Impagliazzo–Pitassi–Segerlind. The paper proves that `FCW_reason` can p-simulate regular Resolution, but C025 does not import that power automatically. We first freeze a smaller object whose reuse theorem is transparent.

## 2. Frozen reason object

Let `F0` be the canonical root CNF. A Policy-0B proof-carrying reason is

```text
R = (root_fingerprint, clause C, resolution_DAG pi)
```

with the following requirements.

1. `C` is a canonical, non-tautological clause over variables of `F0`.
2. `pi` is a DAG derivation whose leaves are indexed clauses of `F0`.
3. Every internal node is an exact Resolution step.
4. The final node of `pi` is exactly `C`.
5. `root_fingerprint` binds the certificate to the canonical encoding of `F0`.

No decision assumption is an axiom of `pi`.

This last rule is the context-independence firewall.

## 3. Applicability

For a partial assignment `rho`, define

```text
APPLIES(R, rho)
```

iff `rho` assigns every variable appearing in `C` and makes every literal of `C` false.

Equivalently, `rho` falsifies `C`.

A reason may be reused at any context satisfying this predicate. The new context does not need to equal, extend, or resemble the context in which the reason was first discovered.

## 4. Soundness theorem

### Lemma B1 — certificate soundness

If the standalone verifier accepts `pi` against root formula `F0` and final clause `C`, then

```text
F0 |= C.
```

**Proof.** Every leaf is a clause of `F0`. Resolution preserves logical consequence. Induction over the topological order of the proof DAG gives that every derived node is implied by `F0`, in particular the final clause `C`. □

### Theorem B2 — context-independent reuse

If `VERIFY(F0,R)=PASS` and `APPLIES(R,rho)`, then

```text
UNSAT(F0 | rho).
```

**Proof.** By Lemma B1 every model of `F0` satisfies `C`. But `rho` falsifies every literal of `C`, so no model of `F0` can extend `rho`. □

This is the core C025-B property.

## 5. Branch-composition theorem

Let `rho` be a parent context and `x` an unassigned branch variable. Suppose the false child returns certified reason `C0` applicable to `rho ∪ {x=0}`, and the true child returns certified reason `C1` applicable to `rho ∪ {x=1}`.

Exactly one of the following safe cases applies.

1. `rho` already falsifies `C0`: return `C0` unchanged.
2. `rho` already falsifies `C1`: return `C1` unchanged.
3. Otherwise `C0` must contain literal `x`, and `C1` must contain literal `~x`. Resolve the two certified clauses on `x` and return the resolvent `C`.

### Lemma B3 — parent reason is certified and applicable

In case 3, the new proof is obtained by adding one Resolution node whose parents are the final proof nodes for `C0` and `C1`. The parent assignment `rho` falsifies every remaining literal of the resolvent.

**Proof.** A clause falsified by `rho ∪ {x=0}` but not by `rho` can depend on the new assignment only through literal `x`; it cannot contain `~x`, which would be true in the false child. Symmetrically, the true-child reason can depend on the branch only through `~x`. Removing the complementary branch literals leaves only literals already false under `rho`. Resolution soundness gives the certificate. □

Thus recursive UNSAT reasons can be lifted toward the root without embedding the decision context into the proof axioms.

## 6. Unit-propagation conflict lifting

Every propagated literal `l` must carry an antecedent clause

```text
(l OR A)
```

that is itself an original clause or an already certified global reason, with all literals of `A` false immediately before propagating `l`.

If a certified conflict clause `K` becomes false, process propagated literals in reverse propagation order. Whenever current conflict clause contains `~l`, resolve it with the antecedent of `l`. This removes that propagated variable while preserving a globally certified clause.

### Lemma B4 — reverse propagation produces a decision-only reason

After eliminating all propagated literals that occur in the conflict clause, the remaining clause is falsified by the decision assignment alone and is derivable from `F0` by the appended Resolution steps.

The number of added Resolution nodes is at most the number of propagated assignments participating in the conflict chain.

This is a deterministic local extraction procedure **given the propagation trace**.

## 7. Standalone verifier model

The verifier accepts only a canonical root CNF and a proof DAG with nodes of two forms:

```text
AXIOM(source_clause_index)
RESOLVE(left_node, right_node, pivot)
```

For every Resolution node it recomputes the exact canonical resolvent. Tautological derived clauses are rejected in the first reason language because they cannot be falsified by a context and provide no reusable conflict reason.

The final node must equal the advertised reason clause and the root fingerprint must match.

### Lemma B5 — verification cost is polynomial in certificate size

Let `M` be the total encoded size of the proof DAG, including all stored clauses and indices. A deterministic verifier using sorted canonical clauses can check each axiom and merge each Resolution pair in time polynomial in `M` (linear in parent-clause length up to integer/identifier comparison costs).

This is a certificate-size bound, **not** a proof that `M` is polynomial in the original CNF size.

## 8. Cost firewall

C025-B deliberately separates four quantities:

```text
REASON_VALIDITY
REASON_LOCAL_CONSTRUCTION
REASON_DISCOVERY_IN_CACHE
TOTAL_REASON_DAG_SIZE
```

What B can establish:

- validity/reuse soundness;
- branch composition with at most one new Resolution node;
- unit-conflict lifting with at most one Resolution node per eliminated propagated variable;
- standalone verification polynomial in certificate size.

What remains open:

- finding an applicable reason among a large cache;
- proving the accumulated reason DAG is polynomial in original input length;
- proving the solver reaches useful conflicts/reasons in polynomial total search;
- proving this clause-only reason language has the same proof-system strength as the paper's formula-level `FCW_reason`.

Therefore

```text
SHORT_REASON_EXISTS != POLICY0B_FINDS_IT_IN_POLYTIME
CHEAP_REASON_CHECK != CHEAP_REASON_DISCOVERY
POLY_VERIFY_IN_CERTIFICATE_SIZE != POLY_CERTIFICATE_SIZE_IN_INPUT
```

## 9. Literature boundary

Beame, Impagliazzo, Pitassi, and Segerlind, *Formula Caching in DPLL*, ACM TOCT 1(3), 2010, define `FCW_reason`, show returned reasons are strengthenings of the recursive formula, and prove that their system p-simulates regular Resolution.

C025 uses that result only as motivation. No theorem transfer is allowed until equivalence or a proved simulation between the exact C025 clause-reason calculus and the literature system is established.

## 10. Promotion gates

C025-B may be promoted to `PROVED_IN_SCOPE` only after:

1. standalone verifier implementation;
2. positive replay of direct reason verification;
3. cross-context reuse replay;
4. branch-composition replay;
5. unit-propagation conflict-lifting replay;
6. malformed certificate rejection tests;
7. root-fingerprint mismatch rejection;
8. independent derivation review.

Current status:

```text
C025_B_REASON_SEMANTICS               = FROZEN
C025_B_CONTEXT_INDEPENDENT_REUSE      = PROVED_ON_PAPER
C025_B_BRANCH_COMPOSITION             = PROVED_ON_PAPER
C025_B_UNIT_CONFLICT_LIFT             = PROVED_ON_PAPER
C025_B_STANDALONE_VERIFIER            = NEXT
C025_C_REASON_DISCOVERY_SEARCH_COST   = OPEN
C025_E_TOTAL_REASON_SIZE              = OPEN
P_VS_NP                               = OPEN
```
