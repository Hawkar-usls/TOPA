# C025 — Akinator U1-I3: polynomial-size projection replacement does not imply polynomial discovery

Status: **BRUTE_FORCE_COMPRESSION_BLOCK_SEARCH_REFUTED / CONSTRUCTIVE_REWRITE_COMPLETENESS_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-I2 closed unrestricted semantic recognition of a proposed projection target as a free operation. A second naive repair is:

> enumerate all B2 replacement circuits of size at most K=poly(N), verify each proposed equivalence certificate, and stop when one works.

This note closes that brute-force route. Polynomial object size does not make the object space polynomially enumerable.

---

## 1. Exponential block-count lower bound

Assume the current state has at least two root variables `p,q` with distinct IDs.

At every fresh extension step `i`, both definitions

`e_i <-> (p AND q)`

and

`e_i <-> (p AND (NOT q))`

are syntactically legal frozen-B2 definitions.

Therefore a block of `K` fresh extension definitions has at least

`2^K`

distinct syntactic choice sequences, obtained by selecting one of these two legal definitions independently at each step.

Hence any algorithm which guarantees discovery only by exhaustively enumerating all legal B2 blocks of length `K` has worst-case search space at least `2^K`.

For `K=Theta(N)` (or any polynomially growing K), this is not a fixed polynomial in original input length.

---

## 2. Polynomial one-step deck is not enough

U1-B proved that the **one-step** frozen-B2 deck is polynomial under polynomial state size.

But a depth-K schema tree formed by repeatedly choosing among polynomial one-step decks can have exponentially many root-to-depth-K paths.

Thus there is no contradiction:

`POLY_ONE_STEP_DECK`

and

`EXPONENTIAL_K_STEP_SCHEMA_SPACE`

can hold simultaneously.

This is the same structural distinction as branching mass: local branching factor can be small while total tree mass is exponential.

---

## 3. Verification does not repair discovery

Suppose a candidate replacement block `R` comes with a polynomially checkable proof certificate that

`R(y) <-> exists x C(x,y)`.

Even then, brute-force enumeration of all possible `(R, certificate)` or all possible R blocks can be exponential before the successful object is reached.

So:

**CHEAP_VERIFICATION != CHEAP_DISCOVERY.**

The certificate helps only once a candidate has been constructed.

---

## 4. Surviving discovery architectures

A universal polynomial projection compressor must avoid exhaustive K-block search. Two scientifically admissible architectures remain:

### A. Direct constructive grammar

From the current local/canonical structure, deterministically generate the whole replacement/proof block in polynomial time, as Cook/PHP and Inner-Product algebraic projection do on their respective families.

### B. Certified single-step descent

Use the already-polynomial one-step B2 deck and a cheap exact proof-carrying progress criterion so that one accepted move is found by polynomial scan, with a polynomial-range global potential preventing exponential sequences/backtracking.

A mixture of A and B is also admissible if every cost is charged.

---

## 5. New exact gate — U1-J constructive projection grammar

The next positive target is now precise:

Construct a deterministic grammar/algorithm which maps

`(current B2 state S, projected root variable x)`

to a polynomial-size exact projection replacement and proof without searching an exponential block space.

It must provide:

1. direct polynomial construction or polynomially many certified one-step moves;
2. exact projection equivalence;
3. polynomial total state and proof bytes in original N;
4. no unrestricted semantic target recognition;
5. no exhaustive compression-block enumeration;
6. polynomial verification;
7. universal applicability to every CNF/B2 state or a proved complete decomposition into handled cases.

If this universal grammar exists with fixed polynomial bounds, repeated elimination yields `P=NP`.

---

## 6. Current status

`POLY_SIZE_REPLACEMENT != POLY_ENUMERABLE_REPLACEMENT_SPACE`

`BRUTE_FORCE_POLY_SIZE_B2_BLOCK_SEARCH = EXPONENTIAL_IN_GROWING_K`

`DIRECT_CONSTRUCTIVE_PROJECTION_GRAMMAR = OPEN`

`CERTIFIED_SINGLE_STEP_DESCENT = OPEN`

`P_VS_NP = OPEN`

---

## 7. New laws

- `POLY_OBJECT_SIZE != POLY_OBJECT_DISCOVERY`
- `POLY_ONE_STEP_DECK != POLY_K_STEP_SCHEMA_TREE`
- `CHEAP_PROOF_VERIFICATION != CHEAP_COMPRESSION_DISCOVERY`
- `UNIVERSAL_COMPRESSOR_MUST_BE_CONSTRUCTIVE_OR_DESCENT_GUIDED`
