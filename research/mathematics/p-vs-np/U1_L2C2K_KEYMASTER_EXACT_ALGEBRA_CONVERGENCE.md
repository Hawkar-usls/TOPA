# U1-L2C2K — KEYMASTER exact algebra convergence

Status: **FROZEN PROTOCOL BEFORE PROVIDER**

Primary goal remains `RESOLVE_P_VS_NP`; claim ceiling remains `P_VS_NP_OPEN`.

## 1. Motivation

Historical KEYMASTER has the useful architecture

`STATE -> GUARD -> TRANSITION -> MEMORY -> OUTPUT`

but its historical numeric threshold steering is not admitted in the P-vs-NP proof path.  This gate keeps the architecture and replaces every heuristic guard by an exact, certificate-carrying algebraic admission predicate.

## 2. No-heuristics invariant

An ACTIVE proof operator MUST NOT depend on random choice, stochastic search, score ranking, EMA, trace, shortlist/top-k, entropy threshold, resonance threshold, learned confidence, LLM judgement, or post-hoc finite success.

A historical method is either:

1. `ALGEBRAIZED_ACTIVE`: converted to an exact theorem/operator satisfying the contract below;
2. `DONOR_ONLY`: exact mathematics may be reused, but it cannot select a proof step;
3. `GOVERNANCE_ONLY`: provenance/safety/epistemic sidecar only;
4. `PRUNED_FROM_PROOF_PATH`: retained as history but has no theorem authority.

## 3. KEYMASTER state

A state is

`K = (H, L, O, Q, C)`

where:
- `H`: canonical syntactic Hephaestus fingerprint of the current representation state;
- `L`: representation language identifier;
- `O`: immutable set of still-open proof obligations;
- `Q`: cumulative charged cost vector;
- `C`: proof-chain/certificate digest.

Canonical hashing is only syntactic identity unless a separate exact semantic equivalence certificate is supplied.

## 4. Exact operator schema

An operator is

`A = (D,T,E,P,B,W,L')`

with:
- `D`: deterministic source/domain predicate;
- `T`: exact rewrite/projection/update;
- `E`: theorem or exact projection identity id;
- `P`: independently replayable certificate schema;
- `B`: polynomial discovery/build/update/verify bound (or an explicitly restricted fixed-family bound);
- `W`: polynomial witness lift/recovery;
- `L'`: declared codomain language.

Admission requires every field. A missing field is a fail-closed refusal.

## 5. Composition theorem

If `A_i` is exact on language `L_i`, produces `L_j`, and `A_j` has a certified domain predicate satisfied by that output, then `A_j o A_i` is exact. Certificates concatenate, charged costs add, and witness lifts compose in reverse order.

This is a composition theorem only; it gives no polynomial global frontier bound by itself.

## 6. Exact convergence rule

At any state KEYMASTER does **not choose a best method**.

1. Enumerate every operator in the finite certified catalog.
2. Evaluate each deterministic domain predicate.
3. Apply every admitted exact operator.
4. Canonicalize outputs and deduplicate exact syntactic duplicates.
5. Prune a route only with an exact certificate:
   - its theorem/domain was refuted for the state; or
   - it reaches the identical canonical state, language and obligations with a componentwise no-worse cumulative cost vector and at least one strict improvement; or
   - a stronger semantic equivalence + future-domain-preservation certificate is explicitly supplied.
6. Keep the exact non-dominated antichain.

There is no top-k, score, beam width, pressure, temperature or random tie break. Ties use lexical deterministic ordering for serialization only, never for scientific pruning.

If the exact non-dominated frontier is not polynomially bounded, emit `KEYMASTER_FRONTIER_EXPLOSION`; do not hide it by heuristic truncation.

## 7. Historical method triage frozen before provider

### PRUNED_FROM_PROOF_PATH
- `SLIME_SEMANTIC_PRESSURE`: trace/EMA/shortlist routing. Exact incidence/fingerprint/profile features are retained separately.
- `WALKSAT`: random assignment/noise/random unsatisfied clause.
- `PSO_SWARM` / score-based swarm optimization.
- historical `PHYSARUM` random-walk/path-threshold selection.
- legacy `HIVE_P_VS_NP` LLM score/theorem synthesis.
- historical KEYMASTER `m2r/e` threshold controller.
- Odonto M2R/EMA/champion/top-k/mutation steering.
- `RAMANUJAN_THETA_DIRECTOR` runtime steering.
- old `MOD_THETA_PRIME` threshold/random route.
- Hephaestus entropy/purity as a selector.

### DONOR_ONLY or ALGEBRAIZED fragments
- Slime exact clause incidence, exact duplicate classes and signed incidence profiles: `DONOR_ONLY` until an exact quotient theorem uses them.
- Physarum graph-flow equations: `DONOR_ONLY` until rational exact certificates and a SAT-side morphism exist.
- Ramanujan/Srinivasa theta sum-product identity and recurrence: `DONOR_ONLY`; C2B proved theta-only parameterization is not sequentially closed.
- Hephaestus canonical hash/revisit guard: `ALGEBRAIZED_ACTIVE` for syntactic identity/accounting only.
- KEYMASTER state/guard/transition/memory architecture: `ALGEBRAIZED_ACTIVE` through this protocol.

## 8. Existing exact operator families admitted to the catalog

The catalog may include only their already-certified source domains:
- pure-literal existential projection;
- tautological-resolvent existential projection;
- single-nontautological-resolvent projection;
- complementary twin contraction;
- clause subsumption;
- self-subsuming resolution;
- component product;
- 2-SAT SCC certificates;
- exact small strong-backdoor proof trees only where the complete bounded search is explicitly charged;
- affine GF(2) boundary join;
- restricted OBDD join;
- live-width DP / log-induced-width bucket elimination on their certified domains;
- one-pivot prebirth quotient;
- exact local K4/G3 identity kernel, without claiming universal completeness;
- ACI shared-factor quotient;
- literal ACI direct/sequential existential update;
- C2B symmetric-weight quotient and its exact sequential update.

## 9. Required verifier obligations

The first provider must verify:
- no ACTIVE catalog entry contains forbidden heuristic authority;
- every ACTIVE entry contains domain/theorem/certificate/bound/witness/codomain fields;
- exact composition is type-checked;
- duplicate-state cost dominance is deterministic and certificate-producing;
- a deliberately cheaper duplicate path is pruned;
- incomparable exact paths remain in the frontier;
- an injected heuristic method is rejected;
- frontier growth is reported, never silently truncated.

## 10. Scientific result this gate may establish

A PASS establishes only an exact **method-composition and pruning algebra** for already-certified operators. It does not establish universal polynomial frontier size and does not solve P vs NP.

New active debts after PASS:
- `U1-L2C2C`: exact discovery/construction of a polynomial transition quotient for arbitrary nonliteral factors;
- `KEYMASTER_FRONTIER_POLY_BOUND`: prove a polynomial bound on the exact non-dominated operator/state frontier, or expose an obstruction;
- universal sequential closure/global cost for arbitrary CNF.

`P_VS_NP = OPEN` until those universal obligations are actually closed.
