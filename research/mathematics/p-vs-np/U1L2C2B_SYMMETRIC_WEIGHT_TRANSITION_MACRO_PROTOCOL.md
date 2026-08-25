# U1-L2C2B — proof-carrying symmetric-weight transition macro

Status: **FROZEN_PROTOCOL_BEFORE_PROVIDER**
Claim ceiling: **P_VS_NP = OPEN**

## Exact nonliteral factor language

For `m>=0` and allowed Hamming-weight set `A subseteq {0,...,m}`, define

`g_{m,A}(x_1,...,x_m)=1 iff sum_i x_i in A`.

The proof-carrying macro-state is `(m,A)` with exact bitset/set encoding of `A`.

This quotients the `2^m` assignment presentations into at most `m+1` exact Hamming-weight states for this symmetric factor class.

## Exact existential update theorem

For any selected variable `x_m`, write the remaining Hamming weight as `t`.

`exists x_m g_{m,A}(Y,x_m)=1`

iff

`t in A OR t+1 in A`.

Therefore the projected state is

`(m-1,A')`, where

`A'={t in {0,...,m-1}: t in A or t+1 in A}`.

This update is deterministic, exact, and `O(m)` on an explicit bitset/set.

## Witness lift

Given a remaining assignment of weight `t` satisfying `A'`:

- choose eliminated bit `x=0` if `t in A`;
- otherwise choose `x=1`, which is valid because then `t+1 in A`.

## Sequential closure and cost

Repeated projection remains in the same `(m,A)` language.

With a straightforward explicit bitset implementation:

- state size: `O(m)` bits/entries;
- one projection: `O(m)` inspections;
- all `m` projections: `O(m^2)` conservative total work;
- witness stack: `O(m)` bits plus replay metadata.

## Ramanujan-theta fixture

Use

`E(n)=n(3n-1)/2`

and define

`A_theta(m)={E(n): 0<=E(n)<=m}`.

Frozen `m` values: `[8,16,32,64,128,256]`.

The initial spectrum must be generated using the exact recurrence donor from C2A, not by floating point.

For each `m`, the provider must:

1. build `A_theta(m)` exactly;
2. project sequentially to `m=0` using only the symmetric-weight theorem;
3. replay a satisfying witness whenever terminal state is TRUE;
4. record state sizes, inspections, certificate bytes and hashes;
5. test after the **first** projection whether the resulting `A'` is still exactly equal to `A_theta(m-1)`.

No assumption is made that theta parameterization is closed.

## Interpretation guard

If theta closure fails but symmetric-weight closure passes, the correct conclusion is:

- theta is an exact compact/structured initial donor;
- the larger symmetric transition language is the actual closed SAT-side representation;
- theta alone is not a sequentially closed SAT representation.

## Controls

- `A=empty` must terminate FALSE.
- `A={0,...,m}` must stay TRUE under projection.
- singleton exact-weight state must update exactly.
- malformed allowed weight outside `[0,m]` must REFUSE.

## Forbidden inference

This restricted theorem does not imply arbitrary CNF is symmetric, does not give a polynomial morphism from arbitrary CNF to `(m,A)`, and does not imply P=NP.

## Next gate

If the theorem/provider passes, the universal debt moves to:

`U1-L2C2C_DISCOVER_PROOF_CARRYING_SYMMETRY_OR_OTHER_POLY_TRANSITION_QUOTIENT_FROM_ARBITRARY_FACTOR`

The missing object is a deterministic polynomial SAT-side morphism/partition that exposes a polynomial number of exact transition states for arbitrary nonliteral factors.
