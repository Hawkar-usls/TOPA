# C025-E2R-L1 — Support-local ER3 restricted frontier

**Status:** `OPEN_RESTRICTED_FRONTIER__MECHANICS_PROVED`.

This is a deliberately restricted testbed after the naive class-count invariant was refuted.

## 1. Definition

For root literal `x`, set

```text
support(x)={x}.
```

For each frozen B2 definition

```text
e_i <-> (a_i AND b_i)
```

set

```text
support(e_i)=support(a_i) union support(b_i).
```

A proof is `kappa-local` if every extension variable satisfies

```text
|support(e_i)| <= kappa.
```

The initial regime is `kappa=O(log N)`.

## 2. What provider replay now proves

The support calculator/verifier is executable and provider-CI green. The frozen mechanics establish:

- exact transitive root-support computation;
- polarity invariance of support;
- rejection of forward dependencies;
- exact `kappa`-local admission;
- root-restriction support monotonicity;
- preservation of `kappa`-locality under partial assignments to root variables.

Authoritative replay:

```text
repo = Hawkar-usls/Janus-Fundamentum
branch = c025-policy0b-fair-reason
workflow = Validate C025 Fair Scheduler and Reasons
run = 32728789959
job = 97436024608
conclusion = SUCCESS
```

## 3. Root-restriction theorem

Let `rho` be a partial assignment to root variables. Every extension denotes a deterministic Boolean function of the roots in its transitive support. After substituting `rho`, a residual extension function can depend only on unassigned roots it depended on before. Therefore

```text
S_rho(e) subseteq S(e) minus dom(rho).
```

Constant folding, aliasing and Boolean simplification can remove additional dependencies but cannot create a new root dependency.

Hence

```text
|S(e)| <= kappa  =>  |S_rho(e)| <= kappa.
```

So the restriction is stable under root restrictions. This is the first property needed by any restriction/heavy-width style lower-bound attempt.

## 4. Direct NW-transfer attempt failed cleanly

Sokolov's functional Nisan-Wigderson encoding uses a stronger graph-local notion: a local function must depend only on variables contained in one fixed neighborhood

```text
Vars_i = N(v_i).
```

Cardinality locality does not imply this.

Example:

```text
Vars_1={x1,x2}
Vars_2={x3,x4}
kappa=2
support(e)={x1,x3}.
```

Then `e` is `kappa`-local by cardinality but lies in no one NW neighborhood.

Therefore

```text
KAPPA_LOCAL -> SOKOLOV_NW_LOCAL
```

is `REFUTED`.

## 5. Refined NW-neighborhood-local subregime

Call an extension `NW-local` when

```text
support(e) subseteq Vars_i
```

for at least one fixed neighborhood `Vars_i`.

For conjunction closure the two operands must be local in the **same** neighborhood:

```text
exists i: support(a) union support(b) subseteq Vars_i.
```

It is not enough that `a` and `b` are separately local somewhere.

Under this same-neighborhood condition, if local functions `g,h` are represented and `s=g AND h`, Sokolov's functional encoding contains the clauses

```text
(~y_s OR y_g)
(~y_s OR y_h)
(y_s OR ~y_g OR ~y_h),
```

which are exactly the frozen B2 extension clauses. Thus extension-axiom compatibility is proved **conditional on the source collection G containing the functions used by the B2 proof**.

## 6. What is NOT transferred

The heavy-width lower bound is not yet available to us. Matching three extension clauses is insufficient because the functional encoding is a richer semantic object and may contain additional clauses among selected local functions.

A full transfer requires:

```text
ROOT_FORMULA_MAP
PROOF_LITERAL_FUNCTION_MAP
FUNCTION_COLLECTION_SIZE_ACCOUNTING
RESOLUTION_STEP_PRESERVATION
RESTRICTION_CORRESPONDENCE
ER3_WIDTH_ACCOUNTING
```

Until those are established, Sokolov is `INSPIRATION_ONLY` for our ER3 restriction.

## 7. Current gates

```text
L1-A support calculator / verifier                        = PROVED_IN_SCOPE / PROVIDER PASS
L1-B root-restriction locality stability                  = PROVED / PROVIDER PASS
L1-C1 kappa-local -> NW-local direct transfer             = REFUTED / PROVIDER PASS
L1-C2 same-neighborhood extension-axiom compatibility     = PROVED CONDITIONAL ON G
L1-C3 full functional-encoding proof transfer             = OPEN ACTIVE
L1-D heavy-width transfer                                 = BLOCKED BY L1-C3
L1-E explicit restricted counterfamily                    = OPEN
```

## 8. Exact restricted target remains

Find an explicit polynomial-size UNSAT CNF family `F_N` such that every proof in a fully specified local ER3 restriction either

1. uses superpolynomially many extension variables, or
2. does not exist inside that restriction.

Any such result is restriction-only unless a separate theorem upgrades it.

## 9. Hard boundaries

```text
MANY_CLASSES != SUPERPOLYNOMIAL_EXTENSION_COUNT
EXPONENTIAL_FLAT_REPRESENTATION != EXPONENTIAL_EXTENSION_COUNT
KAPPA_LOCAL != NW_NEIGHBORHOOD_LOCAL
NW_LOCAL_EXTENSION_AXIOM_MATCH != HEAVY_WIDTH_THEOREM_TRANSFER
ER3[LOCAL] LOWER BOUND != FULL ER3 LOWER BOUND
P_VS_NP = OPEN
```
