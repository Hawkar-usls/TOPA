# C025 — Akinator U1-L2B2: shared-fanout escape for the fixed context-closed local grammar

Status: **EXPLICIT_INFINITE_ESCAPE_FAMILY_FOR_CURRENT_LOCAL_GRAMMAR / NOT_A_P!=NP_RESULT**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-L2B0/B1/B1A establish a useful exact local rewrite system:

- complete frozen local Boolean identity synthesis for `k=4, g<=3`;
- exact all-boundary dependency-mask costs;
- context-closed global affected-cone monotonicity;
- polynomial fixed-catalog saturation.

The remaining question is **coverage**. Does this grammar necessarily expose enough local progress to drive the projected affected cone to a small interface?

This note gives an explicit infinite family showing that the answer is **no for the current bounded context-closed grammar**.

The obstruction is not Boolean hardness. It is shared fanout: exact common factors can be globally obvious while being inaccessible to every admitted small closed region.

---

## 1. Family `SF_4(m)`

Fix integer `m >= 2`.

Root variables:

```text
x
y_1,...,y_m
z_1,z_2,z_3,z_4
```

Create `m` shared gates

```text
a_i := x AND y_i.                (1 <= i <= m)
```

For each lane `r in {1,2,3,4}`, build a positive binary AND tree/chain computing

```text
C_r := z_r AND a_1 AND a_2 AND ... AND a_m.
```

The four lane implementations are disjoint except that they all read the same shared signals `a_i`.

Finally compute

```text
OUT := C_1 AND C_2 AND C_3 AND C_4
```

with three positive binary AND gates.

Every `a_i` has exactly four lane users before saturation.

One concrete left-chain implementation uses:

```text
m                    shared a_i gates
4m                   lane gates, since each C_r has m+1 inputs
3                    final combining gates
---------------------------------------------
G_0(m) = 5m + 3.
```

Every one of these gates syntactically depends on `x`, hence initially

```text
AC_x(SF_4(m)) = 5m + 3.
```

---

## 2. Lemma B2.1 — a shared gate `a_i` cannot be rewritten by the frozen grammar

The frozen local grammar admits regions with at most `g=3` internal gates and requires context closure.

Consider one `a_i`.

### Case A: `a_i` is internal but not the designated region output

Then context closure requires **all outside users of `a_i`** to be inside the region.

`a_i` has one distinct user in each of four lanes, so any such region contains at least

```text
1 + 4 = 5
```

internal gates before including any additional path needed to obtain one designated output.

This exceeds frozen `g=3`.

Therefore no admitted region can contain `a_i` as a non-output internal gate.

### Case B: `a_i` itself is the designated output

The region can then consist of the single gate

```text
x AND y_i.
```

As a Boolean function of the two independent formal inputs, this is not equal to a signed boundary literal or a constant. A fan-in-two AND circuit computing it therefore needs at least one AND gate.

The source already has one gate and one `x`-dependent gate. Hence the frozen admission rule has no strict `(AC,G)` improvement.

Therefore no accepted local rewrite can replace/delete `a_i` directly.

QED.

---

## 3. Lemma B2.2 — each lane must continue to depend on every `a_i`

Treat the shared signals `a_1,...,a_m,z_r` as formal independent boundary inputs of lane `r`.

The lane function is exactly their conjunction:

```text
C_r = z_r AND a_1 AND ... AND a_m.
```

It semantically depends on every `a_i`: flipping one `a_i` from 1 to 0 while all other lane inputs are 1 flips the lane output from 1 to 0.

Every admitted local rewrite is an exact Boolean identity over its formal boundary inputs. Therefore rewrites inside a lane cannot make the lane output independent of any `a_i`.

A replacement region that does not contain `a_i` may reroute the lane's path from boundary `a_i`, but exact dependence guarantees at least one path from `a_i` to the lane output remains.

The four lanes are structurally disjoint below their final outputs. A bounded single-output context-closed replacement inside one lane cannot create a new internal gate shared by a different lane; its only externally visible signal is its own designated output.

Thus every lane retains a dependence path from each `a_i`, and each `a_i` retains at least one user/path obligation in each of the four lanes.

Combined with Lemma B2.1, the shared gates remain live and cannot later become eligible for deletion by the frozen grammar.

---

## 4. Theorem B2.3 — linear affected-cone survives any frozen local saturation

For every `m>=2`, after any sequence of admitted U1-L2B0/B1A context-closed rewrites on `SF_4(m)`, all `m` shared gates

```text
a_i = x AND y_i
```

remain live internal gates and remain syntactically dependent on `x`.

Therefore every reachable saturated state satisfies

```text
AC_x >= m.
```

Relative to the explicit initial state size

```text
G_0 = 5m+3,
```

we have

```text
AC_x >= (G_0-3)/5 = Omega(G_0).
```

Hence the fixed `k=4,g<=3` context-closed local grammar does **not** universally force the projection affected cone to `O(log N)` or any sublinear bound.

This is an exact incompleteness result for the current local grammar.

It is not a lower bound against arbitrary representations or arbitrary polynomial-time algorithms.

---

## 5. Yet a global exact quotient is tiny

The same function has a much smaller projection-aware representation.

By associativity, commutativity, and idempotence of conjunction,

```text
OUT
 = AND_r ( z_r AND AND_i a_i )
 = (AND_i a_i) AND z_1 AND z_2 AND z_3 AND z_4.
```

Since

```text
a_i = x AND y_i,
```

again by associativity/commutativity/idempotence,

```text
AND_i a_i
 = x AND y_1 AND ... AND y_m.
```

Thus

```text
OUT
 = x
   AND y_1 AND ... AND y_m
   AND z_1 AND z_2 AND z_3 AND z_4.
```

Compute the conjunction of all `m+4` roots other than `x` first, then AND with `x` once.

This needs

```text
(m+4)-1 = m+3
```

`x`-independent AND gates for the other roots, followed by one final `x`-dependent AND gate:

```text
G_compact = m+4
AC_x_compact = 1.
```

So the escape is not caused by an intrinsically large projection interface. It is caused by the locality/sharing restriction of the current grammar.

---

## 6. Exact missing operation exposed by the family

The family points to a new CREATE primitive:

```text
PROOF_CARRYING_ACI_SHARED_FACTOR_QUOTIENT
```

for conjunction blocks.

At the algebraic level:

```text
(A AND B_1) AND ... AND (A AND B_r)
  <=>
A AND B_1 AND ... AND B_r.
```

For a pure conjunction DAG, flattening under

```text
associativity + commutativity + idempotence
```

turns the output into a set of factor signals rather than a presentation-sensitive binary tree.

If factor identity is syntactic/proof-carrying, this quotient can be constructed without a general semantic-equivalence oracle.

---

## 7. What this rules out

```text
FIXED_K4_G3_CONTEXT_CLOSED_LOCAL_GRAMMAR_IS_UNIVERSALLY_COMPLETE = FALSE
POLY_LOCAL_SATURATION_IMPLIES_SMALL_PROJECTION_INTERFACE          = FALSE
LOCAL_AFFECTED_CONE_DESCENT_ALONE_CLOSES_U1_L2                    = FALSE
```

The B1 polynomial saturation theorem remains valid; it simply saturates to a local normal form that can still have a linear affected cone.

---

## 8. What this does not rule out

This family does not show:

- arbitrary proof-carrying rewrite grammars fail;
- global ACI/shared-factor normalization fails;
- arbitrary existential projections require large circuits;
- SAT is not in P;
- P!=NP.

In fact the family deliberately has a simple exact global quotient, so it is a **repair guide**, not a hardness candidate.

---

## 9. Frozen verification ladder

Before implementing the next quotient, verify the construction at

```text
m in {2,4,8,16,32,64}.
```

For every rung record:

- `G_0 = 5m+3`;
- initial `AC_x = G_0`;
- fanout of every shared `a_i` equals 4;
- bounded-region closure lower bound `1+fanout=5 > g=3`;
- symbolic ACI factor set of source output;
- symbolic ACI factor set of compact target;
- exact equality of those factor sets;
- `G_compact=m+4`;
- `AC_x_compact=1`;
- source and compact Hephaestus hashes.

No SAT oracle and no sampled valuation test is needed for the conjunction identity; symbolic ACI normalization is the proof object.

---

## 10. Next gate

`U1-L2C PROOF-CARRYING ACI SHARED-FACTOR QUOTIENT`

Requirements:

1. deterministic flattening of admitted pure-AND regions;
2. syntactic/proof-carrying factor identity only;
3. duplicate elimination by exact factor ID, not semantic guessing;
4. DAG sharing preserved/accounted;
5. polynomial construction and verification;
6. emitted quotient remains admissible for the next existential projection;
7. adversarial non-ACI controls retained.

```text
P_VS_NP = OPEN
```
