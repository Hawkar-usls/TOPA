# C025-E2R-F3-D — Self-Reduction Constructor Cost Firewall

**Frozen:** 2026-08-24  
**Status:** `SOURCE_CONSTRUCTION_IDENTIFIED__ALGORITHMIC_COST_NOT_TRANSFERRED`  
**Global ceiling:** `P_VS_NP = OPEN`.

## 1. Source fact

Sokolov's CCC 2022 self-reduction is a mathematical restriction construction. In Algorithm 1 it repeatedly:

1. chooses an active output vertex uniformly;
2. chooses an `x`-assignment from a residual base-function preimage;
3. defines a set `B_i` by a maximum-cardinality condition over subsets of the remaining left vertices subject to a boundary constraint;
4. chooses an assignment `nu_i` on the neighbourhood of `B_i` satisfying the corresponding constraints.

The paper proves that the resulting restriction is a self-reduction under the stated expander/balanced-function hypotheses. It does **not** by this statement give JANUS a deterministic polynomial-time routine for computing every one of those choices in the representation used by Policy-0B.

Primary source:
Dmitry Sokolov, *Pseudorandom Generators, Resolution and Heavy Width*, CCC 2022, DOI `10.4230/LIPIcs.CCC.2022.15`, Definition 20 / Algorithm 1 / Lemma 22.

## 2. Hidden-cost warning

The following transfer is forbidden:

```text
SOURCE_PROVES_SELF_REDUCTION_EXISTS_OR_IS_GENERATED_IN_PROOF_ARGUMENT
=>
POLICY0B_CAN_COMPUTE_THE_RESTRICTION_IN_POLY(N)
```

without a separate algorithmic theorem.

In particular, the project must charge:

```text
COST_FIND_B_i
COST_FIND_OR_SAMPLE_SIGMA_i
COST_FIND_NU_i
COST_VERIFY_BOUNDARY_AND_EXPANSION_CONDITIONS
COST_REPRESENT_RESIDUAL_FUNCTIONS
```

relative to the explicit encoded input length and the exact function/graph representation.

No hardness claim is made here. The cost is **unproved**, not proved exponential.

## 3. Closure-selection distinction

The paper defines a closure as an arbitrary but fixed maximum-size contained set. This is enough for the combinatorial proof because maximal-cardinality existence is the object required by the argument.

For a deterministic solver or executable restriction sampler, however, an actual selection procedure must be frozen. If JANUS uses:

```text
LEXICOGRAPHIC_MAXIMUM
GREEDY_APPROXIMATION
SAT/ILP_SUBROUTINE
BRUTE_FORCE
ORACLE
```

then that is a new algorithmic object. Its correctness relative to the source property and its full runtime/representation cost must be proved separately.

## 4. Random choice is not a heuristic, but must be specified

A probability distribution over restrictions is scientifically admissible when the distribution is explicit. It is not an uncalibrated confidence score.

However, if some source step says only "pick a satisfying assignment" rather than defining a unique distribution, JANUS must not silently invent a sampling rule and call it the source distribution.

For F3-D we therefore split:

```text
D2A_SOURCE_SELF_REDUCTION_RELATION
D2B_EXECUTABLE_DETERMINISTIC_OR_RANDOM_SELECTOR
D2C_SELECTOR_COST_IN_ORIGINAL_INPUT_N
D2D_SURVIVAL_THEOREM_UNDER_THE_EXACT_SELECTED_DISTRIBUTION_OR_RELATION
```

## 5. Interaction with the hidden exponent

Even if restriction survival is mathematically favourable, an implementation could hide superpolynomial work in the constructor used to find the restriction. Conversely, a slow constructor in the lower-bound proof says nothing by itself about the complexity of SAT.

Therefore:

```text
GOOD_RESTRICTION_EXISTS != CHEAP_RESTRICTION_DISCOVERY
CHEAP_RESTRICTION_CHECK != CHEAP_RESTRICTION_CONSTRUCTION
RANDOM_RESTRICTION_ARGUMENT != DETERMINISTIC_SOLVER_STEP
```

## 6. Next exact gate

Before any self-reduction is used as an algorithmic Policy-0B primitive:

1. freeze graph/base-function representation;
2. freeze the selector for every nonunique Algorithm-1 choice;
3. prove it always returns an object satisfying the source hypotheses at the claimed scope;
4. charge total bit complexity in original `N`;
5. keep this separate from the F3-D semantic survival probability theorem.

This is an accounting gate, not a lower bound on Sokolov's proof and not a complexity-class result.
