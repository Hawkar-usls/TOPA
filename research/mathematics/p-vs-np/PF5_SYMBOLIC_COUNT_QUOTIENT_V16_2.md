# PF5 Symbolic Count Quotient v16.2

Status: **RESTRICTED CONSTRUCTIVE THEOREM**  
Claim ceiling: **`P_VS_NP = OPEN`**

## Family

Let

```text
D(n,m) = AND_{j=1..m} (x_1 OR ... OR x_n)
```

with `n,m >= 1`. The incidence graph is `K_{n,m}` and therefore can have large
structural treewidth, while C032 already proves the precisely-satisfiable cut
signature count is at most two.

The whole-order prefix leaves are the `n` variable leaves and `m` clause-copy
leaves.

## Exact symbolic state

For a concrete prefix `S`, define

```text
Sigma(S) = (i,j)
i = number of selected variable leaves
j = number of selected clause leaves.
```

All variables are interchangeable and all clause copies are identical. Hence
any two concrete prefixes with the same `(i,j)` are related by an automorphism
of the source incidence structure and have identical future action types.

The quotient has exactly

```text
(n+1)(m+1)
```

states rather than `2^(n+m)` raw prefixes.

## Exact cut decoder

For a cut `(i,j)`:

- the left projected side has two signatures iff `i>0` and `m-j>0`; otherwise one;
- the right projected side has two signatures iff `n-i>0` and `j>0`; otherwise one.

Therefore, away from the Bellman endpoints,

```text
left(i,j)  = 2 if i>0   and j<m else 1
right(i,j) = 2 if i<n   and j>0 else 1
cut(i,j)   = max(left,right).
```

The whole-order Bellman convention sets the empty and full prefix state costs to
zero; singleton leaf-edge cuts are charged separately exactly as in v16.

## Abstract actions and closure

At `(i,j)` there are at most two action classes:

```text
VAR    if i<n      -> (i+1,j)
CLAUSE if j<m      -> (i,j+1)
```

Every concrete remaining variable is a lift of `VAR`; every concrete remaining
clause copy is a lift of `CLAUSE`. A deterministic concrete lift chooses the
least-index remaining leaf of the selected type.

Thus rank, exact cost, action coverage, transition closure, future congruence and
concrete order lift are all explicit and replayable.

## Exact quotient Bellman

```text
V(n,m)=0
V(i,j)=min(
  max(c(i+1,j), V(i+1,j)) if i<n,
  max(c(i,j+1), V(i,j+1)) if j<m
)
```

The quotient is a DAG ordered by `i+j`, so evaluation costs `O(nm)` states and
at most two transitions per state. The singleton leaf-edge contribution is then
joined exactly as in v16.

For `n,m >= 1`, the optimum is `2` except degenerate one-leaf endpoint details
handled directly by the implementation.

## Why this matters

This is a real polynomial whole-order `Sigma(prefix)` on a family whose raw
incidence treewidth grows as `min(n,m)`. It demonstrates that the v16 quotient
requirements are constructive and that large raw structural width does not by
itself block compact future-state representations.

It does **not** show that arbitrary CNF has such a count quotient. The symmetry
of identical variables/clauses is doing essential work.

## Acceptance gate

The implementation must:

1. exhaustively compare the `(i,j)` cut decoder against the independent exact
   PS-cut oracle for all small `D(n,m)` controls;
2. compare symbolic Bellman against raw subset Bellman on small controls;
3. verify concrete order lift;
4. run large symbolic-only controls without raw subset enumeration;
5. charge quotient states/transitions/decoder checks/lift work;
6. preserve `P_VS_NP = OPEN`.

## Surviving gate

```text
DISCOVER_PROOF_CARRYING_PREFIX_ORBITS_OR_STRONGER_MESSAGES_WITHOUT_SUPPLIED_SYMMETRY
```

The universal problem is to find similarly compact future-congruence classes
for arbitrary CNF with polynomial discovery cost, not merely for a known
permutation-symmetric family.

```text
P_VS_NP = OPEN
```
