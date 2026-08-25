# C025 — Akinator U1-L2C1: direct existential update closure for literal ACI quotients

Status: **FROZEN_PROTOCOL / PROVIDER_PENDING**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-L2C constructs an exact proof-carrying quotient for a closed pure-AND DAG by replacing its presentation-sensitive shared gate structure with a canonical set of exact signed leaf-factor IDs.

This gate asks the essential next question:

> Can the next existential projection be executed directly on the quotient, without reconstructing the original DAG?

The first frozen scope is deliberately narrow: every quotient factor is a signed **root literal**.  No factor is an opaque function of multiple remaining roots.

Within this language, direct sequential closure is exact and elementary.  The point of the gate is to prove and account it explicitly, so the next unresolved boundary is isolated at nonliteral factor objects rather than hidden in a wrapper.

---

## 1. Frozen quotient language

A state is one of:

```text
TRUE
FALSE
LITERAL_FACTOR_SET(S)
```

where `S` is a canonical finite set of signed root literals such as

```text
{x, ~y, z, ...}
```

with exact variable IDs and at most one copy of each signed literal.

Its semantics is

```text
VALUE(S) = AND_{l in S} l.
```

The empty set denotes `TRUE`.

A state containing both `v` and `~v` is semantically `FALSE`; the verifier may normalize it to the terminal FALSE object using the exact complement law.

This is an extension of U1-L2C by two terminal constants and the literal-complement contradiction rule.  It is not a general B2 factor language.

---

## 2. Direct existential update

For projected root `x`, let

```text
p = [x in S]
n = [~x in S].
```

Exactly four cases exist.

### Case 00 — irrelevant pivot

```text
exists x VALUE(S) = VALUE(S).
```

The residual quotient is unchanged.  A witness lift may choose a deterministic default `x=0` because the obligation is independent of x.

### Case 10 — positive literal

Write `S={x} union R` where R contains no literal on x. Then

```text
exists x (x AND VALUE(R)) = VALUE(R).
```

The residual quotient is R and witness lift fixes `x=1`.

### Case 01 — negative literal

Similarly

```text
exists x ((~x) AND VALUE(R)) = VALUE(R),
```

with witness lift `x=0`.

### Case 11 — contradictory pivot

```text
x AND ~x = FALSE
```

for both values of x, hence

```text
exists x VALUE(S) = FALSE.
```

No satisfying witness exists.

These four equations are the complete update theorem for the frozen language.

---

## 3. Sequential-closure theorem C1.1

After projecting any root `x`, the output is again one of

```text
TRUE
FALSE
LITERAL_FACTOR_SET(R).
```

Therefore the same update theorem applies to the next root without decompression.

For an input with `n` distinct root variables and `L` signed literals, a simple deterministic sequence that scans the current factor set at every projection performs at most

```text
O(nL)
```

literal inspections and stores at most `O(L+n)` state plus witness bits, hence polynomial in the explicit input size.

A direct indexed implementation is linear or near-linear overall, but the conservative `O(nL)` bound is sufficient.

Thus the frozen literal-factor quotient language is **closed under arbitrary sequential existential projection with polynomial state/work**.

This is a restricted-language theorem, not a theorem for arbitrary CNF/B2 states.

---

## 4. Witness theorem C1.2

On every SAT-preserving update:

- positive pivot records `x=1`;
- negative pivot records `x=0`;
- irrelevant pivot records deterministic default `x=0`;
- FALSE has no witness.

Reverse replay of these recorded bits reconstructs a full root assignment satisfying the original literal conjunction whenever terminal TRUE is reached.

Every restored bit is checked against the original signed-literal factor set.  No guessed witness is accepted without replay.

---

## 5. Certificate

Each update certificate contains:

- source factor-set fingerprint;
- projected root ID;
- exact membership flags `(p,n)`;
- target object and fingerprint;
- witness-lift bit when SAT-compatible;
- source/target serialized bytes;
- literal inspections and update operations.

The independent verifier recomputes `(p,n)` from source factors and replays the corresponding one of the four frozen identities.

---

## 6. Positive fixtures frozen before provider

The provider must include exact symbolic fixtures for:

1. irrelevant pivot;
2. positive-only pivot;
3. negative-only pivot;
4. contradictory pivot `{x,~x}`;
5. one-factor state projecting to TRUE;
6. already TRUE;
7. already FALSE;
8. the `SF_4(m)` U1-L2C target factor sets for `m in {2,4,8,16,32,64,128}`, projected all the way to terminal by a deterministic root order.

For every SAT fixture, replay the recovered assignment against the original factor set.

---

## 7. Mandatory refusal boundary

A factor which syntactically advertises dependency on projected root `x` but is not the literal `x` or `~x`, for example an opaque factor object `g(x,y)`, is outside this theorem.

The provider must return

```text
REFUSE_NONLITERAL_PIVOT_DEPENDENT_FACTOR
```

rather than treat it as irrelevant or expand it.

This refusal is the exact next research debt.

---

## 8. Claim ledger

A successful provider may establish:

```text
LITERAL_ACI_QUOTIENT_DIRECT_EXISTENTIAL_UPDATE = PROVED_IN_SCOPE
LITERAL_ACI_QUOTIENT_SEQUENTIAL_CLOSURE = PROVED_IN_SCOPE
LITERAL_ACI_QUOTIENT_POLY_TOTAL_STATE_WORK = PROVED_IN_SCOPE
LITERAL_ACI_QUOTIENT_WITNESS_LIFT = PROVED_IN_SCOPE
```

It must not establish:

```text
NONLITERAL_FACTOR_PROJECTION = PROVED
ARBITRARY_B2_SEQUENTIAL_CLOSURE = PROVED
UNIVERSAL_CREATE_GRAMMAR = PROVED
P_EQUALS_NP = PROVED
```

---

## 9. Next gate

If C1 passes, the active front moves to the smallest factor language strictly beyond signed literals:

```text
U1-L2C2 CERTIFIED NONLITERAL FACTOR PROJECTION
```

The first target should be a factor object with a small exact interface to the projected root, not an unrestricted arbitrary circuit.  Candidate languages must be chosen by exact syntactic/proof-carrying predicates and must remain closed under the next update.

```text
P_VS_NP = OPEN
```
