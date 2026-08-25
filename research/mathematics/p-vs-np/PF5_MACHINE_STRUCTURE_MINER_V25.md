# PF5 Machine Structure Miner v25

## Purpose

v25 is **not a solver** and does not add a theorem to the admitted proof-carrying portfolio.
It is a post-hoc machine observer over the 11 `OPEN_RESIDUAL` outputs left by the authoritative v24 frozen holdout.

The point is to let JANUS compare all survivors simultaneously in a representation that is difficult to inspect reliably by eye: clause-width spectra, signed incidence motifs, variable local signatures, component structure, interaction-cycle rank, and syntactic membership in standard tractable SAT classes.

## Frozen lineage

The input population is exactly the v24 holdout:

- `n=6, m=24, seeds 916600..916615`
- `n=7, m=28, seeds 916700..916715`

Authoritative v24 result SHA:

`865eb2de5fdc2c7ae0687f261304bfbafa36ac61cacdd0bcb14441dba1e8a8b9`

Expected v24 terminal split is frozen as `18 TRUE / 3 FALSE / 11 OPEN`.

## Machine-only structural view

For every OPEN residual v25 records:

- canonical residual crystal and SHA-256;
- clause-width histogram;
- variable count, clause count and deficiency `m-n`;
- Horn / dual-Horn / bijunctive (2-CNF) membership;
- unit-clause presence;
- variable-interaction connected components;
- interaction edges and cycle rank;
- signed variable-context signatures;
- repeated signature classes (collision only; **not** an automorphism proof);
- clause-pair overlap/complement motifs;
- exact-action frontier suggested by structural membership.

## Action frontier

The observer may nominate these lanes, but nomination is **not admission**:

- `COMPONENT_PRODUCT` — already supported by an exact disjoint-component theorem when the residual actually splits;
- `UNIT_PROPAGATION_CERTIFICATE` — standard exact reduction, provider still required here;
- `BIJUNCTIVE_2SAT_SCC` — standard polynomial 2-SAT lane, proof-carrying provider required;
- `HORN_FORWARD_CHAIN` — standard polynomial Horn-SAT lane, proof-carrying provider required;
- `DUAL_HORN_FORWARD_CHAIN` — dual Horn analogue, proof-carrying provider required.

v25 ranks the frontier only by survivor coverage, with a frozen tie-break priority. It never evaluates SAT in order to choose a lane.

## Cost rule

Observation cost is charged explicitly: clause visits, literal visits, clause-pair tests, signature-context visits and graph-edge insertions. The miner is polynomial in the explicit residual size.

## Scientific ceiling

A v25 pattern is a **discovery result on an already viewed population**. It cannot validate the selected lane. After v25 selects a dominant structural lane, the next move is:

1. freeze a fresh v26 holdout;
2. only then implement the proof-carrying provider;
3. charge discovery/build/update/proof/witness costs;
4. retain all failures;
5. keep `P_VS_NP = OPEN`.
