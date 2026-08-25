# C025 — Akinator RSPC: explicit-witness frontier explosion versus symbolic compatibility search

Status: **PROVED_IN_GENERAL_COMPOSITION_SCOPE / UNIVERSAL_SELECTOR_FRONTIER_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The previous RSPC note showed that exact residual nonconstancy has a short witness but finding such a witness is NP-complete for general Boolean circuits. A proposed repair was to retain positive/negative assignment witnesses compositionally so accepted B2 macros never need semantic SAT search.

This note closes the strongest naive version of that repair.

The core dichotomy is:

> if the compositional interface is required to be complete against arbitrary small point-macro partners, an explicit assignment frontier can require exponentially many retained witnesses; if the frontier is replaced by a compact symbolic representation, exact compatibility/intersection testing is SAT-hard in the general circuit scope.

This is a general composition barrier. It does **not** prove that every restricted Akinator selector, every source-matched Sokolov state, or every useful macro vocabulary requires exponential storage or SAT-hard search.

---

## 1. Frozen explicit-frontier model

For a Boolean function `g` over root support `S(g)`, an explicit positive witness is a total assignment on `S(g)` on which `g=1`.

Let `W1_frontier(g)` be the retained set of such positive assignments.

For an AND macro `e := g AND h`, the inherited-witness rule accepts a positive witness without semantic search when some

`alpha in W1_frontier(g)` and `beta in W1_frontier(h)`

are compatible on the shared roots. Their union is then a positive witness for `e`.

Call an explicit frontier **partner-complete** for a class `H` of future partners if whenever `g AND h` is nonconstant/satisfiable for `h in H`, the retained frontiers contain at least one compatible positive-witness pair.

---

## 2. Theorem A — exponential explicit frontier for parity against point partners

Let

`PAR_n(x_1,...,x_n) = x_1 XOR ... XOR x_n`.

`PAR_n` has a B2 AND/NOT representation of size `O(n)` using the standard constant-size XOR gadget recursively.

For every assignment `a in {0,1}^n`, define the point macro

`P_a(x) = AND_i l_i^a`

where `l_i^a = x_i` if `a_i=1` and `NOT x_i` if `a_i=0`.

Each `P_a` has B2 size `O(n)` and has exactly one positive assignment: `a`.

Consider only odd-parity assignments `a`, so `PAR_n(a)=1`. Then

`PAR_n AND P_a = P_a`,

which is nonconstant.

Suppose an explicit positive frontier `W1_frontier(PAR_n)` is partner-complete against all odd-parity point macros `P_a`.

For a fixed odd-parity `a`, the unique positive witness of `P_a` is `a`. Since `PAR_n` depends on every root variable, every explicit positive witness retained for `PAR_n` is a total assignment on all `n` roots. Compatibility with the total point assignment `a` therefore requires exact equality.

Hence `a` itself must occur in `W1_frontier(PAR_n)`.

There are exactly `2^(n-1)` odd-parity assignments. Therefore

`|W1_frontier(PAR_n)| >= 2^(n-1)`.

So:

**PARTNER_COMPLETE_EXPLICIT_ASSIGNMENT_FRONTIER_CAN_BE_EXPONENTIAL.**

### Claim ceiling

This theorem refutes only a universal interface that demands explicit-witness compatibility completeness against this exponentially large class of small point partners.

It does **not** prove that a polynomial selector must enumerate all point partners, that all useful future partners occur in one state, or that a source-matched hard family forces this exact interface.

---

## 3. Why storing one compressed symbolic witness-set is not a free repair

A natural repair is to replace the explicit frontier by a compact circuit/formula `R_g(x)` representing all positive witnesses of `g`.

Then exact compatibility of two symbolic frontiers requires deciding whether

`R_g(x) AND R_h(x)`

has a satisfying assignment (after identifying shared roots and existentially allowing private roots).

In the general circuit scope this is SAT-hard.

### Theorem B — symbolic frontier intersection is NP-complete

Membership in NP is immediate: a satisfying root assignment is a polynomial witness and both circuits can be evaluated in polynomial time.

For NP-hardness, given an arbitrary CNF `F(x)`, choose

`R_g(x) := F(x)` and `R_h(x) := TRUE`.

Then

`R_g AND R_h` is satisfiable iff `F` is satisfiable.

Thus exact nonempty-intersection testing for general compact symbolic frontiers is NP-complete.

So:

**COMPACT_SYMBOLIC_FRONTIER != CHEAP_EXACT_COMPATIBILITY.**

Again, restricted symbolic languages can be tractable. This theorem does not rule out a specially structured selector vocabulary.

---

## 4. The general-circuit RSPC dichotomy

The two theorems produce a clean barrier for the naive repair:

1. retain enough explicit full witnesses to make arbitrary small-partner AND composition complete -> exponential frontier is possible even for a linear-size parity macro;
2. compress the witness set symbolically -> exact compatibility/intersection is NP-complete in the unrestricted circuit representation.

Therefore a polynomial Akinator cannot obtain universal progress merely by choosing between `explicit assignment frontier` and `arbitrary compact symbolic frontier`.

The remaining route must exploit additional structure which simultaneously gives:

- polynomial-size witness/progress representation;
- polynomial-time exact compatibility;
- polynomial-time deterministic discovery;
- enough expressive power to escape the NW-local and low-(b,d) barriers;
- source-matched restriction robustness;
- a globally polynomial progress potential.

---

## 5. New exact target — tractable intersection language

Let `L_N` be a frozen family of certificate/frontier representations admitted by the selector on input length `N`.

The next admissible target is not `all circuits`. It is a restricted language with four proved properties:

1. **POLY_SERIALIZATION:** every retained object has `N^O(1)` bits;
2. **POLY_INTERSECTION:** exact nonempty intersection/compatibility of admitted objects is decidable in `N^O(1)` time;
3. **POLY_CLOSURE:** the required B2 composition/update operations keep objects inside `L_N` with `N^O(1)` cost;
4. **UNIVERSAL_PROGRESS_IN_TARGET_SCOPE:** every nonterminal target state has an admitted move with a proof-carrying global-progress certificate.

Properties 1–3 are representation/algorithmic obligations. Property 4 is the real completeness burden and remains OPEN.

Potential known tractable representation classes (Horn/Krom/affine/decomposable forms, bounded-width decision diagrams, etc.) are candidates only after an expressiveness barrier audit; tractability by itself is not progress.

---

## 6. Relation to known frozen results

- exact semantic survival witness discovery is NP-complete in general circuit scope;
- one retained positive witness is not compositionally complete;
- an explicit partner-complete assignment frontier can require `2^(n-1)` witnesses;
- arbitrary compact symbolic frontier intersection is NP-complete;
- NW-neighborhood-local B2/ER3 vocabularies are insufficient on the transferred NW hard family;
- low negative-frontier-width/inversion-depth vocabularies are insufficient in the stated F3 transfer scope;
- large pre-restriction structural complexity can collapse under one restriction (F3D.D0).

Together these results narrow the next route to a **restricted, tractable, compositionally closed, sufficiently expressive proof-carrying representation language**.

---

## 7. Next gates

### RSPC-T1 — tractable-frontier candidate deck
Freeze concrete representation classes with exact polynomial intersection and update algorithms.

### RSPC-T2 — expressiveness kill sweep
For each class, try to embed known hard-family structural requirements. Close classes that collapse to NW-local/low-(b,d)/bounded-width behavior.

### RSPC-T3 — closure-cost audit
Charge normalization, conjunction, negation, restriction and certificate update costs in original input length `N`.

### RSPC-T4 — no-backtracking selector theorem
Prove or refute that a frozen deterministic rule always finds a valid next object without exponential alternative-schema exploration.

### RSPC-T5 — global progress
Only after T1–T4, require a polynomially bounded global potential reaching exact SAT/UNSAT termination.

Until these are discharged:

**PROOF_CARRYING_STRUCTURAL_SELECTOR = OPEN**  
**POLYNOMIAL_AKINATOR = OPEN**  
**P_VS_NP = OPEN**

---

## 8. New laws

- `EXPLICIT_WITNESS_FRONTIER != COMPACT_COMPLETE_INTERFACE`
- `SMALL_MACRO != SMALL_COMPLETE_WITNESS_FRONTIER`
- `COMPACT_SYMBOLIC_FRONTIER != CHEAP_EXACT_INTERSECTION`
- `TRACTABLE_REPRESENTATION != UNIVERSAL_PROGRESS`
- `PARTNER_COMPLETENESS_OVER_EXPONENTIAL_CLASS != POLYNOMIAL_SELECTOR_ENUMERATION_REQUIREMENT`
- `GENERAL_COMPOSITION_BARRIER != SOURCE_MATCHED_SELECTOR_LOWER_BOUND`
