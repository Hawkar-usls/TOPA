# C025 — Akinator U1-I2: exact projection-target recognition is already coNP-complete

Status: **SEMANTIC_TARGET_RECOGNITION_ROUTE_CLOSED_IN_GENERAL_B2_SCOPE / PROOF_CARRYING_SYNTACTIC_LIBRARY_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-I1 gave a strong positive control: the Inner Product family has exponentially many distinct cofactors but a linear-size exact projection, and a local algebraic identity discovers that compact projection without enumerating the cofactor cloud.

The next tempting strategy is:

> generate several small replacement candidates and semantically test which one equals the exact projection.

This note closes that strategy in general B2 scope. Even recognizing the simplest possible target — the constant TRUE projection — is coNP-complete.

This does **not** rule out syntactic pattern matching or proof-carrying rewrite templates whose applicability comes with a local certificate.

---

## 1. Decision problem

Define `PROJ_TRUE_B2`:

Input:
- a B2 circuit `C(x,y_1,...,y_m)`;
- one distinguished root variable `x`.

Question:

`is (exists x C(x,y)) identically TRUE as a function of y?`

Equivalently:

`for every y, C(0,y) OR C(1,y) = 1?`

---

## 2. Membership in coNP

A NO-instance has a short witness: an assignment `beta` to `y` such that

`C(0,beta)=0`

and

`C(1,beta)=0`.

Both circuit evaluations are polynomial in the explicit B2 size.

Therefore the complement is in NP and `PROJ_TRUE_B2` is in coNP.

---

## 3. coNP-hardness

Take arbitrary Boolean circuit/formula `F(y)` and introduce fresh variable `x`.

Construct

`C_F(x,y) := x AND F(y)`.

Frozen B2 is functionally complete, so `F` has a polynomial-size B2 translation, and the outer AND adds constant overhead.

Then

`exists x C_F(x,y)`

is exactly `F(y)`:

- if `F(y)=0`, both x-values give 0;
- if `F(y)=1`, choose x=1.

Hence

`exists x C_F == TRUE`

iff

`F == TRUE`.

Circuit/formula tautology is coNP-complete. Thus `PROJ_TRUE_B2` is coNP-hard.

Combined with membership:

**PROJ_TRUE_B2 is coNP-complete.**

---

## 4. General target equivalence

A more general recognition task gives both `C(x,y)` and a candidate replacement `R(y)` and asks whether

`R(y) <-> exists x C(x,y)`

for all y.

This problem is also coNP-complete:

- non-equivalence has a witness y where the two sides differ;
- hardness follows by taking `R=TRUE` and the reduction above.

Therefore:

**SMALL_REPLACEMENT_CANDIDATE != CHEAP_EXACT_REPLACEMENT_RECOGNITION.**

---

## 5. Consequence for local rewrite libraries

A library of algebraic templates can still be scientifically valid if applicability is established syntactically or by a polynomial proof certificate.

For example, the Inner Product rule

`exists x ((x AND y) XOR R) = y OR R`

is cheap when the current DAG explicitly contains the required decomposition and a syntactic support check proves `x` is absent from `R`.

What is forbidden is the hidden step:

> “try to notice whether an arbitrary circuit is semantically equivalent to this pattern.”

That recognition can contain circuit equivalence/tautology.

Thus the rewrite engine must distinguish:

- **SYNTACTIC_MATCH:** cheap structural pattern recognized in the actual DAG;
- **PROOF_CARRYING_MATCH:** nontrivial match accompanied by an accepted equivalence/decomposition proof;
- **SEMANTIC_MATCH:** unrestricted exact equivalence query — not admitted as a free operation.

---

## 6. Why finite/poly candidate lists do not fix it

Even if the replacement deck contains only polynomially many small candidates `R_1,...,R_q`, testing exact semantic projection equality against each candidate can still be coNP-hard, because the deck may contain `TRUE` and the first target-recognition problem is already coNP-complete.

Therefore:

`POLY_REPLACEMENT_DECK != POLY_EXACT_TARGET_SELECTION`.

The same separation seen earlier for extension candidates reappears inside the projection compressor.

---

## 7. Surviving route — proof-carrying local compression

The viable route is now narrower:

1. enumerate or directly detect a polynomial number of structural rewrite templates;
2. require syntactic applicability or a polynomial derivation certificate;
3. apply the first certified rewrite;
4. never ask unrestricted semantic projection-equivalence during selection;
5. prove that this proof-carrying rewrite system is complete enough to keep every projection stage polynomial.

The last item is the real open theorem.

---

## 8. New exact gate — U1-I3 rewrite-system completeness

Freeze a rewrite system `R` with:

- polynomially many templates/rules describable from the current state;
- polynomial syntactic matching or proof-carrying applicability;
- polynomial-size exact replacement;
- polynomial verification;
- polynomial state after each rewrite/projection stage.

Then prove or refute:

> for every polynomial-size frozen-B2 state and every projected root variable, repeated certified rewrites reduce `exists x S` to an equivalent quantifier-free polynomial-size B2 state without semantic oracle calls or exponential rewrite-sequence backtracking.

If such a universal system exists with fixed polynomial total bounds, repeated variable elimination yields `P=NP`.

---

## 9. Current status

`PROJ_TRUE_B2 = coNP_COMPLETE`

`GENERAL_PROJECTION_TARGET_EQUIVALENCE = coNP_COMPLETE`

`SEMANTIC_REPLACEMENT_SELECTION = CLOSED_AS_FREE_OPERATION`

`PROOF_CARRYING_LOCAL_REWRITE_LIBRARY = OPEN`

`UNIVERSAL_REWRITE_COMPLETENESS = OPEN`

`P_VS_NP = OPEN`

---

## 10. New laws

- `SMALL_PROJECTION_TARGET != CHEAP_TARGET_RECOGNITION`
- `POLY_REPLACEMENT_DECK != POLY_EXACT_TARGET_SELECTION`
- `SYNTACTIC_MATCH != SEMANTIC_MATCH`
- `PROOF_CARRYING_MATCH_MAY_AVOID_FREE_EQUIVALENCE_ORACLE`
- `REWRITE_SOUNDNESS != REWRITE_COMPLETENESS`
