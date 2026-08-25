# C025 — Akinator RSPC: bounded-support ER3 elimination and forced support growth

Status: **INTERNAL ANALYTIC THEOREM / HARD-FAMILY CONSEQUENCE FROM FROZEN RESOLUTION LOWER BOUND**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The bounded-cover RSPC lane showed a positive fact: if every candidate macro is covered by a universal fixed number `C` of NW neighborhoods, exact residual survival can be discovered by exhaustive truth-table evaluation in polynomial time in the actual direct-parity input length `N`.

This note asks whether a polynomial-size ER3 escape can remain in such a bounded-support lane.

The answer is no, assuming the already frozen pure-Resolution lower bound for the selected NW hard family.

The proof does **not** extend Sokolov's functional encoding from one neighborhood to `C` neighborhoods. Instead it eliminates bounded-support extension variables directly.

---

## 1. Setup

Let `F` be a root CNF over original variables.

Let `pi` be an ER3/B2 refutation:

- extension definitions are acyclic B2 AND/NOT definitions;
- every proof clause has width at most 3 after the frozen ER3 normalization;
- `S` is the number of proof lines;
- every extension literal denotes, after recursively substituting its definition, a Boolean function of original roots;
- `supp(e)` is the exact **transitive syntactic root support** of extension variable `e`;
- assume

`max_e |supp(e)| <= k`.

Root literals have support size 1 and can be absorbed into `max(k,1)`.

No claim is made that syntactic support equals minimum semantic support.

---

## 2. Canonical root expansion of one ER3 clause

Take an ER3 clause

`C = L_1 OR ... OR L_w`, with `w<=3`.

After substituting every extension literal by its root Boolean function, obtain a root Boolean formula `C*` depending on at most `3k` roots.

Encode `C*` by the canonical falsifying-assignment CNF `T(C)`:

for every assignment `alpha` to the relevant roots with `C*(alpha)=0`, include the root clause that excludes exactly `alpha`.

Then:

- `T(C)` is equivalent to `C*`;
- `|T(C)| <= 2^(3k)`;
- every clause in `T(C)` has width at most `3k`.

Special cases:

- for a root axiom, keep the original root clause directly;
- after substitution, each extension-definition axiom is a tautology and needs no root clause;
- the final empty clause maps to the root empty clause.

---

## 3. Simulating one ER3 Resolution inference

Suppose an ER3 inference resolves

`P = A OR X`

and

`Q = B OR NOT X`

into

`R = A OR B`.

Here `X` may be a root or extension literal.

After substitution into root Boolean functions,

`P* AND Q* => R*`

is a semantic tautology: ordinary propositional Resolution remains sound under uniform Boolean substitution for the pivot variable.

Therefore

`T(P) union T(Q) |= D`

for every root clause `D` in `T(R)`.

All formulas involved in this local inference depend on at most the union of the supports of the literals in the two parent clauses, hence on at most `6k` roots.

Resolution is complete for CNF implicates. A brute-force Resolution saturation over `m<=6k` variables encounters at most `3^m` distinct non-tautological clauses. With admissible weakening (or by deriving a stronger subclause and then weakening), every entailed target clause `D` can therefore be produced with

`2^O(k)`

local Resolution work.

Weakening is only an admissible convenience here and can be eliminated without changing the asymptotic `2^O(k)` bound.

Since `|T(R)| <= 2^(3k)`, one entire ER3 inference can be simulated in pure root Resolution with

`2^O(k)`

lines.

---

## 4. Theorem D — bounded-support ER3 elimination

For every ER3/B2 refutation `pi` of root CNF `F` with `S` proof lines and maximum transitive syntactic root support `k`, there exists a pure Resolution refutation of `F` of size

`R(F) <= S * 2^(A*k)`

for some universal constant `A` determined only by the fixed width-3 simulation convention, not by the input instance.

Encoding/serialization polynomial factors can be absorbed into the leading polynomial term and must still be charged separately in any implementation claim.

### Scientific status

This is an internal analytic simulation theorem. Provider finite replay can check small instances but is not the proof of the theorem.

---

## 5. Corollary — fixed support cannot yield a polynomial escape on the frozen hard family

Use the already frozen hard-family consequence:

`ResSize(F_N) >= exp(N^eta)`

for some fixed `eta>0` in the selected encoded-input regime.

Assume for contradiction that an ER3 refutation has

`S(N) <= N^d`

for one fixed `d`, while every extension has

`k(N) <= K`

for one universal fixed `K`.

Theorem D gives

`ResSize(F_N) <= N^d * 2^(A*K) = poly(N)`,

contradicting the frozen exponential Resolution lower bound for sufficiently large `N`.

Therefore:

**EVERY_UNIVERSAL_FIXED_ROOT_SUPPORT_BOUND_IS_INSUFFICIENT_FOR_POLY_SIZE_ER3_ESCAPE_ON_THE_FROZEN_HARD_FAMILY.**

---

## 6. Quantitative support-growth consequence

More strongly, if a polynomial-size ER3 escape exists with `S<=N^d`, then Theorem D and the Resolution lower bound imply

`exp(N^eta) <= N^d * 2^(A*k_max)`.

Taking logarithms:

`N^eta <= d*log N + A*k_max + O(1)`.

Hence

`k_max >= (N^eta - d*log N - O(1))/A`

and therefore

**`k_max = Omega(N^eta)`**.

So any polynomial-size ER3 escape on the stated family must contain at least one extension macro with polynomially large transitive syntactic root support.

This is a structural lower bound on a hypothetical short ER3 proof. It is **not** a lower bound on ER3 proof size itself.

---

## 7. Neighborhood-cover consequence

Every frozen NW neighborhood has size `Delta`.

Any collection of `c` neighborhoods covers at most `c*Delta` distinct roots. Therefore a macro with support size `k` requires minimum neighborhood cover number

`c_min >= k/Delta`.

The direct parity input contains `2^(Delta-1)` clauses per output, so

`2^(Delta-1) <= N`, hence `Delta <= log_2 N + 1`.

Combining with `k_max=Omega(N^eta)` gives

**`c_min = Omega(N^eta / log N)`**

for at least one extension macro in any polynomial-size ER3 escape.

No minimum-cover algorithm is needed for this lower bound; it is a counting consequence of neighborhood cardinality.

---

## 8. Consequence for the exact-survival enumerator

The bounded-cover exact-survival route enumerates all assignments on a macro's root support.

For the forced large-support macro above, this route costs

`2^k = exp(Omega(N^eta))`

assignments in the worst case.

Thus:

**THE_FIXED_C_TRUTH_TABLE_SURVIVAL_ROUTE_CANNOT_SUPPORT_AN_ENTIRE_POLYNOMIAL_SIZE_ER3_ESCAPE_ON_THE_FROZEN_HARD_FAMILY.**

Important ceiling:

This does **not** prove that semantic survival of that large-support macro intrinsically requires exponential time. A succinct structural certificate or special-function algorithm could be faster than truth-table enumeration.

The result only kills the exact exhaustive-enumeration route as a universal polynomial selector mechanism.

---

## 9. Relation to the general NP-completeness barrier

Two separate facts now meet:

1. In unrestricted circuit representation, exact residual nonconstancy discovery is NP-complete.
2. In the frozen NW family, fixed-cover truth-table discovery is polynomial, but any polynomial-size ER3 escape must eventually contain a macro with support `Omega(N^eta)` and cover `Omega(N^eta/log N)`.

Therefore the next selector cannot rely on either:

- unrestricted semantic witness search, or
- exhaustive truth-table search on every useful macro.

It needs a **succinct, compositionally discoverable survival/progress certificate for large-support macros**.

This is exactly the proof-carrying structural-selector target.

---

## 10. New exact Akinator resource

Define the root-support width of a proof/selector state:

`K_root(S) := max_e |supp(e)|`.

For a full ER3 proof `pi`:

`K_root(pi) := max over extension variables e in pi of |supp(e)|`.

Theorem D gives the simulation tradeoff

`ResSize(F) <= ER3Size(pi) * 2^(O(K_root(pi)))`.

On the frozen hard family, a polynomial-size escape requires

`K_root(pi)=Omega(N^eta)`.

This exposes a new mandatory scale that any polynomial Akinator architecture must handle symbolically rather than by explicit assignment enumeration.

---

## 11. Next gate — LARGE-SUPPORT PROOF-CARRYING CERTIFICATES

Search for a certificate language `Cert(e)` satisfying all of:

1. certificate bytes polynomial in original `N` even when `|supp(e)|=Omega(N^eta)`;
2. verification polynomial in original `N`;
3. deterministic discovery polynomial in original `N`;
4. no SAT/model-counting oracle;
5. no exponential witness frontier;
6. no backtracking;
7. certificate composes across AND/NOT extension definitions;
8. source-matched restriction survival is proved;
9. accepted certificates imply a globally sound progress potential.

If such a language exists universally, it is the first genuinely viable polynomial-Akinator layer surviving all current gates.

If it fails, the failure should reveal the next hidden resource: certificate width, separator width, rank, communication boundary, or another explicit structural parameter.

---

## 12. Claim ledger

`BOUNDED_SUPPORT_ER3_TO_RESOLUTION_SIMULATION = PROVED_IN_SCOPE`

`POLY_SIZE_ER3_ESCAPE_REQUIRES_K_ROOT_OMEGA_N_ETA = DERIVED_FROM_FROZEN_RESOLUTION_LOWER_BOUND_PLUS_INTERNAL_SIMULATION`

`POLY_SIZE_ER3_ESCAPE_REQUIRES_COVER_OMEGA_N_ETA_OVER_LOG_N = DERIVED_IN_STATED_NW_ENCODING`

`FIXED_C_BOUNDED_COVER_UNIVERSAL_ESCAPE = REFUTED_IN_STATED_ER3_HARD_FAMILY_SCOPE`

`TRUTH_TABLE_SURVIVAL_AS_UNIVERSAL_POLY_SELECTOR = REFUTED_IN_STATED_SCOPE`

`LARGE_SUPPORT_SUCCINCT_CERTIFICATE_EXISTS = OPEN`

`UNRESTRICTED_ER3_SUPERPOLY_SIZE_LOWER_BOUND = NOT_PROVED`

`P_VS_NP = OPEN`

---

## 13. New laws

- `SHORT_ER3_PROOF_CAN_HIDE_COMPLEXITY_IN_ROOT_SUPPORT_WIDTH`
- `BOUNDED_ROOT_SUPPORT_EXTENSIONS_CAN_BE_ELIMINATED_WITH_2^O(K_ROOT)_OVERHEAD`
- `POLY_ER3_ESCAPE_ON_EXP_RES_HARD_FAMILY_FORCES_K_ROOT=OMEGA(N^ETA)`
- `FIXED_NEIGHBORHOOD_COVER != UNIVERSAL_ER3_ESCAPE`
- `EXACT_TRUTH_TABLE_SURVIVAL != VIABLE_LARGE_SUPPORT_SELECTOR`
- `LARGE_SUPPORT_REQUIRES_SUCCINCT_PROOF_CARRYING_STRUCTURE_OR_ANOTHER_ESCAPE`
