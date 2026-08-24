# C025-E2R-L1G-F2 — Negative-edge budget to macro cut-elimination cost

**Status:** `ANALYTICAL_PROOF_V1_1_COMPLETE_PENDING_PROVIDER_REPLAY`.

**Scope firewall:** this theorem converts a bounded polarity-inversion budget into a pure-Resolution simulation bound for frozen B2/ER3 on the NW hard-family transfer. It does **not** prove a superpolynomial lower bound on total extension count, does not resolve unrestricted ER/EF p-boundedness, and does not resolve P vs NP.

## 1. Global budget

Let `q` be the number of distinct negative crossing dependency edges in the complete crossing-extension DAG and `S>=2` the explicit proof/certificate volume. F1 gives, for one crossing literal with cone budget at most `q`,

```text
|CNFEXP(ell)| <= S^((q+2)!).
```

Since the original proof is ER3, a source line has at most three literals, so a safe structural line-expansion ceiling is

```text
B_q := S^((q+3)!).
```

Use structural syntactic CNF expansion with duplicate/tautology deletion but without semantic minimization. This preserves the recursive union/product structure used below.

## 2. Pure-Resolution restriction lemma

For a partial assignment `rho`, restrict every clause in a pure Resolution proof.

### Lemma F2.1 — proof restriction

A pure Resolution refutation restricts to a pure Resolution refutation of the restricted CNF with no increase in proof nodes after deleting satisfied lines and aliasing stronger parents.

For an old inference

```text
A OR x
B OR ~x
---------
A OR B
```

after restriction either the complementary pivot survives and the restricted parents resolve, or one parent loses the pivot and already subsumes the restricted old resolvent. The empty final clause remains empty.

## 3. Pure context lifting by restrict-refute-lift

For a non-tautological clause `C`, let `rho_C` be the partial assignment that falsifies every literal of `C`.

### Lemma F2.2 — context lifting without weakening

Let `pi` be a pure Resolution refutation of `Gamma union Delta` of size `R`. Suppose the current derivation contains, for every `gamma in Gamma`, a clause contained in `gamma OR C`, and contains every `delta in Delta` (or stronger clauses).

Then pure Resolution derives a clause `C' subseteq C` with `O(R)` proof nodes.

**Proof route.**

1. Restrict the current premises by `rho_C`. Every contextual `gamma OR C` becomes a clause contained in `gamma|rho_C`; every `delta` becomes `delta|rho_C` or is satisfied.
2. By Lemma F2.1, restricting `pi` by the same `rho_C` gives a Resolution refutation of the corresponding restricted `Gamma union Delta` premises. Stronger current restricted premises can replace weaker ones by the same subsumption-preserving simulation.
3. Lift this restricted refutation back to the unrestricted current premises: every literal removed because it was falsified by `rho_C` belongs to `C`; replaying the proof while retaining original premises therefore derives a clause contained in the blocking clause for `rho_C`, hence a subclause of `C`.

This is the standard restrict-refute-lift pattern. No weakening rule is added, and no variable-disjointness assumption is used. Context, pivot variables and child cones may overlap.

## 4. Complement refutation for one macro

Use the F1 positive-closure normal form

```text
F = L AND (~F_1) AND ... AND (~F_k),
```

where `L` is a conjunction of signed root/NW-local literals, `k<=q`, and every frontier child has negative-edge budget at most `q-1`.

Let `P(F)` be structural CNF for `F` and `N(F)` structural CNF for `~F`. Then

```text
P(F) = units(L) union N(F_1) union ... union N(F_k),
```

and `N(F)` consists of Cartesian clauses

```text
neg(L) OR p_1 OR ... OR p_k,
```

with `p_j in P(F_j)`.

### Lemma F2.3 — bounded complement refutation

`P(F) union N(F)` has a pure Resolution refutation of size at most

```text
S^((q+4)!).
```

**Induction.** For `q=0`, resolve the one complement clause against at most `S` local unit clauses.

For `q>0`:

1. resolve `neg(L)` away from every clause of `N(F)` using local units;
2. obtain all clauses `p_1 OR ... OR p_k`;
3. eliminate children sequentially. For each fixed context of the other children, apply Lemma F2.2 to the inductive refutation of `P(F_j) union N(F_j)`. The `N(F_j)` clauses are already in `P(F)` and the contextual `P(F_j)` clauses are present from the Cartesian expansion, or stronger subclauses have already been derived;
4. after all children are eliminated, obtain empty.

No disjointness of child cones is assumed.

With `H(q)=(q+2)!`, a safe recurrence is

```text
R_q <= S^(H(q)+1) + q*S^H(q)*R_(q-1),
```

and with `q<=S`, `R_(q-1)<=S^((q+3)!)`, this is dominated by

```text
R_q <= S^((q+4)!).
```

## 5. One macro pivot

For an ER3 inference

```text
A OR e
B OR ~e
--------- Res(e)
A OR B
```

let `e` represent `F`. Expand the parent and target clauses over root/NW-local atoms. For every target clause `alpha OR beta`, the parent expansions provide clauses contained in

```text
alpha OR p   for every p in P(F),
beta  OR n   for every n in N(F).
```

Apply the complement refutation from Lemma F2.3 through the pure context-lifting Lemma F2.2 to derive a clause contained in `alpha OR beta`.

There are at most `B_q` target clauses for one original ER3 line. Thus one macro-pivot inference is simulated within the deliberately loose ceiling

```text
S^((q+5)!).
```

Non-macro pivots are no more expensive: corresponding expanded clauses resolve directly, and if the pivot disappears under a stronger expansion, the stronger parent subsumes the target.

## 6. Full proof simulation

### Theorem F2.4 — bounded-inversion pure-Resolution simulation

Every frozen B2/ER3 refutation of explicit volume `S>=2` and global negative crossing-edge budget `q` can be converted into a pure Resolution refutation over root/NW-local atoms of size

```text
S_local <= S^((q+5)!).
```

Identifying duplicate NW-local function variables by the already-audited literal substitution yields a Resolution refutation of the source functional encoding used by the NW heavy-width lower bound.

The factorial exponent is intentionally loose. The theorem only needs an explicit computable dependence on `q`.

## 7. NW hard-family consequence

For the polynomial-input NW-parity family from L1E/L1F, after absorbing fixed polylogarithmic losses, there is a fixed `eta>0` such that sufficiently large family members satisfy

```text
L(N) >= exp(N^eta)
```

for local-functional Resolution.

If an unrestricted B2/ER3 refutation had polynomial explicit size `S<=N^d`, then Theorem F2.4 forces

```text
(N^d)^((q+5)!) >= exp(N^eta).
```

Hence

```text
(q+5)! * O(log N) >= N^eta.
```

Using `log(r!)=Theta(r log r)`,

```text
q log q = Omega(log N),
```

so

```text
q = Omega(log N / log log N).
```

Therefore every polynomial-size unrestricted ER3/B2 escape on this existential hard family must contain a growing polarity-inversion DAG with at least `Omega(log N/log log N)` negative crossing edges.

This is a structural inversion lower bound, not a superpolynomial total-extension lower bound. Since each B2 gate has at most two operand edges, it also implies only the weaker corollary `K=Omega(log N/log log N)`.

## 8. Claim ceiling

Not established:

- superpolynomial `q`;
- superpolynomial unrestricted ER3 extension count;
- ER/Extended-Frege lower bounds;
- deterministic discovery of the required inversion structure;
- polynomial total runtime;
- `P!=NP` or `NP!=coNP`.

## 9. Promotion gates

```text
L1G_F2_RESTRICTION_LEMMA                 = PROVED_ANALYTICALLY
L1G_F2_PURE_CONTEXT_LIFTING              = PROVED_ANALYTICALLY
L1G_F2_MACRO_COMPLEMENT_REFUTATION       = PROVED_ANALYTICALLY
L1G_F2_MACRO_PIVOT_SIMULATION            = PROVED_ANALYTICALLY
L1G_F2_FULL_S_LOCAL_BOUND                = PROVED_ANALYTICALLY
L1G_F2_Q_LOWER_BOUND                     = DERIVED_FROM_SOURCE_LOWER_BOUND
L1G_F2_PROVIDER_REPLAY                   = PENDING
ISSUE_217_FULL_ER3_EXTENSION_COUNT       = OPEN
P_VS_NP                                  = OPEN
```

## 10. Hard laws

```text
RESTRICT_REFUTE_LIFT_STAYS_INSIDE_PURE_RESOLUTION
SMALL_MACRO_CNF_PLUS_STRUCTURAL_COMPLEMENT_REFUTATION => BOUNDED_MACRO_CUT_COST
Q_GROWTH != SUPERPOLYNOMIAL_EXTENSION_COUNT
LOG_OVER_LOGLOG_INVERSION_LOWER_BOUND != ER_LOWER_BOUND
SHORT_PROOF_EXISTENCE != DETERMINISTIC_PROOF_SEARCH
P_VS_NP = OPEN
```
