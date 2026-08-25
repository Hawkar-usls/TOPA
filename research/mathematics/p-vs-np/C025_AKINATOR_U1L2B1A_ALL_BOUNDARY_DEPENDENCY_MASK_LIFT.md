# C025 — Akinator U1-L2B1A: all-boundary dependency-mask lift

Status: **FROZEN_PROTOCOL / PROVIDER_PENDING**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Adapter debt

The frozen U1-L2B0 catalog is exact as a Boolean identity catalog. Its projection-aware cost key, however, was indexed by one designated formal projected boundary variable `p`, implicitly assigning dependency pattern

```text
D = 1 << p.
```

In an actual global DAG region, multiple boundary signals may already syntactically depend on the same root variable `x`.

Therefore the exact Boolean identity remains valid, but the old `(truth,p)` affected-cone metadata is not by itself sufficient to certify the actual global `AC_x` change under an arbitrary local embedding.

The B1 context-closed monotonicity theorem remains valid when source and target `AC_x` are recomputed using the **actual** boundary dependency bits. This gate lifts the fixed catalog so that those bits are part of the canonical key directly.

---

## 1. Frozen source algebra

Do not change the U1-L2B0 circuit universe:

```text
k = 4 formal boundary signals
g <= 3 internal signed-input AND gates
all internal gates reachable from output
complete 16-row Boolean truth table
```

The admitted circuit set must remain exactly the same 20,792 encodings produced by the frozen provider.

---

## 2. Dependency masks

For every boundary dependency mask

```text
D in {0,...,15},
```

set

```text
dep_D(b_i) = bit_i(D).
```

Propagate syntactic dependency through the local circuit by

```text
dep_D(NOT s)   = dep_D(s)
dep_D(a AND b) = dep_D(a) OR dep_D(b).
```

Define

```text
AC_D(C) = number of reachable internal gates whose propagated dependency bit is TRUE.
```

This exactly matches the dependency contribution of the local region when formal boundary `b_i` is instantiated by an outside signal that depends on global root `x` iff bit `i` of `D` is one.

---

## 3. Canonical all-mask catalog

For every pair

```text
(TT, D)
```

retain the lexicographically unique minimum circuit under

```text
(AC_D(C), G(C), canonical_encoding(C)).
```

There are at most

```text
1254 * 16
```

reachable `(function, dependency-mask)` classes in the frozen source algebra.

No new Boolean equivalence computation is required beyond the already frozen complete 16-row truth table.

---

## 4. Admitted runtime replacement

Given a context-closed local region in a global DAG and projected root `x`:

1. map its at most four ordered boundary signals to formal `b_0..b_3`;
2. compute the actual dependency mask `D` from the global DAG;
3. compute the local truth-table identity key by matching the exact frozen circuit encoding/catalog entry;
4. fetch canonical representative for `(TT,D)`;
5. admit replacement only if

```text
G(target) <= G(source)
AC_D(target) <= AC_D(source)
AND [AC_D(target) < AC_D(source) OR G(target) < G(source)].
```

Then U1-L2B1 applies directly and the global potential cannot increase.

---

## 5. Exhaustive provider obligations

The provider must:

- reuse exactly the frozen U1-L2B0 admitted circuit generator;
- enumerate all 16 masks for every admitted circuit;
- build all canonical `(TT,D)` classes;
- independently replay truth equality for every retained representative;
- report strict replacement counts by popcount of `D`;
- report same-gate strict `AC_D` contractions by popcount of `D`;
- report whether any `(TT,D)` class exhibits an `AC_D` vs gate-count Pareto tradeoff within `g<=3`;
- bind the serialized all-mask catalog to SHA-256;
- make no assertion that useful replacement must exist for every circuit/mask.

---

## 6. Complexity

`k=4`, `g=3`, and the 16 dependency masks are universal constants independent of source size `N`.

Therefore all-mask catalog synthesis remains constant work with respect to `N`, while structural runtime matching of bounded regions remains polynomial in explicit DAG size.

This is an adapter/completeness repair for the fixed local grammar, not an asymptotic SAT theorem.

---

## 7. What success would close

A successful provider closes this implementation debt:

```text
SINGLETON_BOUNDARY_DEPENDENCY_ASSUMPTION
```

for the frozen local kernel.

It would justify using the B1 global monotonicity theorem on arbitrary context-closed local embeddings with up to four boundary signals, regardless of how many of those signals already depend on `x`.

---

## 8. What remains open

Even a complete all-mask fixed catalog does not prove:

- every large affected cone contains an improving bounded closed region;
- high fanout/sharing admits a bounded closed region;
- local normal forms have small projection interfaces;
- sequential projection state stays polynomial;
- P=NP.

After this adapter repair, return to:

```text
U1-L2B2 LOCAL_NORMAL_FORM_ESCAPE_AND_COMPLETENESS_GATE
```

with sharing/fanout and large-AC normal forms as primary adversarial targets.

```text
P_VS_NP = OPEN
```
