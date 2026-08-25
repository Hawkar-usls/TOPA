# C025 — Akinator PF5-R3: exact CNF incidence-component decomposition

Status: **EXACT STRUCTURAL DECOMPOSITION THEOREM / UNIVERSAL EFFECT OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

After PF1, certified subsumption, intact-gate congruence and dead-intact-gate GC, the frozen GT12 residue remains above the exact residual-automaton handoff input cap.

Before invoking a stronger relational quotient, test the cheapest exact structural possibility: perhaps the current CNF is only large because it is the conjunction of independent variable-disjoint components.

---

## 1. Incidence components

For a CNF `F`, form the bipartite incidence graph with:

- one vertex for each current variable;
- one vertex for each current clause;
- an edge `(v,C)` iff `v` or `NOT v` occurs in `C`.

Let the connected clause-components induce sub-CNFs

`F_1,...,F_k`.

Distinct nonempty components use pairwise disjoint variable sets.

An empty clause is handled separately as an immediate UNSAT terminal.

---

## 2. Theorem C1 — exact conjunction decomposition

If `F` contains no empty clause, then

`F = AND_i F_i`

and

`SAT(F) iff for every i, SAT(F_i)`.

### Proof

Every clause belongs to exactly one connected incidence component, so their conjunction is exactly `F`.

If `F` is satisfiable, restriction of a model to the variables of each component satisfies that component.

Conversely, because component variable sets are disjoint, any satisfying assignments of all `F_i` can be unioned without conflict into one assignment satisfying every clause of `F`. QED.

---

## 3. Exact witness composition

For SAT, component witnesses combine by disjoint union.

For UNSAT, one UNSAT component is sufficient to refute the whole conjunction.

If the state contains extension variables that later need original-root witness reconstruction, the existing PF1/PF2 provenance obligations remain separate. Component decomposition does not erase `Q_witness`.

---

## 4. Discovery and accounting

Connected components are found by a deterministic graph traversal over the explicit current CNF.

Charge:

- each literal occurrence inspected;
- variable-to-clause adjacency records;
- traversal visits;
- component serialization;
- all downstream per-component solver work.

Thus component discovery is polynomial in the explicit current state. This does not by itself prove polynomial work in original input `N` when the current state has already grown superpolynomially.

---

## 5. Frozen GT12 successor rule

Starting from the already-frozen post-congruence/post-GC state:

1. build exact incidence components;
2. keep the handoff input cap `20000` unchanged;
3. keep a **global cumulative residual-state budget of 20000** across all component automata;
4. never treat `20000` as a fresh independent budget for every component;
5. if any component encoding exceeds `20000`, stop with `OPEN_GIANT_COMPONENT_INPUT_CAP`;
6. if all components fit, process them deterministically largest-first (tie by canonical component serialization) while decrementing the one shared state budget;
7. every component input, state and witness byte remains charged.

This prevents decomposition from multiplying a fixed cap by the number of components.

---

## 6. Interpretation map

### Many small components

A large global CNF can be an accounting artifact of independent subproblems. Component decomposition may legitimately restore an exact capped handoff.

### One giant component

Then disconnected conjunction is not the source of the residue. The next exact resource is the internal boundary correlation/width of that connected component.

### Several medium components

The sum of exact work still matters. `MAX_COMPONENT_SMALL` does not imply `TOTAL_WORK_SMALL` without the shared ledger.

---

## 7. Claim ledger

`CNF_INCIDENCE_COMPONENT_DECOMPOSITION_EXACT = PROVED`

`COMPONENT_WITNESS_COMPOSITION_EXACT = PROVED`

`COMPONENT_DISCOVERY_POLY_IN_EXPLICIT_CURRENT_STATE = PROVED`

`PER_COMPONENT_FRESH_STATE_BUDGET = FORBIDDEN_SHORTCUT`

`GT12_COMPONENT_STRUCTURE = NOT_YET_MEASURED`

`UNIVERSAL_POLY_COMPONENT_BOUND = OPEN`

`P_VS_NP = OPEN`

---

## 8. Laws

- `DISCONNECTED_CONJUNCTION_CAN_BE_SOLVED_COMPONENTWISE`
- `SMALL_MAX_COMPONENT != SMALL_TOTAL_WORK`
- `ONE_GLOBAL_BUDGET_MUST_NOT_BE_MULTIPLIED_BY_COMPONENT_COUNT`
- `GIANT_CONNECTED_COMPONENT_MOVES_THE_FRONT_TO_INTERNAL_BOUNDARY_WIDTH`
- `COMPONENT_DECOMPOSITION_DOES_NOT_DISCHARGE_PF1_WITNESS_PROVENANCE`
