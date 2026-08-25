# PF5 P=NP Spiral — Hephaestus Crystal v14

## Role

Hephaestus is admitted here only as an immutable state crystallizer, recurrence guard, and cost accountant.

Historical `hephaestus_crystal.py` was a metadata/entropy/slack analyzer, not evidence for P=NP. v14 reuses only the safe architectural idea: freeze a state, hash it, charge its bytes, and compare exact identities.

## No-heuristic contract

Hephaestus Crystal MUST NOT:

- choose a projection variable;
- call SAT, PS-width, truth tables, Slime, or an optimization oracle;
- rank states by entropy, slack, size, or any learned score;
- claim semantic equivalence from a hash match.

It MAY:

1. canonicalize explicit CNF syntax by deterministic literal/clause ordering;
2. serialize the canonical state;
3. hash it with SHA-256;
4. count source/residual/proof bytes;
5. mark an exact syntactic recurrence when the canonical bytes/hash were already observed.

`HASH_EQUALITY => CANONICAL_SYNTACTIC_IDENTITY`, nothing stronger.

## Spiral protocol

The v11 diagnostic corpus `907000..907015` is replayed in fixed seed order through already-admitted exact closure:

`v12 PURE_LITERAL_EXISTENTIAL_PROJECTION`

then

`v13 TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION`

until fixed point.

For each source and residual, v14 emits a Hephaestus crystal containing:

- canonical CNF SHA-256;
- canonical serialized byte count;
- variables / clauses / literal occurrences;
- proof transcript bytes;
- exact operator counts;
- recurrence flag against earlier residual crystals;
- parent/source crystal hash.

The first non-empty residual in the already-frozen seed order becomes the next obstruction. No score selects it.

## Journal law

Every spiral entry records:

`INPUT -> EXACT_RULES_APPLIED -> OUTPUT_CRYSTAL -> NEW_FACT -> CLOSED_GATES -> OPEN_GATE -> DO_NOT_REPEAT`

An identical residual crystal is a recorded revisit, not a new discovery.

## Claim ceiling

`HEPHAESTUS_CRYSTAL = EXACT_SYNTACTIC_STATE_RECEIPT`

`HEPHAESTUS_CRYSTAL != P_VS_NP_SOLVER`

`UNIVERSAL_POLYNOMIAL_SEMANTIC_DECOMPOSITION_DISCOVERY = OPEN`

`P_VS_NP = OPEN`
