# C025 — Akinator PF3: boundary-quotient representation closures

**Status:** `RESTRICTED_REPRESENTATION_SHORTCUTS_CLOSED__POLY_UPDATE_GATE_OPEN`  
**Claim ceiling:** `P_VS_NP = OPEN`

## 0. Context

PF1 removes the explicit one-pivot Davis–Putnam pair cross-product by exact prebirth factorization. PF2 then shows that after existential projection, previously functional B2 provenance may become a **joint boundary relation**. The remaining question is whether that relation can always be carried forward by a polynomially constructible exact quotient.

This note closes several tempting universal representation shortcuts and sharpens the resource that remains open.

---

## 1. Theorem BQ1 — arbitrary CNF functions already occur as one-step projected boundaries

Let `H(Y)` be any CNF over variables `Y`. Introduce one fresh root `x` and define

`F(x,Y) := H(Y) AND x`.

Then

`exists x . F(x,Y) == H(Y)`.

### Proof

For any assignment `alpha` to `Y`, choose `x=1`. Then `F(1,alpha)=H(alpha)`. If `H(alpha)=0`, no value of `x` can satisfy the conjunction because the `H` factor is independent of `x`. Therefore the existential projection equals `H` pointwise. QED.

A symmetric embedding uses `H(Y) AND NOT x`.

Hence the family of relations/functions that may appear immediately after exact existential projection contains every CNF Boolean function.

This matters because no proposed universal boundary language may assume that “post-PF1 boundaries” are automatically a structurally easy subclass unless an additional invariant is proved.

`ONE_STEP_PROJECTED_BOUNDARY_CLASS_CONTAINS_ALL_CNF_FUNCTIONS = PROVED`.

---

## 2. Consequence — representation size alone is not the missing theorem

An arbitrary Boolean circuit/B2 DAG can represent `H` with polynomial size simply by retaining the original CNF circuit. Thus BQ1 is **not** an unconditional lower bound against general circuits.

The hard resource is the combination:

1. polynomial state bytes in original input length `N`;
2. deterministic polynomial construction/discovery;
3. exact polynomial existential projection/update for the next pivot;
4. polynomial verification;
5. polynomial witness/provenance lift;
6. polynomial total intermediate and failed-attempt work over the whole run.

A language that is succinct but does not support the next exact update cheaply has not solved PF3.

New law:

`SMALL_BOUNDARY_REPRESENTATION != CHEAP_BOUNDARY_ELIMINATION`.

---

## 3. OBDD shortcut — universally closed

Bova and Slivovsky, *On Compiling Structured CNFs to OBDDs* (Theory of Computing Systems 61, 2017; arXiv:1411.5494), prove an exponential OBDD lower bound for a class of CNFs built from expander graphs. The hard formulas satisfy strong syntactic restrictions: monotone 2-CNF / bounded incidence degree, with the lower bound holding for every variable ordering.

Combine this external theorem with BQ1. For each hard CNF `H(Y)`, form

`F(x,Y)=H(Y) AND x`.

After eliminating `x`, the exact boundary is `H(Y)`. Therefore any boundary engine that promises a polynomial-size OBDD for **every** projected boundary contradicts the known OBDD lower bound.

Thus:

`UNIVERSAL_POLY_OBDD_BOUNDARY_QUOTIENT = REFUTED`.

Precision: this closes OBDDs as a universal target language. It does not refute OBDDs on bounded-pathwidth or other special families, where they remain a valid positive lane.

---

## 4. DNNF shortcut — universally closed

Bova, Capelli, Mengel and Slivovsky, *Expander CNFs have Exponential DNNF Size* (arXiv:1411.1995), prove an unconditional exponential lower bound for DNNF representations of a class of read-3 monotone 2-CNF formulas based on expander graphs.

Again use BQ1. If every projected Akinator boundary admitted a polynomial-size DNNF, then every CNF in that hard family would admit one after eliminating the fresh unit pivot. This contradicts the external lower bound.

Therefore:

`UNIVERSAL_POLY_DNNF_BOUNDARY_QUOTIENT = REFUTED`.

Because DNNF strictly generalizes several common knowledge-compilation targets, this also blocks treating those restricted sublanguages as an unproved universal escape.

Precision: arbitrary unrestricted Boolean circuits are not covered by this DNNF lower bound.

---

## 5. ZDD family-algebra shortcut — separately restricted

For symbolic **families of sets**, Nakamura, Nishino and Denzumi, *Single Family Algebra Operation on BDDs and ZDDs Leads to Exponential Blow-Up* (ISAAC 2024, DOI `10.4230/LIPIcs.ISAAC.2024.52`), prove that `Join`

`F join G = {A union B : A in F, B in G}`

can map polynomial-size input ZDDs to an exponential-size output ZDD, with the lower bound persisting for every element order.

This is directly relevant to any lane that stores a symbolic family of residual clauses and computes the resolution pair product by ZDD family algebra.

However, the compact-ZDD inputs in that theorem need not correspond to an **explicit** polynomial-size CNF clause list. Therefore this lower bound is not silently promoted to an arbitrary-CNF or arbitrary-B2-circuit lower bound.

It closes only the shortcut:

`ORDINARY_ZDD_JOIN_AS_UNIVERSAL_POLY_SYMBOLIC_FRONTIER = REFUTED`.

---

## 6. Explicit live-width lane — useful but not universal by assumption

The existing internal live-width theorem gives exact relational DP in

`poly(T) * 2^O(lambda)`

for the deterministic gate-trace live width `lambda`, and therefore polynomial time when `lambda=O(log N)` with a universal constant.

The same artifact already contains a polynomial-size fixed B2 architecture whose every topological serialization has large live width. It also correctly notes that an equivalent lower-width representation may exist, so this is an architecture lower bound rather than an intrinsic function lower bound.

Hence the explicit table lane remains:

- **proved positive** for low live width;
- **not universal** without a polynomial rewrite/discovery theorem.

`LOW_WIDTH_REWRITE_DISCOVERY = OPEN`.

---

## 7. The remaining universal gate — representation plus update

After these closures, the universal target cannot be stated merely as “find a small canonical boundary object.” The required object is an **updatable proof-carrying boundary quotient**.

Define a candidate boundary package at stage `t`:

`BQ_t = (Rep_t, Cert_t, Provenance_t)`.

A universal PF3 theorem must provide fixed constants such that, for every original CNF input of length `N` and every stage:

1. `bytes(BQ_t) <= N^K`;
2. `BQ_t` is deterministically discovered/constructed in polynomial total work;
3. the next original-root existential projection is computed **directly on the representation** in polynomial work, without full decompression;
4. exact equivalence/equisatisfiability of the update is polynomially verified;
5. witness lift/project is polynomial;
6. all failed candidate representations/orders/quotients are charged;
7. cumulative live and temporary bytes over all stages are polynomial in `N`;
8. no SAT/UNSAT/semantic-equivalence oracle is hidden in canonicalization.

Call this gate

`UNIVERSAL_POLY_BOUNDARY_QUOTIENT_WITH_UPDATE`.

If it is proved for all `n` original-root eliminations, the final root-free exact state is directly decidable in polynomial time. That would yield a deterministic polynomial SAT decider and hence establish `P=NP`.

At present this gate is open.

---

## 8. Where the organism can still help

The whole JANUS organism now contributes **restricted mechanisms**, not a universal theorem:

- Tranception: prebirth exact orbit generators on restricted equality families;
- live-width path DP: exact boundary relations at `lambda=O(log N)`;
- ROBDD: exact residual quotient where a compact order is available;
- C2G laminar/disjoint charging: conditional global amortization if accepted regions/rewrites admit the required charge structure;
- PF2 canonical-sharing trilemma: structural equality is cheap, unrestricted semantic equality is not;
- distributed field: parallel latency never erases total-work accounting;
- OdontoForge/AIFC-style lineage rules: compact state without witness-return/provenance is not promotable.

The next useful synthesis must prove that enough of these restricted lanes cover **every** nonterminal state with polynomial discovery and a single polynomial potential. Coverage, not another isolated positive family, is the missing theorem.

---

## 9. Frozen next experiment — PF3 boundary coverage matrix

Before adding a new holdout, build a preregistered matrix over already-revealed controls.

For every state/family, record whether a boundary package is admitted by:

- `LW`: explicit live-width DP;
- `OBDD`: only if actual serialized size/order certificate is polynomial;
- `ORBIT`: exact prebirth symmetry/generator quotient;
- `LAMINAR_CHARGE`: only as a global repeated-step charge, not a representation by itself;
- `RAW_B2`: compact representation only; **not** counted as success unless the next projection/update is polynomially certified.

Required columns:

`N, stage, representation, state_bytes, construction_work, verification_work, next_update_work, failed_search_work, witness_bytes, cumulative_bytes, admitted_reason`.

A row is `PASS` only when **representation and next exact update** are both inside one fixed polynomial budget.

Use expander-CNF controls specifically to falsify universal OBDD/DNNF claims, not to claim a lower bound against arbitrary circuits.

---

## 10. Claim ledger

`ONE_STEP_PROJECTED_BOUNDARY_CLASS_CONTAINS_ALL_CNF_FUNCTIONS = PROVED`

`SMALL_GENERAL_CIRCUIT_REPRESENTATION_OF_BOUNDARY = TRIVIAL_BUT_INSUFFICIENT`

`UNIVERSAL_POLY_OBDD_BOUNDARY_QUOTIENT = REFUTED_BY_EXTERNAL_LOWER_BOUND_PLUS_BQ1`

`UNIVERSAL_POLY_DNNF_BOUNDARY_QUOTIENT = REFUTED_BY_EXTERNAL_LOWER_BOUND_PLUS_BQ1`

`ORDINARY_ZDD_JOIN_AS_UNIVERSAL_POLY_SYMBOLIC_FRONTIER = REFUTED_IN_ITS_REPRESENTATION_LANE`

`LOW_LIVE_WIDTH_EXPLICIT_BOUNDARY_DP = POSITIVE_RESTRICTED_LANE`

`UNIVERSAL_POLY_BOUNDARY_QUOTIENT_WITH_UPDATE = OPEN`

`UNIVERSAL_POLYNOMIAL_COVERAGE_AND_GLOBAL_POTENTIAL = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 11. Laws

- `POST_PROJECTION_BOUNDARY_CAN_BE_AN_ARBITRARY_CNF_FUNCTION`
- `SMALL_REPRESENTATION != CHEAP_UPDATE`
- `KNOWLEDGE_COMPILATION_CANONICALITY != UNIVERSAL_SUCCINCTNESS`
- `RESTRICTED_LOWER_BOUND != GENERAL_CIRCUIT_LOWER_BOUND`
- `BOUNDARY_QUOTIENT_MUST_BE_CONSUMED_WITHOUT_EXPONENTIAL_DECOMPRESSION`
- `COVERAGE_PLUS_TOTAL_COST_NOT_ONE_POSITIVE_FAMILY_IS_THE_GLOBAL_GATE`
