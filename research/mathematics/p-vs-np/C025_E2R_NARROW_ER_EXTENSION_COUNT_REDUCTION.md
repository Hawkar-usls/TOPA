# C025-E2R — Narrow-ER extension-count reduction

**Status:** `REDUCTION_PROVED`, conditional on the standard theorem that Narrow Extended Resolution `ER3` p-simulates Extended Resolution.

**Purpose:** replace the vague global resource "proof size" by a sharper equivalent existential resource: the number of extension variables needed in a width-3 Extended-Resolution refutation.

**Claim ceiling:** this does not prove that the extension count is polynomial or superpolynomial. It proves that such a bound is enough, and in the global p-boundedness question is equivalent up to polynomial transformations.

## 1. External normalization theorem

Narrow Extended Resolution `ER3` is the restriction of Extended Resolution in which every derived resolvent has width at most 3. Prcovic proved that `ER3` p-simulates unrestricted Extended Resolution.

Thus any polynomial-size ER/B2 refutation can be transformed in polynomial time into a polynomial-size `ER3` refutation.

## 2. Clause-universe lemma

Let a root CNF `F` have:

- encoded length `N`;
- `n0` root variables, with `n0 <= N`;
- `m` root clauses, with `m <= N` under any ordinary explicit encoding;
- an `ER3` refutation using `K` fresh extension variables.

Let

```text
V = n0 + K.
```

Each extension contributes exactly three definitional clauses of width at most 3.

Every non-axiom Resolution-derived clause in `ER3` has width at most 3. The number of distinct non-tautological clauses of width at most 3 over `V` variables is at most

```text
1 + 2V + C(2V,2) + C(2V,3) = O(V^3),
```

and the true number is smaller because clauses containing both `x` and `~x` are tautological and excluded.

Therefore the entire set of possible distinct narrow derived clauses is polynomial in `V`.

## 3. Duplicate-elimination lemma

Take any finite `ER3` refutation over a fixed topologically ordered set of `K` extension definitions.

For every derived clause, retain its earliest occurrence. If the same clause is derived again later, redirect all later uses to the earliest occurrence. The earliest derivation's parents occur before it (or are axioms), so this redirection preserves acyclicity and validity.

Thus there exists a DAG refutation with at most one node per distinct derived clause, plus root and extension axioms.

Hence an `ER3` refutation using `K` extensions can be compressed to size

```text
O(m + K + V^3)
= O(N + K + (N+K)^3).
```

The exact byte encoding contributes only the ordinary logarithmic identifier factors.

## 4. Extension-count sufficiency theorem

If there are constants `c,N0` such that every UNSAT CNF of encoded length `N >= N0` has **some** `ER3` refutation using

```text
K(F) <= N^c
```

extension variables, then every such CNF has a polynomial-size B2/ER certificate.

Proof: substitute `K <= N^c` into the compressed-size bound above. Since B2 and ER are p-equivalent and `ER3` is an ER subsystem, the resulting certificate size is polynomial in `N`. □

## 5. Necessity under global E2

Conversely, suppose global E2 is positive: every UNSAT CNF of length `N` has a B2/ER refutation of size `poly(N)`.

By `ER3 p-simulates ER`, transform that proof into a polynomial-size `ER3` refutation. Such a refutation can contain at most polynomially many extension-definition steps, hence uses at most polynomially many extension variables.

Therefore universal polynomial B2/ER proof size implies a universal polynomial bound on `K` in some `ER3` refutation.

## 6. Equivalence

Up to the standard polynomial proof translations:

```text
GLOBAL_E2_P_BOUNDEDNESS
<=poly=> UNIVERSAL_POLY_ER3_EXTENSION_COUNT
<=poly=> GLOBAL_E2_P_BOUNDEDNESS.
```

So the proof-size gate can be refactored as:

```text
C025_E2R_EXTENSION_COUNT:
Does every UNSAT CNF F of length N admit some ER3 refutation
with K(F) <= N^c for one fixed c?
```

This is still a major open strong-proof-system question, but it is now a single explicit structural resource rather than an undifferentiated proof-size statement.

## 7. Why this matters for Policy-0B

Policy-0B no longer needs to treat all proof bytes as the first existential bottleneck.

The hierarchy becomes:

```text
E2R-A  extension-count existence       OPEN
E2R-B  narrow-clause DAG size          POLY GIVEN K=POLY(N)
E2R-C  certificate verification        PROVED POLY IN CERT SIZE
C2     extension discovery/search      DEFERRED UNTIL EXISTENCE TARGET IS UNDERSTOOD
#212   active representation           STILL OPEN FOR THE ACTUAL SOLVER
```

A counterfamily forcing superpolynomial `K` in every `ER3` refutation would refute global E2 and yield the corresponding ER/EF lower-bound breakthrough. A polynomial universal `K` theorem would imply `NP = coNP` via polynomially verifiable UNSAT certificates, but would still not provide a deterministic polynomial SAT algorithm without C2.

## 8. Next direct attack

Do not search blindly over all extension formulas. Attack the extension-count resource itself:

1. identify known ER-hard candidate families and strong lower-bound surrogates;
2. search for invariants preserved by a single extension variable;
3. ask whether one extension can collapse more than polynomially many distinguishable residual/communication states;
4. construct guarded/adversarial families where useful abbreviations require many mutually independent extension variables;
5. separately test restricted extension depths/fanout to obtain unconditional lower bounds without confusing them with full ER.

## 9. Status

```text
C025_E2A_B2_ER_P_EQUIVALENCE            = PROVED
C025_E2R_ER3_NORMALIZATION              = EXTERNAL_THEOREM
C025_E2R_CLAUSE_UNIVERSE_BOUND          = PROVED
C025_E2R_DUPLICATE_ELIMINATION          = PROVED
C025_E2R_POLY_K_IMPLIES_POLY_PROOF      = PROVED
C025_E2R_GLOBAL_EQUIVALENCE             = PROVED
C025_E2R_UNIVERSAL_POLY_EXTENSION_COUNT = OPEN
P_VS_NP                                 = OPEN
```
