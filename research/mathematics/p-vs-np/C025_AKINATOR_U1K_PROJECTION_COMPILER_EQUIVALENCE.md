# C025 — Akinator U1-K: uniform exact projection compilation is essentially P=NP

Status: **UNIFORM_SEMANTIC_PROJECTION_COMPILER_EQUIVALENCE_PROVED / PROOF-CARRYING_ER_VERSION_STRONGER_AND_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The projection route has become very strong, so a claim-ceiling firewall is required:

> a universal polynomial-time exact projection compiler is not merely a helpful lemma on the way to P=NP; in its broad semantic form it is essentially equivalent to P=NP.

This prevents circularity: restating SAT as “compile existential projections efficiently” is not itself progress unless the compiler is obtained from additional independent structure.

---

## 1. Define the semantic projection compiler

A **uniform exact B2 projection compiler** is a deterministic polynomial-time algorithm `PROJ` such that, given a Boolean/B2 circuit

`C(x,y)`

with a designated block `x` to eliminate, it outputs a quantifier-free B2 circuit

`D(y)`

satisfying

`D(y) = 1 iff exists x C(x,y)=1`

for every y, with `|D|` polynomial in the explicit input circuit size.

For this theorem we ask only semantic correctness of the compiler as an algorithm. We do **not** additionally require a polynomial Extended-Resolution proof certificate of each compiled equivalence.

---

## 2. Projection compiler implies P=NP

Given arbitrary CNF/circuit `F(z)`, invoke the compiler with the entire variable block `z` designated for elimination and no remaining y-inputs.

The output is a zero-input Boolean circuit/constant `D` such that

`D=1 iff exists z F(z)=1`.

Constructing `D` and evaluating a zero-input circuit are polynomial time.

Hence SAT is in P.

Therefore

`UNIFORM_POLY_EXACT_PROJECTION_COMPILER => P=NP`.

The same conclusion follows from repeated one-variable compilation provided global state/output/work remain polynomial across the run.

---

## 3. P=NP implies a uniform semantic projection compiler

Assume `P=NP`.

Fix a circuit `C(x,y)`. Consider the language/function

`f_C(y) = 1 iff exists x C(x,y)=1`.

The decision problem on input `(C,y)` is in NP: x is the witness and C can be evaluated in polynomial time. Under `P=NP`, there is one fixed deterministic polynomial-time algorithm `A(C,y)` computing this predicate.

Now hardwire the description of C into `A` and regard y as the only live input.

Standard uniform circuit simulation of polynomial-time Turing machines gives a P-uniform polynomial-size Boolean circuit family for every polynomial-time computation. Hence, from C and its input lengths, one can construct in polynomial time a circuit `D_C(y)` simulating `A(C,y)` with C hardwired.

Translate the resulting ordinary Boolean circuit to frozen B2 (AND with signed literals) with standard polynomial/constant-factor gate-basis overhead.

Then

`D_C(y) = exists x C(x,y)`

and `D_C` has polynomial size and polynomial-time uniform construction.

Therefore

`P=NP => UNIFORM_POLY_EXACT_SEMANTIC_PROJECTION_COMPILER`.

So, at the broad semantic-constructor level:

**P=NP iff a universal uniform polynomial exact existential-projection compiler exists.**

### External basis for the circuitization step

Standard complexity theory: a language is computable by a P-uniform polynomial-size circuit family iff it is in P. See Arora–Barak, *Computational Complexity*, the chapter on uniformly generated circuits (Theorem 6.13 in the publicly available draft/notes).

---

## 4. Important caveat — proof-carrying ER compilation may be stronger

The current JANUS program often requires not just a semantically correct output circuit, but a polynomially checkable **B2/Extended-Resolution proof object** certifying the transformation.

`P=NP` implies `NP=coNP`, and it implies existence of some polynomially bounded Cook–Reckhow proof system, but it does **not** automatically establish that the specific Extended-Resolution system is p-bounded or that every projection-equivalence tautology has a short ER proof.

Therefore this note does **not** claim:

`P=NP <=> universal proof-carrying ER projection compiler`.

Only the semantic uniform compiler equivalence is proved here.

This distinction preserves issue #217 / full ER proof-complexity uncertainty.

---

## 5. Why U1-I remains useful despite the equivalence

The route is still valuable because it decomposes the original P-vs-NP question into concrete falsifiable sub-obligations and exposes where naive algorithms fail:

- Davis–Putnam: exact descent but exponential clause state;
- naive B2 Shannon: exact descent but exponential copying;
- cofactor caching: exponential even when final projection is small;
- semantic target recognition: coNP-complete;
- brute-force replacement-block search: exponential;
- family-specific algebraic compression: succeeds for Inner Product, PHP, affine/Horn/etc.

A genuine breakthrough must provide **new independent structural machinery** that constructs the compiler, rather than assuming the compiler as a black box.

---

## 6. Nonuniform size-only variant

If we drop construction and assume only:

> for every polynomial-size NP verifier circuit, its existential projection has a polynomial-size circuit,

then every NP language has polynomial-size circuits:

`NP subseteq P/poly`.

This is weaker than P=NP because the circuits need not be uniformly constructible.

By the external Karp–Lipton theorem,

`NP subseteq P/poly => PH collapses to Sigma_2^p`.

Thus even the existence-only projection-size theorem would be a major complexity consequence, but it still must not be labeled P=NP.

---

## 7. New exact gate — structure beyond equivalence

Because the unrestricted semantic compiler is equivalent to the target theorem, the next useful question must impose a concrete independently analyzable mechanism.

Current candidate:

**U1-L CERTIFIED LOCAL-TO-GLOBAL PROJECTION GRAMMAR**

Build a frozen finite/polynomial family of structural reduction rules and a decomposition theorem showing that every B2 state can be reduced by those rules with polynomial total state/work.

The decomposition/completeness theorem — not the abstract existence of a compiler — would constitute actual progress.

---

## 8. Current status

`UNIFORM_SEMANTIC_PROJECTION_COMPILER <=> P_EQUALS_NP = PROVED`

`NONUNIFORM_POLY_PROJECTION_SIZE => NP_SUBSET_P_POLY = PROVED`

`KARP_LIPTON_PH_COLLAPSE = EXTERNAL_THEOREM`

`PROOF_CARRYING_ER_PROJECTION_COMPILER_EQUIVALENCE = NOT_CLAIMED`

`CERTIFIED_LOCAL_TO_GLOBAL_PROJECTION_GRAMMAR = OPEN`

`P_VS_NP = OPEN`

---

## 9. New laws

- `REFORMULATING_P_EQUALS_NP_AS_A_UNIVERSAL_PROJECTION_COMPILER_IS_NOT_BY_ITSELF_PROGRESS`
- `UNIFORM_PROJECTION_CONSTRUCTION_IS_THE_CRITICAL_DIFFERENCE_FROM_NONUNIFORM_SIZE_EXISTENCE`
- `P_EQUALS_NP_DOES_NOT_AUTOMATICALLY_PROVE_ER_P_BOUNDEDNESS`
- `ACTUAL_PROGRESS_REQUIRES_ADDITIONAL_STRUCTURAL_MECHANISM_BEYOND_THE_EQUIVALENT_COMPILER_STATEMENT`
