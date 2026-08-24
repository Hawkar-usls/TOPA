# C025-E2R-L1G — Expansion entropy and monotone-crossing frontier

**Status:** `GENERIC_POLY_ELIMINATION_REFUTED`; `MONOTONE_CROSSING_POLY_ELIMINATION_CANDIDATE`.

**Scope firewall:** this studies the structure required for crossing extensions to beat the NW-local heavy-width lower bound. It does not lower-bound unrestricted Extended Resolution.

## 1. Why the generic factor 2^t cannot simply be replaced by poly(t)

Fully eliminate B2 extension variables into root/local atoms by exact CNF substitution.

For a literal `ell`, let `CNFEXP(ell)` be the canonical clause set for the Boolean function represented by `ell`, treating root and NW-local extension literals as atoms.

For a local atom `u`:

```text
CNFEXP(u)  = {{u}}
CNFEXP(~u) = {{~u}}.
```

For

```text
e <-> (a AND b)
```

we have the exact distributive recurrences before semantic subsumption:

```text
CNFEXP(e)  = CNFEXP(a) union CNFEXP(b)
CNFEXP(~e) = CNF( (~a) OR (~b) )
           = {A union B : A in CNFEXP(~a), B in CNFEXP(~b)}.
```

Thus positive AND is additive in clause count, while negating an AND can make clause sets multiply after later polarity changes.

Define the syntactic expansion entropy

```text
Phi(ell) = log2(max(1, |CNFEXP(ell)|)).
```

This is an analysis measure, not a solver primitive.

## 2. Parity barrier

Frozen B2 can update a parity prefix `y` with a new atom `x` using three AND extensions:

```text
t1 = y AND x
t2 = (~y) AND (~x)
y' = (~t1) AND (~t2)
```

The new output is `y XOR x`.

Starting with `y=x1`, parity on `n` atoms therefore uses exactly

```text
3(n-1)
```

B2 extension gates.

But the exact root-only CNF for the positive parity literal contains

```text
2^(n-1)
```

width-`n` clauses, one forbidding each assignment of the wrong parity.

Hence an `O(n)`-gate B2 circuit can have exact CNF expansion `2^Omega(n)`.

### Barrier L1G.1

```text
GENERIC_CROSSING_ELIMINATION_OVERHEAD = poly(t)
```

is false as a universal syntactic-expansion claim.

The previous `2^t` elimination theorem is therefore qualitatively consistent with real extension compression; one cannot remove its exponential nature without using additional crossing-circuit structure.

## 3. Monotone-crossing restriction

Call a B2 crossing skeleton **crossing-monotone** if every occurrence of a crossing extension variable as an operand of another crossing extension is positive.

Negations of root or already NW-local literals are allowed and remain local atoms. The restriction forbids only edges

```text
parent crossing gate <- (~child_crossing).
```

Under this restriction every crossing variable is semantically a conjunction of local literals:

```text
e = l1 AND l2 AND ... AND lr
```

for some local literals `li`.

Let `leaves(e)` be the number of distinct local leaf occurrences after flattening and canonical duplicate deletion. For a proof with `t` crossing definitions,

```text
leaves(e) <= t+1 + O(local direct operands).
```

Relative to the explicit proof/certificate size, this is polynomial.

## 4. CNF expansion under crossing monotonicity

For a flattened conjunction `e = AND_i li`:

```text
CNFEXP(e)  = {{l1},...,{lr}}
CNFEXP(~e) = {{~l1 OR ... OR ~lr}}.
```

So:

```text
|CNFEXP(e)|  = r,
|CNFEXP(~e)| = 1.
```

An original ER3 proof clause has at most three literals. If it contains `p<=3` positive crossing literals, full local expansion distributes across at most those `p` conjunctions, giving at most

```text
prod_j leaves(e_j) <= (S+1)^3
```

clauses when `S` is total explicit proof/certificate volume. Negative crossing literals do not branch.

## 5. Resolution simulation for a flattened crossing pivot

Suppose a crossing pivot represents

```text
e = l1 AND ... AND lr.
```

The two parent clauses

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

Resolve the last clause successively with `A OR l1`, ..., `A OR lr`. After `r` ordinary Resolution steps the result is

```text
A OR B.
```

When `A` and `B` contain other crossing-monotone macros, perform this construction for every combination in their polynomial-size expansions. Since the original proof is ER3, each source line has at most three macro literals, and each pivot simulation has polynomial overhead in the explicit proof volume.

Thus a crossing-monotone ER3/B2 refutation of total explicit size `S` can be converted into a local-only Resolution refutation of size `poly(S)`.

## 6. Consequence for the NW-parity hard family

The L1E/L1F direct NW-parity family has a superpolynomial local-functional Resolution lower bound in its explicit input length `N`.

If there were a polynomial-size crossing-monotone B2/ER3 refutation, then `S=poly(N)` and the polynomial elimination above would give a polynomial-size local-functional Resolution refutation, contradicting the source heavy-width lower bound.

Therefore, in the stated existential hard-family scope:

```text
POLY_SIZE_CROSSING_MONOTONE_ER3_REFUTATION = IMPOSSIBLE.
```

Equivalently, every polynomial-size unrestricted escape must contain at least one **polarity-inverting crossing dependency**.

This does not say that one inversion is enough, nor does it lower-bound the number of such inversions.

## 7. Next structural resource

The surviving escape is not merely crossing; it is crossing plus enough polarity structure to generate large CNF expansion.

Freeze:

```text
Phi(ell) = log2 |CNFEXP(ell)|
```

and call a crossing literal **high-expansion** when `Phi` is superlogarithmic in the input length.

The next question is:

> must every polynomial-size ER3 refutation of the hard family synthesize a crossing literal with very large `Phi`, and can NW-specific heavy-width/correlation restrict how cheaply such a literal can be built or used?

Parity proves that large `Phi` alone does not imply large circuit size, so any successful next invariant must combine expansion entropy with NW-specific correlation/locality information.

## 8. Exact gates

```text
L1G_A_PARITY_EXPANSION_BARRIER               = PROVED_ANALYTICALLY
L1G_B_GENERIC_POLY_T_ELIMINATION             = REFUTED
L1G_C_MONOTONE_CROSSING_FLATTENING           = PROVED
L1G_D_MONOTONE_CROSSING_POLY_ELIMINATION     = CLAIM_PENDING_PROVIDER_REPLAY
L1G_E_MONOTONE_CROSSING_POLY_PROOF           = REFUTED_IF_D_PASSES
L1G_F_EXPANSION_ENTROPY_X_NW_CORRELATION     = NEXT
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
P_VS_NP = OPEN
```
