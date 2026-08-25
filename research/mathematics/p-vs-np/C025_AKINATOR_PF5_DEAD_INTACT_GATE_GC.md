# C025 — Akinator PF5-R2: dead intact-gate garbage collection

Status: **EXACT LOCAL EXISTENTIAL-PRUNING THEOREM / UNIVERSAL EFFECT OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Motivation

After PF1 projection and exact intact-gate congruence, a current state may still contain many complete B2 definitions whose outputs no longer feed any retained constraint.

Such definitions are not boundary information. They are dead computation history.

Before invoking stronger semantic quotient machinery, remove this dead state exactly.

---

## 1. Frozen dead-gate criterion

Let the current CNF contain the complete intact B2 definition

`Def(e;a,b) := (NOT e OR a) AND (NOT e OR b) AND (e OR NOT a OR NOT b)`.

Call `e` **state-dead** iff every current clause containing literal `e` or `NOT e` belongs to this exact three-clause definition.

No historical provenance alone can establish deadness. The criterion is computed from the current exact CNF.

---

## 2. Theorem G1 — deleting a dead intact definition preserves existential satisfiability

If `e` is state-dead, let

`F = R AND Def(e;a,b)`

where `R` contains no occurrence of `e`.

Then

`SAT(F) iff SAT(R)`.

More strongly, as a relation over every variable except `e`,

`exists e . F == R`.

### Proof

For every assignment to variables of `R`, exactly one value

`e := a AND b`

satisfies the complete B2 definition. Therefore existentially quantifying `e` makes `Def(e;a,b)` identically true, leaving exactly `R`. QED.

---

## 3. Exact witness/provenance receipt

If a SAT witness for `R` is later available and values of signed inputs `a,b` are available, lift to the deleted extension output by

`e := value(a) AND value(b)`.

Therefore state bytes can be removed while a compact provenance record

`(e, a, b)`

is retained if full extension-witness reconstruction is required.

Important PF2 boundary: a recipe is valid only because the definition was **current and intact at deletion time**. A stale historical definition whose clauses were changed by projection is not eligible.

The full solver must charge these provenance records under `Q_witness`.

---

## 4. Recursive garbage collection

Deleting a dead output may make one or more of its input extension gates dead. Repeat the exact criterion until no further deletion applies.

Each successful deletion strictly reduces the current extension-variable count and removes at least one definition triple, so the process terminates after at most the number of intact definitions present at entry.

A deterministic implementation can maintain occurrence sets and a queue of newly exposed parent outputs. Even a naive rescanning implementation is polynomial in the explicit current-state size times the number of deletions.

This proves local algorithmic tractability relative to the explicit state, not a universal polynomial bound in original input `N`.

---

## 5. Why this is different from subsumption and congruence

- **subsumption** deletes a clause implied syntactically by a retained subset-clause;
- **gate congruence** merges two live intact outputs computing the same signed AND;
- **dead-gate GC** existentially removes an intact output that is not used outside its definition.

All three are exact, cheap relative to the current state, and use no semantic oracle. They attack different forms of avoidable representation residue.

---

## 6. Boundary of the theorem

G1 does not authorize deletion when `e` appears in:

- another gate definition;
- a projected relational clause;
- a final/root constraint;
- a retained proof/witness obligation represented in the current logical state.

Nor does it delete a non-intact historical gate merely because a dependency graph says it “should” be dead.

For non-intact outputs, existential projection can leave an arbitrary relation; PF2 applies.

---

## 7. GT12 finite successor protocol

Starting from the exact PF1 GT12 residue:

1. apply intact-gate congruence to fixpoint;
2. identify dead intact outputs by current occurrence equality with their exact definition triples;
3. delete all currently dead outputs and record `(e,a,b)` provenance;
4. repeat to fixpoint;
5. charge occurrence/index/deletion work and provenance volume;
6. keep the same handoff input cap `20000` and state budget `20000`;
7. do not raise caps after inspection.

If the residue stays above the handoff cap, the surviving cost is more plausibly genuine live boundary/relational structure rather than duplicated/dead intact computation.

---

## 8. Claim ledger

`DEAD_INTACT_B2_DEFINITION_EXISTENTIAL_DELETION = PROVED`

`DEAD_INTACT_GATE_WITNESS_RECIPE = PROVED_IF_INPUT_VALUES_ARE_AVAILABLE`

`RECURSIVE_DEAD_INTACT_GATE_GC_TERMINATES = PROVED`

`POLY_IN_CURRENT_EXPLICIT_STATE = PROVED_FOR_STRAIGHTFORWARD_IMPLEMENTATIONS`

`GT12_DEAD_GATE_REDUCTION = NOT_YET_MEASURED`

`UNIVERSAL_POLY_RESIDUE_AFTER_GC = OPEN`

`FULL_PF1_WITNESS_PROVENANCE_ACROSS_ALL_PROJECTIONS = OPEN_IMPLEMENTATION_OBLIGATION`

`P_VS_NP = OPEN`

---

## 9. Laws

- `DEAD_COMPUTATION_HISTORY != LIVE_BOUNDARY_INFORMATION`
- `CURRENT_INTACT_DEFINITION + NO_EXTERNAL_USE => SAFE_EXISTENTIAL_GC`
- `STATE_COMPRESSION_CAN_MOVE_BYTES_INTO_Q_WITNESS`
- `STALE_PROVENANCE_DOES_NOT_AUTHORIZE_GC`
- `POLY_GC_RELATIVE_TO_CURRENT_STATE != UNIVERSAL_POLYTIME`
