# PF5 Orbit-Count × Semantic-Message Product v16.4

Status: **RESTRICTED CONSTRUCTIVE COMPOSITION THEOREM**  
Claim ceiling: **`P_VS_NP = OPEN`**

## Purpose

v16.3 separates two duties that a universal whole-order state must eventually
perform:

1. **orbit/action state** — which interchangeable leaves remain and how many;
2. **semantic message** — what exact cut cost and continuation behavior those
   orbit counts represent.

v16.4 composes the two explicitly.

## Raw-CNF family

The API receives raw CNF only. The admitted family is:

```text
SIGNED_DUPLICATE_FULL_SUPPORT_OR
```

Every clause is an exact duplicate of one full-support disjunction containing
every source variable exactly once, with an arbitrary but fixed sign per
variable. No family tag or sign partition is supplied.

Exact signed clause-incidence signatures discover at most two variable swap
orbits (positive and negative literals), while exact duplicate clauses discover
one clause-copy orbit.

## Product state

Let discovered variable-orbit sizes be `p` and `q` (one may be zero), with `m`
clause copies. A concrete prefix maps to:

```text
Orbit(S) = (i_plus, i_minus, j)
```

where the coordinates count selected leaves in each discovered orbit.

The semantic message is only:

```text
M(S) = (
  LEFT_OR_ACTIVE,
  RIGHT_OR_ACTIVE
)

LEFT_OR_ACTIVE  := (i_plus+i_minus > 0) and (j < m)
RIGHT_OR_ACTIVE := (i_plus+i_minus < p+q) and (j > 0)
```

For a nonempty projected disjunction of fixed signed literals, both satisfied
and unsatisfied outcomes are realizable. Therefore each active side contributes
exactly two precisely-satisfiable signatures and each inactive side contributes
one. Hence:

```text
cost(S)=max(2 if LEFT_OR_ACTIVE else 1,
            2 if RIGHT_OR_ACTIVE else 1)
```

with empty/full Bellman endpoint cost zero.

## Closure

The abstract actions are:

```text
PLUS_VAR   if i_plus<p
MINUS_VAR  if i_minus<q
CLAUSE     if j<m
```

Each increments exactly one orbit coordinate, after which `M` is recomputed in
constant time. A concrete lift picks the least remaining source leaf in the
action orbit.

Thus the combined state is closed under whole-order transitions.

## State bound

The state product is:

```text
Q = (p+1)(q+1)(m+1)
```

(with a missing-sign orbit omitted rather than multiplied by a dummy factor).
For this admitted raw family the input has `Theta((p+q)m)` literal occurrences,
so `Q` is polynomial in explicit source size. v16.4 still records the exact
state product and one fixed `L^2` capability gate rather than relying on this
asymptotic sentence alone.

## General product theorem OM16.4

Suppose a source family has a proof-carrying orbit state `O(S)` and semantic
message `M(S)` such that:

- both state sets have polynomial cardinality/bytes;
- the reachable product states `(O,M)` are polynomially bounded;
- exact current cost is decoded from `(O,M)`;
- every concrete next leaf maps to an abstract action;
- transitions on `(O,M)` are closed and proof-carrying;
- equal product states are future-congruent;
- every selected abstract action has a concrete lift;
- orbit discovery, message discovery, failed search, transition construction,
  Bellman evaluation, proofs, and lift are all globally polynomially charged.

Then exact whole-order bottleneck Bellman on the reachable product quotient is
polynomial.

The theorem is conditional in general; the signed-duplicate-OR family below is
a constructive instance of it.

## Acceptance gate

The implementation must:

1. discover sign-orbits and duplicate-clause orbit from raw CNF;
2. verify variable transpositions clause-by-clause;
3. recognize the signed full-support duplicate-OR cost language with no tag;
4. exhaustively compare product-state cut cost and Bellman to raw exact audits on
   small controls containing both signs;
5. run larger mixed-sign controls entirely symbolically;
6. reject a one-clause sign perturbation and a non-full-support formula as OPEN;
7. charge discovery, quotient transitions, message recomputation and lift;
8. preserve `P_VS_NP = OPEN`.

## Surviving gate

```text
DISCOVER_RICHER_SEMANTIC_MESSAGES_THAT_COMPOSE_WITH_CERTIFIED_ORBITS
```

The next useful advance is not more symmetry by itself, but a message language
that can carry exact cut semantics for non-identical clauses while remaining
closed under orbit-count transitions.

```text
P_VS_NP = OPEN
```
