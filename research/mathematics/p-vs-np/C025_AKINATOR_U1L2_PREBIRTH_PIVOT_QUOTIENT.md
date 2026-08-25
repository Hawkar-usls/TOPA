# C025 — Akinator U1-L2A: prebirth pivot quotient and the sequential-closure debt

Status: **UNIVERSAL_ONE_CNF_PIVOT_COMPRESSION_PROVED / SEQUENTIAL_CLOSURE_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why this node exists

U1-H shows that generic Shannon projection is exact but can double a B2 circuit at every eliminated variable.  
MACRO-RESTORE-CAP proves that add-only extension definitions cannot erase an already-existing Davis–Putnam root-resolvent frontier.  
U1-L1 shows that low induced width is exploitable but not universal in the original graph.

The missing CREATE operation must therefore act **before** the expensive resolvents are materialized and must change the representation rather than merely append names.

For a single CNF pivot there is an exact universal factorization that does exactly this.

---

## 1. Frozen pivot decomposition

Let a CNF `F` and pivot `x` be written canonically as

```text
F = R
    AND_i (x OR A_i)
    AND_j (~x OR B_j),
```

where `R` contains no occurrence of `x`, and every `A_i`,`B_j` is the corresponding pivot clause with the pivot literal removed.

Define

```text
A := AND_i A_i
B := AND_j B_j.
```

Empty conjunction is TRUE.

---

## 2. Theorem PQ1 — universal one-pivot prebirth quotient

```text
exists x F  <=>  R AND (A OR B).
```

### Proof

For `x=0`, every negative pivot clause `(~x OR B_j)` is true and every positive pivot clause reduces to `A_i`. Hence

```text
F[x=0] = R AND A.
```

For `x=1`, every positive pivot clause is true and every negative pivot clause reduces to `B_j`. Hence

```text
F[x=1] = R AND B.
```

Therefore

```text
exists x F
= F[x=0] OR F[x=1]
= (R AND A) OR (R AND B)
= R AND (A OR B).
```

QED.

No semantic equivalence oracle is used; the proof follows only from the explicit pivot partition.

---

## 3. Construction cost

The object

```text
PQ_x(F) := (R, AND(A_i), AND(B_j), OR-root)
```

can be built by one deterministic scan of the explicit CNF plus linear-size gate/list construction.

With persistent references to unchanged clauses/subgraphs:

- pivot partition discovery is `O(literal_volume(F))`;
- no `P_x x N_x` pair enumeration is required;
- no resolvent is born;
- serialized quotient payload is linear in the pivot-local input plus references to `R`;
- witness lift stores one chosen branch bit for `x` once a model of the quotient is obtained.

Thus the *single CNF pivot* admits a direct proof-carrying prebirth quotient even when Davis–Putnam would enumerate `|P_x|*|N_x|` parent pairs.

This is a stronger one-step representation statement than add-only extension and a more source-sensitive construction than naive full-circuit Shannon copying.

---

## 4. Exact witness lift

Given an assignment `alpha` satisfying

```text
R AND (A OR B),
```

choose deterministically:

```text
if A(alpha)=TRUE: x:=0
else:             x:=1.
```

If the first branch is selected, all positive pivot clauses are satisfied by `A_i(alpha)` and all negative pivot clauses by `~x=1`.

Otherwise quotient satisfaction implies `B(alpha)=TRUE`; with `x=1`, all negative pivot clauses are satisfied by `B_j(alpha)` and all positive clauses by `x=1`.

So a quotient witness lifts to a source witness in polynomial time.

---

## 5. Why this is not P=NP

After one step, the state is generally not CNF:

```text
R AND (A OR B).
```

Applying the same construction to another variable `y` is no longer the same CNF pivot partition problem.

A generic quantifier-free circuit projection returns to the U1-H recurrence:

```text
C' = C[y=0] OR C[y=1],
```

and may duplicate the `y`-dependent region.

Therefore:

```text
LINEAR_ONE_PIVOT_QUOTIENT != POLYNOMIAL_SEQUENTIAL_CLOSURE.
```

The exact unpaid term is not the first resolvent frontier. It is the growth of **distinct restricted descendants** of the factorized DAG over successive projections.

---

## 6. Selective-copy accounting

For a quantifier-free proof-carrying DAG `C`, let `Dep_y(C)` be the set of explicit nodes whose Boolean value depends syntactically on root `y` under the frozen dependency graph.

A purely syntactic two-cofactor constructor can reuse every node outside `Dep_y(C)` and needs at most two restricted descendants for a node inside it.

Thus a conservative implementation has the local upper bound

```text
size(PROJECT_y(C)) <= size(C) + |Dep_y(C)| + O(1)
```

when one original dependent version can be reused as one restricted version, or the looser representation-independent baseline

```text
size(PROJECT_y(C)) <= 2*size(C) + O(1).
```

This accounting uses no semantic merge. It identifies the concrete object that must be amortized or quotiented.

Important: small `Dep_y` is a positive control, not a universally proved property.

---

## 7. Cofactor-diversity debt

Across a projected block `X`, one explicit DAG node can in principle acquire multiple syntactically distinct restricted descendants indexed by assignments to projected variables in its support.

Define the **certified restricted-descendant set** only from actually constructed, hash-consed, proof-carrying descendants; do not identify semantically equivalent descendants without a certificate.

The universal CREATE problem can therefore be sharpened to:

> construct exact quotient/replacement certificates before restricted-descendant diversity becomes superpolynomial.

This connects U1-L2 to the older semantic-cut / PS-width / symbolic-factor line, but with one crucial difference:

- `DISCOVER` asks for low-width structure already present in a representation;
- `CREATE` must perform a proof-carrying replacement that changes the representation so that the next exact projection interface stays polynomial.

---

## 8. Anti-circularity firewall

The following do not close this gate:

1. storing `exists y C` as a wrapper;
2. assuming a small equivalent circuit exists;
3. semantic hash-consing by unrestricted circuit equivalence;
4. enumerating all polynomial-size replacement blocks;
5. choosing a replacement by SAT/#SAT/model-count score;
6. finite holdout success;
7. simply adding extension definitions while retaining the old expensive frontier.

Each is already blocked elsewhere in U1-E/U1-H/U1-I3/U1-K/MACRO-RESTORE-CAP.

---

## 9. New exact gate — U1-L2B certified prebirth diversity contraction

For every admissible high-width state `S`, before a projection would create a superpolynomial restricted-descendant frontier, deterministically construct in polynomial time a proof-carrying replacement `T` such that:

1. `T` is quantifier-free;
2. `T` is exactly equivalent to the required existential projection/replacement;
3. `|T| + proof_bytes(T) <= N^c` for one fixed universal `c`;
4. construction + failed-search + verification work is globally `N^O(1)`;
5. no unrestricted semantic-equivalence oracle is used;
6. `T` is valid input to the same CREATE/EXPLOIT grammar;
7. a polynomial-range certified rank decreases, or a certified `O(log N)` exact projection interface is exposed;
8. witness lifting remains polynomial;
9. the guarantee holds under sequential projection for arbitrary CNF source.

This is the first currently active subgate of `U1-L2 CREATE`.

---

## 10. Claim ledger

```text
UNIVERSAL_SINGLE_CNF_PIVOT_PREBIRTH_QUOTIENT      = PROVED
SINGLE_PIVOT_DISCOVERY                            = LINEAR_IN_EXPLICIT_SOURCE
SINGLE_PIVOT_RESOLVENT_PAIR_ENUMERATION_REQUIRED = FALSE
SINGLE_PIVOT_WITNESS_LIFT                         = POLYNOMIAL
ADD_ONLY_EXTENSION_AS_REPAIR                      = ALREADY_REFUTED
SEQUENTIAL_QUANTIFIER_FREE_CLOSURE                = OPEN
UNIVERSAL_CERTIFIED_DIVERSITY_CONTRACTION         = OPEN
P_VS_NP                                            = OPEN
```

## 11. JANUS law

`COMPRESS_THE_PIVOT_PAIR_RELATION_BEFORE_RESOLVENT_BIRTH; THEN_CHARGE_THE_NUMBER_OF_DISTINCT_DESCENDANTS_THAT_SURVIVE_THE_NEXT_PROJECTION.`
