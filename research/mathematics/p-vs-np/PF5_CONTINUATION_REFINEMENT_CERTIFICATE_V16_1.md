# PF5 Continuation Refinement Certificate v16.1

Status: **CONDITIONAL THEOREM + EXPONENTIAL FINITE AUDIT**  
Claim ceiling: **`P_VS_NP = OPEN`**

## Input from v16

On the already-open seed `911000`, one-step exact minimization is insufficient:
Slime v5 has width `5`, while exact whole-order Bellman gives width `4`, even
though every Slime choice is an exact immediate-PS minimum.

v16 also established that weak scalar labels are unsafe congruences. The target
must preserve the transition structure of future order choices.

## Refinement object

Let the raw prefix DAG have states `S subseteq L`, exact state cost `c(S)`, and
one transition `S -> S union {a}` for each remaining leaf `a`.

Start from any proof-carrying coarse partition that at least preserves:

```text
rank(S) = |S|
current_cost(S) = c(S)
terminal(S)
```

A block may be split only by a **continuation refinement certificate**.
For a current partition `P`, define

```text
Succ_P(S) = sorted multiset of P-block IDs reached by all concrete next leaves.
```

If two states in one block have different `Succ_P` multisets, they are not
future-congruent under `P` and the block must split.

A split certificate contains:

- the old block identifier and its committed member/block digest;
- two representatives `S,T` from that block;
- their independently replayed exact rank/current-cost records;
- the two successor-block multisets;
- one block-count discrepancy witnessing inequality;
- concrete leaf lifts reaching the discrepant successor blocks when available;
- the prior-partition digest and next-partition digest.

No SAT oracle or semantic-equivalence oracle authorizes a split or merge.

## Monotone refinement theorem R16.1

Repeatedly replace each block by classes with equal tuple

```text
(old_block_id, Succ_P(S)).
```

Equivalently, since the initial partition already preserves rank and cost, use

```text
(rank(S), c(S), Succ_P(S)).
```

with monotonicity against the prior partition.

Then:

1. refinement never merges states separated by an earlier certified distinction;
2. the process terminates after at most the number of raw states minus the
   initial class count splits;
3. at a fixed point, states in one block have identical rank, current cost, and
   successor-block multiset;
4. therefore Bellman bottleneck value is constant on each fixed-point block;
5. quotient Bellman plus representative-specific concrete action lifts yields a
   concrete order with the quotient bottleneck.

On a finite explicit prefix DAG this is a sound exact construction.

## Why this is not yet polynomial

The explicit algorithm may require:

```text
2^|L| raw states,
Theta(|L| 2^|L|) transition references,
and exponentially many split certificates.
```

So the raw-state refinement is an **audit oracle only**.

## Conditional polynomial bridge

A family admits a polynomial whole-order solver through this route if there is a
proof-carrying symbolic refinement implementation satisfying one fixed universal
polynomial bound on all of:

- initial symbolic blocks;
- number of reachable refined blocks;
- symbolic block bytes;
- successor-class construction;
- separating-continuation discovery;
- failed separator searches;
- split certificates;
- refinement rounds;
- abstract transitions;
- quotient Bellman work;
- concrete action/order lift;
- cumulative intermediate bytes.

If all these are polynomial and the fixed point is a true future congruence,
then exact whole-order bottleneck DP is polynomial on that family.

This is a conditional theorem. It does **not** establish a universal polynomial
symbolic partition for arbitrary CNF.

## Relation to older JANUS work

This is the whole-order counterpart of C036 proof-carrying partition refinement:
coarse states are refined only by explicit separating continuations, never by an
uncertified semantic guess. C035 supplies the congruence discipline; C047/C048
supply restricted examples where compact transition states and layout DP are
constructive.

## v16.1 finite acceptance gate

On seed `911000` the exponential audit must:

1. start from `(depth,current exact cut)` classes;
2. refine synchronously by successor-block multisets;
3. preserve monotonic refinement at every round;
4. stabilize;
5. produce replayable split witnesses;
6. yield exactly the same partition as v16's bottom-up audit
   future-bisimulation, modulo class IDs;
7. reproduce Bellman optimum `4` and lift one concrete width-`4` order;
8. explicitly mark raw-state enumeration and split discovery as exponential.

No favorable compression ratio is required for PASS.

## Surviving gate

```text
SYMBOLIC_CONTINUATION_REFINEMENT_WITH_POLYNOMIAL_BLOCK_AND_SPLIT_BOUNDS
```

or a stronger symbolic whole-order state language that satisfies the same
future-congruence and lift requirements without explicit refinement.

```text
P_VS_NP = OPEN
```
