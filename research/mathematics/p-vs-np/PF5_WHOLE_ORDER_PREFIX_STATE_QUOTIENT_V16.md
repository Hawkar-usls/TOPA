# PF5 Whole-Order Prefix-State Quotient v16

Status: **THEOREM CONTRACT + FINITE AUDIT ONLY**  
Claim ceiling: **`P_VS_NP = OPEN`**

## Why this gate exists

PF5 v15.1 produced the first clean `PURE_GREEDY_FUTURE_OBSTRUCTION` in the Slime line.
On the already-observed connected 3-CNF seed `911000`, the frozen v5 order has caterpillar PS-width `5` while an exact order has width `4`. Yet along the entire v5 path:

- every chosen next leaf has minimum **exact immediate** PS cut value among the available leaves;
- there is no v5 `OPEN_FEEDBACK_BUDGET` on the chosen path;
- no one-step v5-cap tie hides a smaller immediate exact PS value.

Therefore the remaining problem is not merely to estimate the next cut more accurately. The objective is inherently whole-order:

```text
OPT(F) = min_order pi  max_prefix S of pi  PS_F(S)
```

For `n` incidence leaves, the direct exact state graph is the `2^n` subset lattice.

## Exact exponential Bellman object

Let `L` be the leaf set and let `c(S)` be the exact PS cut value of prefix subset `S`.
The caterpillar leaf-edge contribution is the order-independent constant

```text
C_leaf = max_{a in L} c({a}).
```

Define the future bottleneck value:

```text
V(L) = 0
V(S) = min_{a in L-S} max(c(S union {a}), V(S union {a}))
```

where `c(L)=0` at the terminal. Then

```text
OPT(F) = max(C_leaf, V(empty)).
```

Computing `V` on raw subsets is exponential. v16 uses it only as an audit oracle on the already-open seed `911000`.

## Candidate universal object: proof-carrying prefix quotient

A candidate representation is a map

```text
Sigma_F : 2^L -> Q_F
```

with an abstract action system. It is admitted for whole-order bottleneck DP only if all of the following are replayably certified.

### Q1. Rank / terminal preservation

`Sigma(S)` determines `|S|` (or an equivalent strictly increasing rank) and whether `S=L`. Quotient transitions therefore form a DAG.

### Q2. Exact cost preservation

There is a polynomial-time proof-carrying decoder

```text
cost(Sigma(S)) = c(S).
```

A heuristic upper bound is not sufficient for this exact whole-order theorem.

### Q3. Abstract action coverage

For every concrete remaining leaf `a notin S`, a polynomial-time map emits an abstract action class

```text
alpha = Act(Sigma(S), S, a).
```

Every concrete action is covered and every admitted abstract action has a concrete lift.

### Q4. Transition closure

There is a polynomial-time proof-carrying transition

```text
Delta(Sigma(S), alpha) = Sigma(S union {a})
```

for every concrete `a` represented by `alpha`, without decompressing to an exponential truth table or subset family.

### Q5. Future congruence / bisimulation

If

```text
Sigma(S) = Sigma(T),
```

then the two states have the same exact cost, terminal/rank status, and the same abstract successor-class structure. In particular, every abstract action available at one state has a matching action at the other leading to the same quotient successor, and conversely.

This is the whole-order analogue of the C035 rule: equal independently replayed canonical residual messages may merge only when their represented continuation behavior is identical. Semantic similarity without a certificate never authorizes a merge.

### Q6. Order lift

For every selected quotient transition, a proof record reconstructs one concrete remaining leaf. Recursing over the selected quotient path reconstructs a full concrete leaf order whose measured bottleneck equals the quotient DP value.

### Q7. Polynomial discovery and global accounting

For explicit source size `N`, one fixed universal polynomial must bound:

- construction/discovery work for `Sigma`, action classes, and transitions;
- number of reachable quotient states `|Q_F|`;
- number of abstract transitions;
- state/proof/certificate bytes;
- failed recognizer / failed merge work;
- Bellman evaluation work;
- concrete order-lift work;
- cumulative intermediate bytes.

No SAT oracle, formula-equivalence oracle, exact-width oracle, hidden truth table, or exponential precomputation may be free.

## Conditional theorem Q16

If Q1-Q7 hold for every CNF family with

```text
|Q_F| <= poly(N)
```

and polynomially many abstract outgoing actions per quotient state, then the exact caterpillar PS-width bottleneck objective is computable by dynamic programming on the quotient in polynomial total work:

```text
V_Q(q_terminal) = 0
V_Q(q) = min_alpha max(cost(Delta(q,alpha)), V_Q(Delta(q,alpha))).
```

Because rank strictly increases, quotient evaluation is a DAG computation. Q5 makes the Bellman value independent of the concrete representative, and Q6 lifts the selected quotient path to a concrete order.

This is a **conditional composition theorem**, not a proof that such a universal quotient exists.

## Why weak state labels are not enough

Labels such as

```text
(depth, current_cut)
(depth, current_cut, exact_future_value)
```

may merge raw subsets that have different successor structures. Even if the scalar Bellman value happens to agree, such a merge is not an admitted proof-carrying congruence unless the transition system also replays.

v16 therefore measures three different objects on seed `911000`:

1. raw subset states;
2. weak scalar label classes, only as compression hints;
3. an **audit-only exact future-bisimulation partition** built bottom-up from exact cut values and successor class multisets.

The third object is safe for the finite audited bottleneck graph, but its construction enumerates the full subset lattice and exact PS cuts. It is not a polynomial candidate representation.

## Donor alignment

- **C035 / PR #43**: proof-carrying interface congruence — equal canonical residual state implies equal admitted continuation behavior; under-merging is allowed, unproved semantic merging is not.
- **C047 / PR #71**: exact bounded-width trellis DP in a restricted affine language, with replayable transitions and witness lift.
- **C048 / PR #72**: frozen polynomial candidate portfolio and charged layout selection.
- **C048.1 / PR #73**: constructive FPT layout discovery bridge for fixed finite-field subspace width; fixed width is tractable, unbounded width is not promoted to a universal polynomial theorem.

These are donors for the form of Q1-Q7, not evidence that arbitrary CNF already has a polynomial quotient.

## Surviving gate

```text
POLYNOMIAL_PROOF_CARRYING_PREFIX_BISIMULATION_DISCOVERY
OR
A_STRONGER_SYMBOLIC_WHOLE_ORDER_STATE_LANGUAGE
```

The target is no longer another one-step Slime score. It is a compact state algebra closed under **future order transitions**.

```text
P_VS_NP = OPEN
```
