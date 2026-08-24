# C025-E2R-L1G — Expansion entropy and monotone-crossing frontier

**Status:** `MONOTONE_CROSSING_POLY_ELIMINATION_PROVED__PROVIDER_PASS`; generic polynomial elimination remains `REFUTED_BY_PARITY`.

**Scope firewall:** this studies the structure required for crossing extensions to beat the NW-local heavy-width lower bound. It does not lower-bound unrestricted Extended Resolution.

## 1. Why the generic factor 2^t cannot simply be replaced by poly(t)

Treat root and NW-local extension literals as local atoms. For a literal `ell`, let `CNFEXP(ell)` denote its exact canonical local-CNF expansion.

For a local atom `u`:

```text
CNFEXP(u)  = {{u}}
CNFEXP(~u) = {{~u}}.
```

For `e <-> (a AND b)`, positive AND is additive while a negated AND can create a Cartesian-product expansion after distribution. Define the analytical expansion entropy

```text
Phi(ell) = log2(max(1, |CNFEXP(ell)|)).
```

This is not a solver primitive.

Frozen B2 computes an `n`-bit parity prefix with exactly `3(n-1)` AND-extension gates:

```text
t1 = y AND x
t2 = (~y) AND (~x)
y' = (~t1) AND (~t2).
```

Yet the exact root-only CNF for positive parity has `2^(n-1)` width-`n` clauses. Therefore a linear-size extension DAG can have exponential exact-CNF expansion.

```text
GENERIC_CROSSING_ELIMINATION_OVERHEAD = poly(t)
```

is false as a universal syntactic-expansion statement.

## 2. Crossing-monotone restriction

A crossing skeleton is **crossing-monotone** when every crossing extension variable used as an operand of another crossing extension occurs positively. Negated root or NW-local literals remain allowed.

Therefore every crossing macro flattens to a conjunction of signed local literals:

```text
e = l1 AND ... AND lr.
```

After duplicate deletion, the number of distinct leaves is polynomial in the explicit proof/certificate volume `S`.

For such a macro:

```text
CNFEXP(e)  = {{l1},...,{lr}}
CNFEXP(~e) = {{~l1 OR ... OR ~lr}}.
```

An ER3 line contains at most three literals. If it contains positive crossing macros `e_1,...,e_p`, `p<=3`, then

```text
|CNFEXP(C)| <= product_j leaves(e_j) <= poly(S).
```

The product is an **upper bound**, not necessarily equality: overlapping macro leaves can canonicalize different Cartesian choices to the same clause.

## 3. Resolution simulation

For a crossing pivot `e=l1 AND ... AND lr`, the parents

```text
A OR e
B OR ~e
```

expand to

```text
A OR l1
...
A OR lr
B OR ~l1 OR ... OR ~lr.
```

Resolve successively on `l1,...,lr`; after `r` steps obtain `A OR B`.

When the contexts contain other crossing-monotone macros, perform the construction for each member of their polynomially bounded local expansions. Resolution on an already-local pivot is preserved componentwise under the same expansion. Since every source line is ER3 and each flattened leaf set has polynomial explicit size, the entire transformed derivation has size `poly(S)`.

Thus:

```text
CROSSING_MONOTONE_ER3/B2 -> LOCAL_ONLY_RESOLUTION
```

with polynomial overhead in explicit proof volume.

## 4. Consequence for the NW-parity hard family

L1E/L1F established, using Sokolov's heavy-width theorem plus the direct-CNF transfer, a superpolynomial Resolution lower bound for the corresponding NW local-functional encoding.

If the direct NW-parity family admitted a polynomial-size crossing-monotone B2/ER3 refutation, the simulation above would yield a polynomial-size local-functional Resolution refutation, contradiction.

Therefore, in this **restricted existential hard-family scope**:

```text
POLY_SIZE_CROSSING_MONOTONE_ER3_REFUTATION = IMPOSSIBLE.
```

Equivalently, any polynomial-size unrestricted escape, if it exists, must contain at least one negative dependency edge from a crossing macro into a later crossing macro.

This proves necessity of **some polarity inversion**. It does not prove that many inversions are necessary.

## 5. Preserved first CI failure

The first provider replay was intentionally preserved:

```text
run = 32747919279
job = 97497745879
conclusion = FAILURE
```

The fixture incorrectly asserted that three overlapping positive macros generated exactly `2*3*4=24` distinct clauses. Canonicalization collapses overlapping choices; the fixture actually generates 11 distinct clauses.

The mathematical claim only needs

```text
|EXP(C)| <= product_j leaves(e_j),
```

so the failure repaired an **equality overclaim** without weakening the polynomial upper-bound theorem.

Canonical failure receipt:

```text
data/TOPA-C025-E2R-L1G-FIRST-CI-FAILURE-REPAIR-2026-08-24-v1.0.json
```

## 6. Authoritative provider replay

Post-repair provider run:

```text
repo       = Hawkar-usls/Janus-Fundamentum
branch     = c025-policy0b-fair-reason
workflow   = Validate C025 Fair Scheduler and Reasons
run        = 32748097836
job        = 97498313316
conclusion = SUCCESS
```

PASS/negative gates:

```text
C025_E2R_L1G_PARITY_LINEAR_B2_GATE_COUNT                = PASS
C025_E2R_L1G_PARITY_EXACT_CNF_EXPONENTIAL               = PASS
C025_E2R_L1G_GENERIC_POLY_ELIMINATION_ROUTE             = REFUTED
C025_E2R_L1G_CROSSING_MONOTONE_ADMISSION                = PASS
C025_E2R_L1G_MONOTONE_FLATTENING                        = PASS
C025_E2R_L1G_OVERLAP_CANONICALIZATION                   = PASS
C025_E2R_L1G_ER3_MACRO_CLAUSE_POLY_UPPER_BOUND          = PASS
C025_E2R_L1G_FLATTENED_PIVOT_CHAIN                      = PASS
C025_E2R_L1G_NEGATIVE_CROSSING_DEPENDENCY_REJECTION     = PASS
```

CI checks finite mechanics; the asymptotic restricted impossibility additionally uses the established source heavy-width theorem and earlier theorem-transfer chain.

## 7. Next structural resource

The surviving escape is now sharper:

```text
cross-neighborhood mixing
        +
negative crossing dependencies
```

are both necessary for a polynomial-size escape from this restricted lower-bound route.

Freeze expansion entropy

```text
Phi(ell)=log2(max(1, |CNFEXP(ell)|)).
```

but keep the firewall:

```text
HIGH_PHI != LARGE_EXTENSION_CIRCUIT
```

because parity has high `Phi` with linear circuit size.

The next front must combine **polarity-inversion structure with NW-specific correlation/locality**, not expansion entropy alone. A useful target is a tradeoff in terms of the number/depth/placement of negative crossing edges and the amount of NW-neighborhood correlation they can create.

## 8. Exact status

```text
L1G_A_PARITY_EXPANSION_BARRIER               = PROVED
L1G_B_GENERIC_POLY_T_ELIMINATION             = REFUTED
L1G_C_MONOTONE_CROSSING_FLATTENING           = PROVED
L1G_D_MONOTONE_CROSSING_POLY_ELIMINATION     = PROVED__PROVIDER_PASS
L1G_E_MONOTONE_CROSSING_POLY_PROOF           = REFUTED_IN_RESTRICTED_HARD_FAMILY
L1G_F_POLARITY_INVERSION_X_NW_CORRELATION    = NEXT / OPEN
ISSUE_217_FULL_ER3                            = OPEN
P_VS_NP                                       = OPEN
```

## 9. Hard laws

```text
HIGH_CNF_EXPANSION != LARGE_B2_CIRCUIT
PARITY_COMPRESSION_KILLS_GENERIC_POLY_ELIMINATION
CROSSING_MONOTONE != UNRESTRICTED_CROSSING
ONE_POLARITY_INVERSION_REQUIRED != MANY_INVERSIONS_REQUIRED
EXPANSION_ENTROPY_ALONE != ER_LOWER_BOUND
RESTRICTED_NW_RESULT != FULL_ER3_LOWER_BOUND
P_VS_NP = OPEN
```
