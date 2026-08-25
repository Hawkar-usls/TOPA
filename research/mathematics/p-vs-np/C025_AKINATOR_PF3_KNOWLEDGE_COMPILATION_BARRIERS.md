# C025 — Akinator PF3-KC: knowledge-compilation representation barriers

Status: **MULTIPLE RESTRICTED UNIVERSAL-QUOTIENT ROUTES CLOSED BY EXTERNAL SIZE LOWER BOUNDS**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Question

PF2/PF3 asks whether the joint projected boundary relation can always be converted into an exact representation whose total construction, state, verification and witness-provenance costs are bounded by one fixed polynomial in original CNF length `N`.

Before inventing a new representation, we audit mature knowledge-compilation languages whose purpose is precisely to represent Boolean functions compactly while supporting tractable queries.

A lower bound against one representation language is **not** a lower bound against arbitrary Boolean circuits or against SAT itself. It closes only the route that requires every relevant state/function to be compiled into that language with polynomial size.

---

## 1. DNNF universal-container route is closed

External source:

Simone Bova, Florent Capelli, Stefan Mengel, Friedrich Slivovsky, **A Strongly Exponential Separation of DNNFs from CNF Formulas**, arXiv:1411.1995.

The source states that there exists a class `C` of CNF formulas such that, for every `F in C`, every equivalent DNNF has size

`2^Omega(n)`

where `n` is the number of variables of `F`.

The formulas are sparse graph CNFs built from bounded-degree expander graphs; they are monotone 2-CNFs. The source identifies a graph CNF with

`AND_{ {x,y} in E } (x OR y)`

and proves the strongly exponential DNNF lower bound via a bottleneck/certificate argument.

Since the source CNFs themselves have only linear-size sparse graph descriptions, this is an unconditional exponential representation separation.

Therefore:

`UNIVERSAL_POLY_EXACT_BOUNDARY_QUOTIENT_AS_DNNF = REFUTED`.

Any Akinator/BQ lane that requires the exact current Boolean function or boundary relation to *always* be materialized as a DNNF of polynomial size is dead.

This automatically applies to subclasses of DNNF as a universal representation route. It does not apply to arbitrary unrestricted B2 circuits.

---

## 2. OBDD / path-structured route has independent width barriers

Existing TOPA ROBDD notes already record order sensitivity and external order-discovery hardness.

A stronger structural source boundary is supplied by Amarilli, Monet and Senellart, **Connecting Width and Structure in Knowledge Compilation**, ICDT 2018, DOI `10.4230/LIPIcs.ICDT.2018.6`.

For bounded-arity, bounded-degree monotone CNF/DNF, their lower bounds relate OBDD width exponentially to pathwidth and structured DNNF size exponentially to treewidth (with the stated arity/degree factors).

Thus high-width formulas can force exponential OBDD/structured-DNNF representation even without using heuristic order arguments.

Exact ceiling:

`WIDTH_BASED_KC_LOWER_BOUND != LOWER_BOUND_AGAINST_UNRESTRICTED_B2_CIRCUITS`.

---

## 3. SDD and other tractable descendants do not rescue a DNNF-hard function

Every representation class that is literally a syntactic subclass of DNNF inherits a DNNF size lower bound on the same Boolean function: if the smallest DNNF is exponential, a more restricted DNNF subclass cannot be smaller.

This observation is set inclusion, not a new external theorem.

For representation classes not contained in DNNF, no transfer is claimed without an explicit simulation/containment theorem.

The separate Beame–Liew line also contains strong SDD/DNNF lower bounds, but the DNNF expander theorem already suffices to kill the universal-DNNF-container shortcut.

---

## 4. Why this matters for the boundary quotient

PF2 showed that exact existential projection may leave a joint boundary relation whose correlations must be represented somehow.

The DNNF result means the following universal design is impossible:

```text
CURRENT EXACT STATE
  -> compile boundary/current function to polynomial DNNF
  -> perform tractable conditioning/projection
  -> repeat
```

because there are already polynomial-size CNF inputs whose **initial exact function** has no polynomial DNNF representation.

So the exponential does not even need repeated projection to enter this lane.

---

## 5. Positive width-restricted lane remains valid

The same knowledge-compilation literature gives constructive upper bounds when structural width is bounded.

For example, bounded-treewidth CNF/circuits can be compiled into structured deterministic DNNF with singly-exponential dependence on width, and quantifier elimination costs are controlled by the representation width.

This is consistent with our internal live-width theorem:

`lambda=O(log N)`

is a polynomial exact relational lane.

Hence:

`LOW_WIDTH = TRACTABLE_SPECIAL_CASE`

and

`UNBOUNDED_WIDTH + DNNF_CONTAINER = NOT_UNIVERSALLY_POLY`.

No contradiction exists: the first is parameterized/restricted, the second is a universal representation claim.

---

## 6. PF3 representation map after the sweep

### Closed as universal exact quotient containers

- frozen syntactic Shannon/hash-cons projector — internal equality counterfamily;
- OBDD/ROBDD as a universal polynomial exact representation — known size/width barriers plus order issues;
- ZDD/BDD family-operation canonicalization — ISAAC 2024 operation blow-up in source representation scope;
- DNNF and every literal DNNF subclass as a universal polynomial exact container — Bova et al. expander-CNF theorem.

### Still valid restricted lanes

- PF1 local prebirth pivot factorization;
- deterministic live-width DP when `lambda=O(log N)`;
- ROBDD on families/orders with polynomial explicit size and paid deterministic order;
- exact prebirth orbit quotient on certified families such as the frozen equality control.

### Still open universal route

A quotient language not constrained to a representation family already carrying known exponential size lower bounds, together with deterministic polynomial discovery and a global polynomial novelty/progress theorem.

---

## 7. What remains mathematically possible

Unrestricted Boolean circuits are much more succinct than DNNFs. The DNNF lower bound therefore points us away from **tractability-by-decomposability as a universal representation principle**, but it does not prove unrestricted circuits must be exponential.

However unrestricted circuits restore the hard operation that restricted KC languages were designed to make easy:

- exact equivalence;
- exact existential projection simplification;
- discovery of a small equivalent quotient.

General circuit equivalence is coNP-complete, already recorded by PF2.

So the representation/discovery tension becomes explicit:

`RESTRICT_REPRESENTATION -> TRACTABLE_OPERATIONS_BUT_EXPONENTIAL_SIZE_ON_SOME_CNFS`

`ALLOW_GENERAL_CIRCUITS -> SUCCINCTNESS_BUT_NO_FREE_SEMANTIC_QUOTIENT_DISCOVERY`.

This is the current PF3 trilemma in its strongest form so far.

---

## 8. Next exact gate — PROOF-CARRYING REWRITE SYSTEM

The next candidate does not demand a canonical tractable representation.

Instead, keep a general B2/Boolean DAG and allow only **locally proof-carrying exact rewrites** whose correctness is syntactic/algebraic and polynomially verifiable.

Required theorem:

For every current exact state, a deterministic polynomially enumerable rewrite/projection step exists such that:

1. at least one original root is existentially eliminated;
2. resulting DAG bytes remain under `N^K` for one universal fixed `K`;
3. cumulative created/failed-work bytes remain under `N^K`;
4. every rewrite has a polynomial certificate;
5. witness/provenance reconstruction is polynomial;
6. no semantic-equivalence/SAT/#SAT oracle is used;
7. no exponential backtracking over rewrite sequences is hidden.

PF1 is one member of such a rewrite language. Equality prebirth orbit is another restricted member.

Universal availability/completeness is OPEN.

---

## 9. Claim ledger

`DNNF_EXPANDER_CNF_STRONGLY_EXPONENTIAL_LOWER_BOUND = EXTERNAL_SOURCE_THEOREM`

`UNIVERSAL_POLY_DNNF_BOUNDARY_QUOTIENT = REFUTED`

`DNNF_SUBCLASS_UNIVERSAL_POLY_CONTAINER = REFUTED_BY_CONTAINMENT_ON_SOURCE_FAMILY`

`OBDD_STRUCTURED_KC_WIDTH_BARRIERS = EXTERNAL_SOURCE_BOUND_FACTS`

`ARBITRARY_B2_CIRCUIT_POLY_QUOTIENT = NOT_REFUTED_BY_KC_LOWER_BOUNDS`

`PROOF_CARRYING_GENERAL_CIRCUIT_REWRITE_DISCOVERY = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 10. Laws

- `TRACTABLE_QUERY_LANGUAGE != UNIVERSAL_POLYNOMIAL_REPRESENTATION`
- `DNNF_LOWER_BOUND != GENERAL_CIRCUIT_LOWER_BOUND`
- `RESTRICTED_CANONICALITY_CAN_MOVE_THE_EXPONENT_INTO_REPRESENTATION_SIZE`
- `GENERAL_CIRCUIT_SUCCINCTNESS_MOVES_THE_HARDNESS_BACK_INTO_EQUIVALENCE_AND_REWRITE_DISCOVERY`
- `REPRESENTATION_CLASS_MUST_BE_AUDITED_BEFORE_IT_IS_ADOPTED_AS_THE_BOUNDARY_QUOTIENT`
