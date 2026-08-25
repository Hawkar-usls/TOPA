# PF5 Slime PS-width Blind Probe v9

Status: **FROZEN BEFORE PROVIDER RUN**  
Claim ceiling: **P_VS_NP = OPEN**

## Purpose

Test whether the recovered JANUS Slime routing gene can help the existing C032/C040 semantic-decomposition route **only as a candidate producer**.

The Slime producer lives in `Hawkar-usls/Janus-Demiurge` and must be pinned by commit/blob. It receives only raw CNF source structure and emits a polynomial-size, assignment-independent manifest of candidate linear incidence-leaf orders. It is forbidden from computing SAT, PS-width, truth tables, branch assignments, witnesses, or post-probe repairs.

TOPA then independently performs an exact finite PS-signature audit on the already-frozen manifest. The exact audit is deliberately exponential and is **not** promoted to a polynomial algorithm. Its only role is to measure candidate quality on bounded controls.

## Lineage

- Janus-Fundamentum C032: JANUS semantic cut signatures are aligned with PS-width; a supplied decomposition of polynomial PS-width gives polynomial #SAT / weighted MaxSAT dynamic programming.
- Janus-Fundamentum C040: candidate generation must be assignment-independent, polynomially bounded, frozen before probes, and fully charged.
- TOPA PF5 v8: fixed separator widths 0, 1, and 2 are constructive restricted lanes; the open issue is scalable semantic decomposition discovery.
- Janus-Demiurge Slime: `HEURISTIC_GENERATOR_EXACT_VERIFIER_SPLIT` and `REMEMBER_USEFULNESS -> PRUNE_WEAK -> GROW_IF_NEEDED -> SPEND_PRECISION_WHERE_TRACE_IS_HIGH`.

## Pinned producer contract

Expected upstream path:

`Hawkar-usls/Janus-Demiurge::models/slime/slime_semantic_candidate_router.py`

Required producer fields:

- `frozen_before_probe = true`
- `exact_ps_width_computed_inside_generator = false`
- `sat_oracle_used = false`
- candidate role = `CANDIDATE_ONLY_NOT_WIDTH_CERTIFICATE`

Frozen candidate names:

1. `LEXICAL_BASELINE`
2. `EXACT_DUPLICATE_CLAUSE_BLOCKS`
3. `SIGNED_INCIDENCE_PROFILE_BLOCKS`
4. `SLIME_SEMANTIC_PRESSURE`

## Exact TOPA probe

For a linear order of incidence leaves, TOPA constructs the corresponding right-linear/caterpillar cut family and evaluates:

- every prefix cut;
- every singleton leaf cut.

For each cut `S = C union X`, TOPA independently computes the two C032/STV precisely-satisfiable signature families and records

`cut_value = max(|PS_left|, |PS_right|)`.

The reported finite candidate width is the maximum exact cut value over this caterpillar cut family.

Every enumerated assignment and literal/clause check in the verifier is charged separately from Slime generation work.

## Frozen controls

### Calibration family — results may already be anticipated

Connected local-block chains with group counts:

`g in [2, 3, 4, 5]`

Each block has two duplicate local clauses and adjacent blocks are connected by a 3-literal bridge through one hub variable.

These controls test whether Slime keeps locally equivalent incidence structure together.

### Known semantic-gap controls

Duplicate wide-clause families:

- `K_4_4`: 4 variables, 4 identical clauses;
- `K_6_6`: 6 variables, 6 identical clauses.

C032 already proves that every cut PS-value in this family is at most 2 even though structural width can grow.

### Blind connected-3CNF holdout

The following seeds are frozen **before the provider run**:

`[905101, 905102, 905103, 905104, 905105, 905106, 905107, 905108]`

For every seed:

- variables: `n = 7`
- clauses: `m = 10`
- first `n-2` clauses form a signed 3-CNF chain backbone to guarantee connectedness;
- remaining clauses are seeded random signed 3-clauses.

No holdout candidate may be changed after its manifest hash is produced.

### Negative / pressure control

Unit-clause signature family at `n = 8`, retained only to show that exact cut-state explosion can still occur for a poor cut. A bad cut is not a lower bound on optimal PS-width.

## Frozen evaluation questions

1. Does Slime beat or tie lexical ordering on the blind connected-3CNF holdout?
2. Does Slime beat the best of the three non-Slime frozen candidates?
3. Does any control force exact PS cut-state growth despite Slime routing?
4. Is generator work polynomially explicit and independent of exact probe results?
5. Are all losses and failed improvements preserved rather than tuned away?

## Prohibitions

- no post-probe candidate generation;
- no holdout seed replacement;
- no exact PS-width call inside the producer;
- no SAT/UNSAT oracle inside the producer;
- no hidden truth table inside the producer;
- no use of finite exact-probe cost as the claimed polynomial algorithm;
- no promotion of a Slime win to universal candidate completeness;
- no promotion of a Slime loss to hardness;
- no `P=NP` claim.

## Surviving theorem gate

Even if Slime wins every finite control, the unresolved statement remains:

`POLYNOMIAL_SEMANTIC_DECOMPOSITION_CANDIDATE_COMPLETENESS_WITH_CHARGED_DISCOVERY`

A universal result would require a polynomially generated candidate/decomposition construction that is proven to contain or directly build a polynomial-message decomposition for every CNF, with proof-carrying join, projection, decision, and witness recovery.

`P_VS_NP = OPEN`
