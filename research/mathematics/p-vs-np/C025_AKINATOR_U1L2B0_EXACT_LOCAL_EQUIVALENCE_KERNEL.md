# C025 — Akinator U1-L2B0: exact local equivalence kernel

Status: **FROZEN_PROTOCOL / PROVIDER_PENDING**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-L2A proves that one arbitrary CNF pivot can be projected without materializing its Cartesian resolvent frontier, but sequential closure can still create many distinct restricted descendants in the quantifier-free DAG.

Instead of hand-authoring another local rewrite, this gate asks JANUS to **exhaustively synthesize the complete exact rewrite catalog inside one fixed local B2 scope**.

This is not heuristic search. The local scope is constant and every semantic comparison is a complete truth-table comparison over formal boundary inputs.

---

## 1. Frozen finite scope

```text
BOUNDARY_ARITY k = 4
MAX_INTERNAL_B2_GATES g = 3
BASIS = signed-input AND
OUTPUT = signed literal of a boundary signal or internal gate
```

Each internal gate is topologically ordered and has the form

```text
e_i := lit(a) AND lit(b)
```

where `a` and `b` are distinct previously available signal IDs and either input may be negated.

Only circuits whose advertised output reaches every serialized internal gate are admitted; decorative/unreachable gates are rejected.

The provider must enumerate **all** admitted circuits with 0..3 internal gates in this frozen scope.

---

## 2. Exact semantics

For every admitted circuit `C`, compute its complete Boolean truth table on the four formal boundary variables:

```text
TT(C) in {0,1}^{16}.
```

Two fragments are equivalent iff their 16-bit tables are byte-equal:

```text
C1 == C2  iff  TT(C1) = TT(C2).
```

Because the inputs are formal Boolean variables, equality of all 16 rows proves the propositional identity. Therefore the identity remains valid after arbitrary substitution of the four formal inputs by Boolean signals/functions in a larger DAG.

No input-sized SAT/equivalence oracle is used.

---

## 3. Projection-aware local cost

For each formal projected boundary variable `x_p`, compute the **syntactic dependency flag** of every internal gate recursively:

```text
dep_p(boundary_i) = (i == p)
dep_p(NOT s)      = dep_p(s)
dep_p(a AND b)    = dep_p(a) OR dep_p(b).
```

Define

```text
AC_p(C) = number of reachable internal gates with dep_p = TRUE.
G(C)    = number of reachable internal gates.
```

The canonical representative for `(TT, p)` is the lexicographic minimum under

```text
(AC_p(C), G(C), canonical_encoding(C)).
```

A runtime replacement from source fragment `C` to catalog representative `C*` is admissible only if

```text
TT(C*) = TT(C)
AND G(C*) <= G(C)
AND [AC_p(C*) < AC_p(C) OR G(C*) < G(C)].
```

Thus the kernel never increases local gate count and every accepted rewrite has an explicit strict local improvement.

---

## 4. Deterministic catalog construction

The provider must enumerate circuits in one frozen lexical order. It may not stop after finding a good representative.

For every `(truth_table, projected_variable)` class, retain the exact canonical minimum under the frozen tuple above.

Required immutable outputs:

- number of admitted circuits;
- number of distinct Boolean functions reached;
- number of `(function,p)` canonical classes;
- number of source circuits having a strict admitted replacement;
- canonical serialized catalog;
- SHA-256 of the catalog;
- several replayed replacement certificates chosen by lexical order, not by aesthetic interest.

---

## 5. Complexity theorem in frozen scope

`k=4` and `g=3` are universal constants independent of source input size `N`.

Therefore:

- complete catalog generation is constant work with respect to `N`;
- complete truth-table equivalence checking is constant work per catalog item;
- the resulting catalog is a fixed finite object;
- matching a bounded fragment at runtime can be done by deterministic enumeration of at most `O(S^g)` candidate fragments in an explicit DAG of size `S`, hence polynomial because `g` is fixed;
- each accepted rewrite is exactly verified by a fixed identity certificate.

This establishes polynomial **admissibility** of the local kernel. It does not establish universal usefulness or polynomial global projection state.

---

## 6. Global saturation discipline

A future runtime saturator may apply the catalog only under all conditions:

1. fixed deterministic fragment enumeration order;
2. exact match to a catalog identity;
3. no semantic input-sized equivalence call;
4. no gate-count increase;
5. strict decrease of the declared local affected-cone cost or gate count;
6. full cost ledger charged;
7. Hephaestus hash recorded before and after replacement;
8. no claim that local normal form is globally optimal.

If a global implementation uses a potential, it must separately prove that replacements cannot increase the chosen global potential through ancestor rewiring. That theorem is **not** assumed here.

---

## 7. What this can discover

The finite kernel can rediscover known Boolean identities and may find structurally awkward identities that are easy for exhaustive enumeration but easy for a human to overlook.

Any such identity becomes a theorem only because its complete formal truth table was checked, not because it improved a benchmark.

The scientifically interesting question is whether the exact catalog repeatedly contracts the `Dep_x` frontier created after U1-L2A prebirth projection.

---

## 8. What this cannot prove

Even a perfect local catalog for this scope does not prove:

- every arbitrary circuit has an improving 3-gate window;
- local saturation reaches polynomial projection width;
- larger/global equivalences have short local derivations;
- the number of global saturation steps is polynomial without a separate global potential theorem;
- `P=NP`.

A family with no improving admitted local window is a valid escape receipt, not a failure to be hidden.

---

## 9. Next gate after provider

If provider replay succeeds, the next gate is:

`U1-L2B1 EXACT LOCAL SATURATION ON PREBIRTH-PROJECTION DAGs`

with a frozen global potential/accounting contract and adversarial escape families.

If the kernel has no nontrivial affected-cone contractions, record that negative result and do not proceed to saturation.

```text
P_VS_NP = OPEN
```
