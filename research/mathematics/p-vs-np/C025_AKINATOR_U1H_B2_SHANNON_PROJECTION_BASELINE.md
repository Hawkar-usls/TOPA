# C025 — Akinator U1-H: exact B2 Shannon projection baseline and the compression gate

Status: **NAIVE_QUANTIFIER_FREE_SHANNON_ROUTE_EXPONENTIAL_BY_CONSTRUCTION / SMART_B2_PROJECTION_COMPRESSION_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Context

U1-G showed that Davis–Putnam has perfect universal variable-count descent but can generate exponentially many clauses. The natural repair is to keep the residual obligation as a general B2 circuit rather than materializing all CNF resolvents.

Exact variable projection is trivial semantically:

`exists x C(x,y) = C(0,y) OR C(1,y)`.

This note isolates what is and is not gained by the naive B2 implementation.

---

## 1. One-step exact B2 projection

Let `C` be a B2 circuit/DAG with output literal `o` and size `S` extension gates.

Construct two restricted copies:

- `C_0 := C[x=0]`;
- `C_1 := C[x=1]`.

Constant propagation and hash-consing may be applied if justified, but the naive baseline does not rely on any semantic equivalence merging.

Let their output literals be `o_0,o_1`.

Create one fresh B2 gate

`u <-> ((NOT o_0) AND (NOT o_1))`.

Use signed literal `NOT u` as the new output.

Then

`NOT u = o_0 OR o_1 = exists x C`.

Thus one root variable is eliminated exactly and no semantic oracle is required.

---

## 2. Naive size recurrence

Without cross-copy sharing, each restricted copy contains at most `S` copied gates and the OR gadget adds one gate:

`S' <= 2S + 1`.

If the baseline deliberately copies both sides at every elimination regardless of possible sharing, define

`S_{k+1} = 2 S_k + 1`.

Then exactly

`S_k = 2^k (S_0 + 1) - 1`.

Therefore after a linear number of eliminated variables the naive quantifier-free Shannon constructor is exponential **by construction**.

This is an algorithm-specific route closure, not a lower bound on the minimum B2 circuit size of the projected function.

---

## 3. Perfect descent still holds

As in Davis–Putnam, define

`mu = number of unprojected root variables`.

Each Shannon projection eliminates one variable and decreases `mu` by one. Exact SAT preservation is immediate from existential quantification.

So this baseline again satisfies:

- universal stage availability;
- exactness;
- deterministic construction;
- strict linear-range descent;
- exact terminal semantics.

Yet its explicit state can grow as `2^k`.

This reinforces:

**PERFECT_DESCENT != POLY_STATE.**

---

## 4. Why a quantifier marker is not a compression theorem

One can avoid copying by storing a symbolic object

`exists x C(x,y)`

as a constant-size wrapper around `C`.

After eliminating all variables this yields

`exists x_1 ... exists x_n C(x_1,...,x_n)`,

which is exactly the original SAT question.

Unless the representation provides a polynomial-time exact procedure for evaluating/normalizing these existential wrappers, the hard work has merely moved into the wrapper semantics.

Thus:

`SMALL_QUANTIFIER_ANNOTATION != QUANTIFIER_FREE_POLY_COMPRESSION`.

---

## 5. What sharing can legitimately do

A smarter constructor may reduce the naive factor of two by:

- reusing gates unaffected by `x`;
- syntactic hash-consing of identical restricted subgraphs;
- constant propagation;
- proof-carrying equivalence/implication rewrites;
- family-specific algebraic reductions.

All are allowed if their discovery and verification costs are charged.

But arbitrary semantic merging of `C_0` and `C_1` subcircuits cannot be assumed free: exact B2 circuit equivalence is coNP-complete in the general scope (U1-E/D1 barrier).

Hence the open problem is precisely **proof-carrying compression**, not semantic wishful sharing.

---

## 6. Conditional closure theorem

Suppose there exists a deterministic projection operator `PROJECT_B2` such that for every polynomial-size current state and chosen remaining root variable `x` it outputs a quantifier-free B2 state exactly equivalent to `exists x S`, and across a full elimination run:

1. every output state has at most `N^c` bits for one fixed universal `c`;
2. total projection construction/proof work is at most `N^d` for fixed universal `d`;
3. each step carries a polynomially verifiable correctness certificate;
4. no hidden SAT/#SAT/equivalence oracle or exponential alternative-compression search is used.

Then eliminate every root variable, evaluate the final zero-variable state, and decide SAT in deterministic polynomial time.

Therefore:

`UNIVERSAL_POLY_EXACT_B2_PROJECTION_COMPRESSION => SAT in P => P=NP`.

This is conditional and does not establish that such an operator exists.

---

## 7. New exact gate — U1-I proof-carrying projection compression

The next research object is no longer “find a good macro” in the abstract.

It is an exact compressor for one existential projection stage:

`(B2 state S, root variable x) -> (smaller-root B2 state S', projection certificate)`

with:

- exact equivalence `S' <-> exists x S`;
- universal polynomial serialized state;
- polynomial construction and verification;
- proof-carrying sharing only;
- no semantic oracle;
- no exponential backtracking over possible compressions;
- compatibility with the global variable-count descent rank.

Adversarial tests:

- Galil Davis–Putnam hard family;
- expander graph formulas / high induced width;
- selector-lift;
- parity/inner-product reuse;
- F3D collapse;
- HWB and structured knowledge-compilation size barriers;
- p-reencoding wrappers.

Positive controls:

- Horn/Krom/affine families;
- bounded-treewidth formulas;
- Cook/PHP extension schema;
- families where `x` occurs only locally and restricted copies share most gates.

---

## 8. Current status

`NAIVE_B2_SHANNON_PROJECTION = EXACT_BUT_EXPONENTIAL_BY_CONSTRUCTION`

`QUANTIFIER_WRAPPER = COMPACT_BUT_DOES_NOT_SOLVE_EVALUATION`

`PROOF_CARRYING_B2_PROJECTION_COMPRESSION = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 9. New laws

- `EXACT_SHANNON_PROJECTION != POLY_COMPRESSION`
- `SMALL_QUANTIFIER_WRAPPER != CHEAP_QUANTIFIER_ELIMINATION`
- `SYNTACTIC_SHARING != SEMANTIC_EQUIVALENCE_ORACLE`
- `NAIVE_B2_PROJECTION_CAN_RETAIN_THE_FULL_EXPONENT`
- `UNIVERSAL_POLY_EXACT_PROJECTION_COMPRESSION_WOULD_CLOSE_P_EQUALS_NP`
