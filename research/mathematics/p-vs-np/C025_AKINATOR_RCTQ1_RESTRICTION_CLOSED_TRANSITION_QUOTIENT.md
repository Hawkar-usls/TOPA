# C025 — JANUS RCTQ-1: restriction-closed transition quotient

Status: **FROZEN PROTOCOL BEFORE PROVIDER / P_VS_NP OPEN**

## 0. Target

The active JANUS route requires an exact proof-carrying transition representation, not a heuristic solver selector.

RCTQ-1 separates three quantities that must not be conflated:

1. `STATE_SIZE`: bytes of one canonical quotient state;
2. `TRACE_VOLUME`: total states/bytes actually materialized by one deterministic execution;
3. `ALL_RESTRICTION_RESIDUAL_COUNT`: number of inequivalent residual functions obtainable over all partial restrictions.

Only (1)+(2), together with exactness, closure, discovery, verification and witness costs, are required for a polynomial deterministic SAT execution. A polynomial bound on (3) would be sufficient but may be unnecessarily strong.

## 1. Exact RESTRICT operator

For canonical CNF `F` and a compatible partial assignment `rho`, define `RESTRICT(F,rho)` by:

- delete every clause satisfied by `rho`;
- delete every literal falsified by `rho` from surviving clauses;
- if an empty clause appears, return canonical `FALSE`;
- canonicalize literals, clauses and duplicates.

This is exactly the residual Boolean relation on unassigned variables.

Composition law for compatible assignments with disjoint domains:

`RESTRICT(RESTRICT(F,rho),sigma) = RESTRICT(F,rho union sigma)`.

Construction is polynomial in the explicit input state and assignment size.

## 2. Context-certified intact-B2 congruence

For current intact definitions

`Def(e;a,b) := (!e|a) & (!e|b) & (e|!a|!b)`

and

`Def(f;a,b)`,

every model has `e=f`. The canonical duplicate output may be substituted by the representative with deterministic witness lift.

RCTQ-1 promotes this old exact theorem into a transition object:

`ALIAS(e -> r, certificate)`.

After a certified alias has been introduced, later restriction may destroy the syntactic three-clause definition, but the already-proved equality is preserved by restriction. The alias therefore persists as provenance rather than being re-authorized from stale gate syntax.

The quotient state is

`Q = (canonical residual CNF over representatives, canonical alias map, witness provenance)`.

Restriction acts on representatives; assignments to aliases are translated through the certified map and inconsistent alias assignments are rejected.

## 3. Closure theorem in the certified-alias language

If `Q` is an RCTQ-1 certified-alias state and `rho` is a compatible partial assignment, then direct restriction produces another RCTQ-1 state without reconstructing deleted duplicate gates.

Exactness is equisatisfiability plus deterministic witness lift through the alias map.

This is a restricted exact transition language. It does **not** assert a universal polynomial quotient for arbitrary CNF.

## 4. Mandatory adversarial control: selector-unit family

For `n>=1`, define

`F_n := AND_{i=1..n} (z_i OR y_i)`.

For every subset `S subseteq {1..n}`, define a restriction assigning **all** selector variables:

- `z_i=0` if `i in S`;
- `z_i=1` if `i notin S`.

Then

`RESTRICT(F_n,rho_S) = AND_{i in S} y_i`.

Hence there are exactly `2^n` pairwise distinct residual Boolean functions over the common remaining variables `y_1..y_n`.

Moreover for `S != T`, choose `i in S triangle T`; setting `y_i=0` and every other `y_j=1` distinguishes the two residuals by satisfiability under the continuation.

Therefore any quotient equivalence that must preserve **all future restrictions/continuation satisfiability** must distinguish at least `2^n` classes on this family.

Consequently the universal target

`ALL_RESTRICTION_RESIDUAL_CLASSES <= poly(N)`

is false for this exact future-congruence notion.

This does **not** refute P=NP and does not refute a deterministic polynomial trace that visits only polynomially many states.

## 5. Corrected universal target

The P=NP route must target:

`DETERMINISTIC_EXACT_EXECUTION`

with

- polynomial bytes per materialized state;
- polynomial number/volume of states actually materialized;
- polynomial discovery/build/projection/verification/witness cost;
- sequential exact closure;
- exact SAT/UNSAT terminal.

It must **not** require polynomial cardinality of the entire counterfactual restriction state space.

The Keymaster quantity `M(N)` is henceforth interpreted only as the number of canonical transition states actually retained/materialized by the frozen deterministic exact execution/frontier, not the number of all possible restriction residual functions.

## 6. Frozen finite verifier ladder

The provider must be written after this file and must check without heuristic selection:

- RESTRICT exactness and composition on fixed CNFs;
- intact-B2 duplicate equality and alias witness lift by independent finite exhaustive replay;
- alias persistence under subsequent restrictions;
- selector-unit family counts for `n in {4,8,12,16}` equal `2^n` by canonical residual construction;
- deterministic continuation distinguisher for every enumerated pair only at small `n=8`, and analytic count/law for larger n;
- no change to active 14-operator Keymaster catalog in this gate.

Finite exhaustive checks are post-freeze judges only and have no runtime discovery authority.

## 7. Claim ledger

`RESTRICT_EXACTNESS = TO_BE_VERIFIED_AGAINST_FROZEN_THEOREM`

`RESTRICT_COMPOSITION = TO_BE_VERIFIED_AGAINST_FROZEN_THEOREM`

`CERTIFIED_INTACT_B2_ALIAS_PERSISTS_UNDER_RESTRICTION = TO_BE_VERIFIED`

`RCTQ1_CERTIFIED_ALIAS_LANGUAGE_RESTRICTION_CLOSED = TO_BE_VERIFIED`

`ALL_RESTRICTION_FUTURE_CONGRUENCE_CLASSES_POLYNOMIAL = REFUTED_BY_SELECTOR_UNIT_FAMILY`

`POLYNOMIAL_DETERMINISTIC_TRACE_VOLUME_FOR_ARBITRARY_CNF = OPEN`

`UNIVERSAL_POLYNOMIAL_SAT_ALGORITHM = NOT_ESTABLISHED`

`P_VS_NP = OPEN`
