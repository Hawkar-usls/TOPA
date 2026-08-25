# JANUS RCTQ-2 — Frozen Exact Catalog Universal-Transition Falsification

**Status:** protocol frozen before provider/results  
**Primary goal:** `RESOLVE_P_VS_NP`  
**Claim ceiling:** `P_VS_NP = OPEN`  
**Global rule:** `NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT`

## 0. Question

RCTQ-1 corrected an over-strong target.  We do **not** require polynomially many
states over the entire counterfactual restriction universe.  We require a
polynomially bounded **actually materialized deterministic exact execution**.

The next necessary question for the currently frozen Keymaster catalog is:

> For every nonterminal CNF state, does at least one of the currently admitted
> exact typed operators provide a next exact transition in its certified domain?

This protocol attacks that statement **for the frozen 14-operator catalog only**.
A single explicit CNF state outside every currently applicable operator domain
is sufficient to refute universal coverage of that catalog.  Such a result does
not refute P=NP and does not refute future exact operators.

## 1. Frozen catalog

The authoritative active catalog has 14 operators:

1. `PURE_LITERAL_EXISTS`
2. `TAUTOLOGICAL_RESOLVENT_EXISTS`
3. `SINGLE_NTR_EXISTS`
4. `COMPLEMENTARY_TWIN`
5. `CLAUSE_SUBSUMPTION`
6. `SELF_SUBSUMING_RESOLUTION`
7. `COMPONENT_PRODUCT`
8. `TWO_SAT_SCC`
9. `AFFINE_GF2_JOIN`
10. `ACI_SHARED_FACTOR`
11. `LITERAL_ACI_EXISTS`
12. `SYMMETRIC_WEIGHT_EXISTS`
13. `SWAP_ORBIT_WEIGHT_EXISTS`
14. `SWAP_ORBIT_WEIGHT_EXISTS_CLOSED`

No operator may be added or have its domain widened after this protocol is
frozen.  `RESTRICT` and certified B2 alias-restriction closure proved in RCTQ-1
are deliberately **not** retroactively inserted into this frozen catalog.

## 2. Explicit candidate state

For `n >= 11`, define variables `x_0,...,x_(n-1)` and indices modulo `n`.
Define

```
A_i = ( x_i OR x_(i+1) OR NOT x_(i+2) )
B_i = ( NOT x_i OR x_(i+3) OR x_(i+5) )
E_n = AND_i (A_i AND B_i).
```

The authoritative escape witness for this gate is **exactly `E_37`**.
The additional frozen audit ladder is `{37,41,43,47}` and is secondary.

`E_n` is nonterminal and satisfiable: the all-ones assignment satisfies every
`A_i` and every `B_i` because every clause contains at least one positive
literal.

## 3. Exact domain checks

For a CNF state, the provider must test all source-language-compatible catalog
operators without ranking or early stopping.

### 3.1 Pure literal

For every variable, count positive and negative occurrences.  The operator is
admitted only if some variable occurs in exactly one polarity.

### 3.2 Tautological-resolvent and single-NTR projection

For every pivot `x`, enumerate the explicit positive-parent / negative-parent
pairs.  Build canonical resolvents.  Record the set of distinct non-tautological
resolvents.

- `TAUTOLOGICAL_RESOLVENT_EXISTS` applies iff some pivot has zero NTRs.
- `SINGLE_NTR_EXISTS` applies iff some pivot has exactly one distinct NTR.

No SAT oracle or semantic equivalence oracle is allowed.

### 3.3 Complementary twin

Check exact canonical clause membership for a pair

`(x OR A)` and `(NOT x OR A)`.

### 3.4 Strict clause subsumption

Check exact set inclusion between explicit clauses.

### 3.5 Self-subsuming resolution

Check the standard explicit syntactic predicate: clauses

`(l OR A)` and `(NOT l OR B)` with `A subseteq B`.

### 3.6 Component product

Build the variable-clause incidence graph and test connectedness exactly.
`COMPONENT_PRODUCT` applies only when the incidence graph has more than one
nonempty connected component.

### 3.7 Typed non-CNF lanes

`TWO_SAT_SCC`, `AFFINE_GF2_JOIN`, `ACI_SHARED_FACTOR`,
`LITERAL_ACI_EXISTS`, `SYMMETRIC_WEIGHT_EXISTS`, and
`SWAP_ORBIT_WEIGHT_EXISTS_CLOSED` have source languages other than raw `CNF`.
They must be reported as exact `REFUSE_SOURCE_LANGUAGE_MISMATCH` unless a
separately admitted conversion operator exists.  No implicit conversion is
permitted.

### 3.8 Swap-orbit quotient

Reuse the frozen U1-L2C2C1 exact pair-transposition discovery and its fixed
admission condition

`P <= N^4`,

where `P = product_j (|C_j|+1)` and
`N = variables + clauses + literal_occurrences + 1`.

If exact pair-swap discovery produces singleton classes on `E_37`, then
`P=2^37`; the provider must compare this to `N^4` exactly.

## 4. Verdict contract

The strong frozen-catalog statement

`FROZEN_14_CATALOG_UNIVERSAL_NEXT_TRANSITION_AVAILABILITY`

is **refuted** iff the provider establishes all of the following for `E_37`:

1. state is valid explicit CNF and nonterminal;
2. a concrete satisfying witness is replayed;
3. every one of the 14 frozen operators is either source-language incompatible
   or its exact domain predicate is false/refuses;
4. the catalog identity is verified against the frozen Keymaster source;
5. no heuristic, randomization, ranking, SAT oracle, truth-table oracle, or
   exact-optimum oracle participates in operator-domain discovery.

This is a result about **coverage of the current finite catalog only**.

## 5. What a negative result means

If `E_37` escapes all 14 operators, then

`FROZEN_14_CATALOG_UNIVERSAL_NEXT_TRANSITION_AVAILABILITY = FALSE`.

This does **not** imply SAT is hard, does not imply `P != NP`, and does not imply
that `E_37` itself is computationally difficult.  In fact its all-ones witness
makes satisfiability trivial externally.  The purpose is to isolate a missing
**exact transition schema** in JANUS.

This distinction is mandatory:

`CATALOG_COVERAGE_FAILURE != SAT_HARDNESS`.

## 6. RCTQ-1 interaction

RCTQ-1 proved exact `RESTRICT`, but a single restriction `F|x=b` is not by itself
an equisatisfiable existential projection of `F`; choosing one branch without a
theorem would be an inadmissible selector.  Therefore RCTQ-1 does not silently
repair frozen catalog coverage.

Any future use of restriction in a SAT-decision transition must provide an
exact branch-composition theorem, quotient, or other proof that preserves the
decision/witness contract with polynomial total materialized trace.

## 7. Next gate after either verdict

If the frozen catalog escapes, reverse JANUS must determine which exact missing
schema is smallest.  The default next obligation is:

`RCTQ3_EXACT_BRANCH_COMPOSITION_OR_NEW_EQUIVALENCE_PRESERVING_CNF_TRANSITION`

with the global cost target remaining:

`POLYNOMIAL_TOTAL_MATERIALIZED_DETERMINISTIC_TRACE_VOLUME_PLUS_STATE_BYTES_PLUS_Q_TOTAL`.

`P_VS_NP = OPEN`.
