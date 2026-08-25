# PF5 — Representation Escape Ladder v1

**Status:** `FROZEN_COMPOSITE_REPRESENTATION_STRESS_PROTOCOL`  
**Claim ceiling:** `P_VS_NP = OPEN`

## 1. Purpose

PF5 Boundary Coverage Matrix v0.1 found no finite portfolio coverage hole, but it did isolate lane-specific weaknesses:

- frozen-order OBDD hit its node cap on blocked equality;
- exact factor/live-boundary elimination hit its bucket-scope cap on the fan-out architecture;
- the current Tranception/orbit lane is deliberately restricted to parity/equality templates;
- C2G-Laminar is a progress sidecar, not a primary boundary language;
- RAW-B2 Shannon remained a generic primary representation on every v0 control.

v1 therefore does **not** add a new solver.

It asks whether the currently surviving generic representation can still close repeated existential projection when already-revealed weaknesses are composed in the same input.

---

## 2. Composite family

For parameter `m` and fixed `f=6`, define a conjunction of two disjoint components.

### Blocked equality component

Roots

```text
x_1,...,x_m,y_1,...,y_m
```

with

```text
EQ_m = AND_i (x_i <-> y_i).
```

The frozen OBDD order places all `x` roots before all `y` roots.

### Fan-out component

Fresh roots

```text
u_1,...,u_f,v_1,...,v_f
```

with

```text
e_i := u_i AND v_i
g_ij := e_i AND e_j  for all i<j
FAN_f := AND_{i<j} g_ij.
```

### Composite state

```text
HYBRID_{m,f} := EQ_m AND FAN_f.
```

The components are intentionally simple and the formula has the explicit satisfying witness `all roots = 1`.

This is **not** a hardness family. It is a representation-coverage stress family assembled from already-revealed lane weaknesses.

---

## 3. Frozen parameter ladder

Run all three sizes, with no stopping or retuning after the first result:

```text
m in {8,10,12}
f = 6
```

Thus root counts are

```text
28, 32, 36.
```

The same v0 representation caps remain unchanged.

No cap is raised between ladder rungs.

---

## 4. Frozen projection/order rules

Root IDs are canonical and projection is performed in ascending root-ID order.

OBDD order is the same canonical order, which means the equality component is blocked:

```text
x_1,...,x_m,y_1,...,y_m,u_1,...,u_f,v_1,...,v_f.
```

No variable-order search is allowed.

The factor lane uses the same exact factor construction and deterministic extension finalization order as v0.1.

The Tranception lane receives no new family-specific recognizer in v1. If the current template language cannot represent the conjunction, it must return `UNSUPPORTED` and charge the failed template checks.

C2G remains sidecar-only.

---

## 5. Ground truth

Every ladder member is SAT by the explicit all-true assignment.

Reference classification therefore consists of:

1. construct the all-true root assignment from the public family definition;
2. independently evaluate the original B2 DAG;
3. accept SAT only if the formula evaluates true.

This witness has zero selector authority and is used only to check finite semantic correctness.

No exponential DPLL reference is run for these larger composite controls.

---

## 6. Frozen cost law

All v0.1 accounting rules remain active, including PF5-BCM-001:

- partial failed construction must be charged;
- representation peak bytes and cumulative bytes are separate;
- failed discovery is not erased;
- every existential projection is charged;
- terminal finalization is charged;
- SAT witness return is charged.

The caps remain exactly those in `PF5_BOUNDARY_COVERAGE_MATRIX_V0.md`.

---

## 7. Interpretation

For each rung, a **finite primary representation-coverage escape** occurs iff every primary lane is one of:

```text
CAP_HIT
UNSUPPORTED
```

before producing a verified final Boolean value and witness under the frozen caps.

Allowed statement:

```text
CURRENT_PF5_PRIMARY_REPRESENTATION_PORTFOLIO_ESCAPED_ON_THIS_FROZEN_CONTROL_UNDER_THE_FROZEN_CAPS
```

Forbidden statements:

```text
NO_POLYNOMIAL_REPRESENTATION_EXISTS
P != NP
THE_FAMILY_IS_PROOF-COMPLEXITY-HARD
```

The family has an explicit easy SAT witness; any escape is about the current **representation/update portfolio**, not semantic hardness.

---

## 8. Scientific value of either outcome

If RAW-B2 crosses its frozen node/byte/work cap while OBDD/factor/orbit are already unavailable, the matrix obtains its first composite representation-coverage witness and the next research obligation becomes a new proof-carrying representation or a proved compositional switch.

If RAW-B2 remains under cap through all rungs, the result is still useful: the generic Shannon DAG survived the first deliberate cross-lane composite stress, and the next test must increase structural novelty rather than invent a solver.

---

## 9. Laws

- `COMPOSE_REVEALED_REPRESENTATION_WEAKNESSES_NOT_SOLVER_HEURISTICS`
- `PARAMETER_LADDER_NOT_POST_HOC_SINGLE_SIZE`
- `SAME_CAPS_ACROSS_ALL_RUNGS`
- `EASY_SEMANTICS_CAN_STILL_STRESS_A_REPRESENTATION`
- `PORTFOLIO_ESCAPE_UNDER_CAPS != REPRESENTATION_LOWER_BOUND`
- `RAW_B2_SHANNON_IS_THE_CURRENT_GENERIC_TARGET`
- `P_VS_NP = OPEN`
