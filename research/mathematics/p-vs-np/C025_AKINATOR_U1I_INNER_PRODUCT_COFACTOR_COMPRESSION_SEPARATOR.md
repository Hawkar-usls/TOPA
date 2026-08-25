# C025 — Akinator U1-I1: Inner Product separates cofactor explosion from compact exact projection

Status: **COFACTOR_ENUMERATION_ROUTE_REFUTED / FAMILY_SPECIFIC_SMART_PROJECTION_POSITIVE_CONTROL**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-H showed that naive quantifier-free Shannon projection can double state at each eliminated variable. The next obvious repair is to cache distinct residual cofactors and share identical ones.

This note closes that repair as a universal projection strategy: one polynomial-size B2 function can have exponentially many distinct cofactors under a block of variables, while its complete existential projection over that block has a linear-size B2 representation.

The same family also supplies a positive control: a simple algebraic projection rule compresses each elimination stage without enumerating all cofactors.

Thus:

**MANY_DISTINCT_COFATORS != LARGE_PROJECTED_FUNCTION**

and

**COFACTOR_ENUMERATION != PROJECTION_COMPRESSION**.

---

## 1. Inner-product family

For `k>=1`, define

`IP_k(x,y) := XOR_{i=1}^k (x_i AND y_i)`

with root blocks

`x=(x_1,...,x_k)` and `y=(y_1,...,y_k)`.

Frozen B2 can compute each product `x_i AND y_i` with one gate and XOR can be implemented with constant AND/NOT overhead, so `IP_k` has `O(k)` B2 size.

---

## 2. Theorem A — all 2^k x-cofactors are distinct

Fix an assignment `a in {0,1}^k` to the x-block.

Then

`IP_k(a,y) = XOR_{i:a_i=1} y_i`.

So each x-assignment selects the parity of exactly the subset

`S_a = {i : a_i=1}`.

If `a != a'`, choose an index `j` in the symmetric difference of `S_a,S_a'` and set `y_j=1`, all other y-bits 0. Then the two parity functions differ.

Therefore the map

`a -> IP_k(a,.)`

is injective, and there are exactly

`2^k`

distinct x-cofactors.

Hence any projection implementation which first materializes one representative for every distinct full x-block cofactor before performing global compression has exponential intermediate representation on this linear-size family.

This is an algorithm/interface lower bound, not a lower bound on the minimum projected circuit.

---

## 3. Theorem B — the complete existential projection is only OR_k

For a fixed y-assignment:

- if `y=0^k`, then every product `x_i y_i=0`, so `IP_k(x,y)=0` for all x;
- if some `y_j=1`, choose x with `x_j=1` and all other x_i=0. Then `IP_k(x,y)=1`.

Therefore

`exists x_1...x_k IP_k(x,y) = y_1 OR ... OR y_k`.

The projected function has a linear-size B2 representation using De Morgan OR composition.

Thus:

`2^k DISTINCT COFACTORS`

coexist with

`O(k) PROJECTED B2 SIZE`.

So counting or materializing all distinct cofactors is not a sound proxy for minimum exact projection size.

---

## 4. Theorem C — one-variable algebraic projection stays compact

Write

`IP_k = (x_i AND y_i) XOR R`,

where `R` is independent of `x_i`.

For fixed `(y_i,R)`:

- if `y_i=0`, varying `x_i` has no effect and existential projection returns `R`;
- if `y_i=1`, choose `x_i` to make the XOR output 1, so projection returns TRUE.

Hence

`exists x_i [(x_i AND y_i) XOR R] = y_i OR R`.

After projecting `x_1,...,x_j`, the residual has the compact form

`(y_1 OR ... OR y_j) OR XOR_{i=j+1}^k (x_i AND y_i)`

with only `O(k)` Boolean structure under straightforward shared implementation.

Therefore there is a deterministic family-specific exact projection algorithm with:

- one root variable eliminated per stage;
- no exponential cofactor materialization;
- polynomial state;
- polynomial construction;
- exactness proved by the local identity above.

This is a genuine positive control for proof-carrying projection compression.

---

## 5. What this kills

The following universal strategy is closed:

> enumerate/cache all semantically distinct Shannon cofactors, then compress them.

On `IP_k`, the cache can contain `2^k` distinct functions even though the correct projected result is only `OR_k`.

Likewise, a cache keyed by exact residual truth function is not saved by deduplication: the cofactors are genuinely semantically distinct.

This sharpens the earlier D6 law

`EXPONENTIALLY_MANY_RESIDUAL_SEMANTIC_CLASSES != EXPONENTIALLY_MANY_EXTENSIONS`

into the projection setting:

`EXPONENTIALLY_MANY_COFATORS != EXPONENTIAL_PROJECTED_FUNCTION_SIZE`.

---

## 6. What this does not kill

This note does not prove:

- a universal smart compressor exists;
- minimum B2 projection size is always polynomial;
- semantic simplification can be discovered cheaply for arbitrary circuits;
- the Galil hard family has compact B2 projections;
- P=NP.

It only proves that naive cofactor enumeration can be exponentially wasteful and that algebraic structure can sometimes give dramatic exact compression.

---

## 7. New exact gate — U1-I2 local algebraic projection certificates

The next admissible question is whether the successful IP identity can be generalized into a polynomially enumerable library of **locally certified projection rewrites**.

A rewrite template should have the form

`exists x Pattern(x,z)  <->  Replacement(z)`

with:

1. constant/poly-size proof of the identity;
2. polynomial-time syntactic matching against the current B2 DAG;
3. polynomial-size replacement;
4. no semantic equivalence oracle;
5. proof-carrying update;
6. a theorem that repeated application is complete enough to prevent exponential projection state on every CNF.

Items 1–5 are local engineering/theorem obligations. Item 6 is the universal completeness burden and remains OPEN.

Positive templates already visible:

- pure unused variable: `exists x R = R` when x not in support;
- literal branch: `exists x (x AND A) = A`;
- XOR-toggle template from Inner Product: `exists x ((x AND y) XOR R) = y OR R` when R is x-independent;
- Horn/Krom/affine family-specific eliminations where polynomial closure is known in the restricted family.

The next kill test is to ask whether a finite/poly-size local rewrite library can cover arbitrary polynomial B2 states without either missing hard cases or hiding semantic recognition complexity.

---

## 8. Current status

`ALL_X_COFATORS_OF_IP_K = 2^k DISTINCT`

`EXISTS_X_IP_K = OR_K = O(k) B2`

`IP_FAMILY_SMART_PROJECTION = POLYNOMIAL POSITIVE CONTROL`

`COFACTOR_ENUMERATION_AS_UNIVERSAL_COMPRESSION = REFUTED`

`LOCAL_ALGEBRAIC_PROJECTION_LIBRARY_COMPLETENESS = OPEN`

`UNIVERSAL_B2_PROJECTION_COMPRESSION = OPEN`

`P_VS_NP = OPEN`

---

## 9. New laws

- `MANY_DISTINCT_COFATORS != LARGE_PROJECTED_FUNCTION`
- `COFACTOR_ENUMERATION != PROJECTION_COMPRESSION`
- `SEMANTIC_DEDUPLICATION_DOES_NOT_SAVE_IP_COFACTOR_CACHE`
- `ALGEBRAIC_STRUCTURE_CAN_COMPRESS_EXACT_PROJECTION_WITHOUT_ENUMERATING_COFATORS`
- `FAMILY_SPECIFIC_SMART_PROJECTION != UNIVERSAL_PROJECTION_ALGORITHM`
