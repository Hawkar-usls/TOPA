# C025 — Akinator PF5: total certified residual quotient criterion

Status: **DIRECT ALGORITHMIC CRITERION / UNIVERSAL CONSTRUCTION OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The historical C025 certified-residual-quotient work and the current PF1–PF4 line converge on the same bottleneck:

`POLYNOMIALLY_DISCOVERABLE_DECOMPOSITION + CHEAP_CERTIFIED_QUOTIENT`.

The old C025 artifact separated two costs:

- continuation-distinct residual state volume;
- proof volume needed to certify merges.

BH-Q2 then gave a finite negative control showing that a stronger quotient can reduce some local Resolution work while increasing canonicalization/discovery work substantially.

PF5 therefore freezes a four-part total-cost criterion so that no future quotient can hide the exponent in an uncharged column.

---

## 1. Frozen cost decomposition

For original CNF `F` of encoded length `N`, let a deterministic proof-carrying quotient solver produce a trace of proposal, verification, merge, projection and witness-return events.

Define cumulative costs over the **entire run**, including rejected candidates:

### Q_state(F)

Total explicit state/representation volume:

- distinct residual states or DAG nodes ever created;
- temporary states later discarded;
- transition records;
- live boundary tables;
- canonical representation nodes.

A small final object does not erase earlier state volume.

### Q_proof(F)

Total logical/certificate volume:

- normalization certificates;
- signed-map/orbit certificates;
- B2/Resolution rewrite proofs;
- equivalence/quotient witnesses;
- exact projection certificates.

### Q_discovery(F)

Total work needed to *find* accepted certificates:

- failed candidate generation;
- failed canonicalizations;
- rejected equivalence/orbit attempts;
- refinement edge visits;
- order/decomposition search;
- all selector work before acceptance.

A verifier that is cheap after an expensive search does not make the solver polynomial.

### Q_witness(F)

Total provenance required to reconstruct/check a SAT witness or an UNSAT terminal:

- inverse maps;
- eliminated-variable choices;
- lineage/parent links;
- stored witness-return data;
- verification work for the returned witness/proof terminal.

Define

`Q_total(F) := Q_state(F) + Q_proof(F) + Q_discovery(F) + Q_witness(F)`

under a fixed bit/operation encoding model.

Parallel execution may reduce wall-clock latency but every operation remains charged to the corresponding total-work column.

---

## 2. Necessity theorem for this solver architecture

If a solver's actual deterministic runtime is bounded by `N^c` for one universal fixed `c`, then each nonnegative charged component above is individually bounded by `N^O(1)`.

This is immediate from

`Q_component(F) <= Q_total(F) <= Time(F)`

under the frozen accounting where every recorded operation/byte is produced by the solver.

Therefore any family with a proved superpolynomial lower bound on **one mandatory component for a frozen architecture** closes that architecture as a polynomial-time route.

Important: such a component lower bound is not automatically a lower bound against other representations or algorithms.

---

## 3. Sufficient criterion

Assume there exists one deterministic algorithm `A` and universal constants `c,k` such that for every CNF `F` of encoded length `N`:

1. `A` starts from an exact state representing `F`;
2. every accepted transformation is independently checkable and SAT-preserving/equisatisfiable with explicit witness/proof provenance;
3. every nonterminal accepted step decreases a frozen well-founded rank, or the total number of accepted steps is otherwise proved `<=N^k`;
4. proposal, failed proposal, verification, representation, proof and provenance costs are all included in `Q_total`;
5. `Q_total(F) <= N^c`;
6. the terminal state yields exact `SAT` or `UNSAT`;
7. on SAT, an original-variable witness is reconstructed and checked in polynomial time.

Then `A` decides SAT in deterministic polynomial time.

Hence

`SAT in P`, and because SAT is NP-complete,

`P = NP`.

This is a direct algorithmic implication, not evidence that such `A` exists.

---

## 4. Historical C025/BH-Q2 finite control

Frozen GT12 data from the 2026-08-18 bidirectional run supplies a concrete warning.

Q1 work proxy:

`resolution_attempts + refinement_edge_visits = 14,175,910`.

BH-Q2 work proxy:

`resolution_attempts + signed_refinement_edge_visits + q0_fallback_refinement_edge_visits = 55,323,019`.

BH-Q2 reduced Resolution attempts by about `11.7%` and found many more exact signed absorptions, but its frozen total proxy was about `3.90x` Q1 and both lanes still hit the same 20,000-state OPEN cap.

This finite result proves no asymptotic lower bound. It falsifies only the naive inference

`MORE_CERTIFIED_MERGES OR FEWER_RESOLUTION_ATTEMPTS => LOWER_TOTAL_WORK`.

---

## 5. Exact role of the PF5 operator portfolio

The portfolio is a deterministic first-accepting controller over exact operators such as:

- PF1 prebirth pivot factorization;
- certified subsumption normalization;
- low-live-width exact relational DP;
- capped ROBDD/decision-diagram lanes;
- exact prebirth orbit/signed-map quotients;
- B2/ER-certified rewrites;
- fail-closed residual automata.

The controller may use a cheap proposal heuristic internally, but a heuristic has zero logical authority and all proposal work is charged.

To prove P=NP through PF5, it is not enough to show that every tested family is solved. One must prove one universal fixed polynomial bound on `Q_total(F)` for **every** CNF.

---

## 6. Architecture-specific negative theorem template

For a frozen operator policy `Pi`, a valid route-closure theorem has the form:

> There exists an explicit infinite family `F_n` such that every `Pi` run must incur `Q_component(F_n) >= g(N_n)` with `g` superpolynomial in actual encoded input length `N_n`.

Examples already established in restricted lanes:

- plain Resolution/Policy0B.1: exponential proof/runtime lower bound via PHP;
- frozen syntactic Shannon equality projector: cumulative DAG novelty `>=2^n`;
- universal DNNF container: external strongly exponential representation lower bound on sparse expander graph CNFs.

These close those lanes only.

---

## 7. Universal positive theorem template

A valid closure theorem has the form:

> For every CNF `F` of length `N`, the frozen deterministic PF5 controller finds an accepted exact rank-decreasing operator step until termination and satisfies `Q_total(F)<=N^c` for one universal fixed `c`.

Together with exact terminal/witness correctness, this is a polynomial SAT algorithm and proves `P=NP`.

No weaker finite scaling observation has this consequence.

---

## 8. Current open subproblem

Find either:

### Positive

A polynomially complete proof-carrying quotient/decomposition language with deterministic polynomial discovery and global progress.

### Negative for current PF5

An explicit family that simultaneously escapes every currently frozen capped operator, with the escaping cost proved in the operator's own mandatory accounting resource.

Finite GT12 is a holdout for capability localization, not an asymptotic lower bound.

---

## 9. Claim ledger

`PF5_TOTAL_QUOTIENT_COST_DECOMPOSITION = FROZEN`

`POLYTIME_PF5_IMPLIES_EACH_CHARGED_COMPONENT_POLY = PROVED_BY_ACCOUNTING`

`UNIVERSAL_POLY_Q_TOTAL_PLUS_EXACT_TERMINATION_IMPLIES_P_EQUALS_NP = PROVED_AS_DIRECT_ALGORITHMIC_IMPLICATION`

`HISTORICAL_BHQ2_STRONGER_QUOTIENT_TOTAL_WORK_ADVANTAGE = NOT_ESTABLISHED_FINITE_NEGATIVE_CONTROL`

`UNIVERSAL_POLY_Q_TOTAL = OPEN`

`P_VS_NP = OPEN`

---

## 10. Laws

- `MORE_MERGES != LESS_TOTAL_WORK`
- `CHEAP_VERIFIER != CHEAP_CERTIFICATE_DISCOVERY`
- `SMALL_STATE_SET != SMALL_MERGE_PROOF_VOLUME`
- `SMALL_FINAL_STATE != SMALL_CUMULATIVE_STATE_VOLUME`
- `PARALLEL_LATENCY != TOTAL_WORK`
- `ALL_FAILED_QUOTIENT_ATTEMPTS_ARE_CHARGED`
- `P_EQUALS_NP_REQUIRES_ONE_UNIVERSAL_POLYNOMIAL_BOUND_ON_THE_FULL_TRACE`
