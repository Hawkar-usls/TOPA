# C025 — Akinator RSPC U1-A: complete clause-frontier width dichotomy

Status: **COMPLETE_ROOT_CLAUSE_FRONTIER_ROUTE_CLOSED_IN_STATED_RESOLUTION_SCOPE / B2_PROOF_RELEVANT_INTERFACE_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The structured knowledge-compilation sweep suggests that the selector should not maintain the complete semantic model set of every macro. The next natural repair is genuinely proof-relative:

> retain only Resolution consequences that can be used by later proof steps.

A canonical exact version is the complete width-`w` Resolution frontier: saturate all non-tautological clauses of width at most `w` derivable from the current root CNF.

This note shows the basic dichotomy for that exact interface:

- small fixed width gives a polynomially enumerable/closed proof interface but is incomplete on expander pigeonhole formulas;
- increasing width enough to cover the known hard Resolution regime makes the **complete clause universe itself exponential**.

This closes only the complete root-clause-frontier route. Sparse wide-clause interfaces and extension-aware B2 interfaces remain open.

---

## 1. Frozen interface

For a CNF `F` on `n` root variables and integer `w`, define

`CL_w(F)`

as the set of all non-tautological clauses of width at most `w` that are derivable from `F` by a Resolution derivation in which every clause has width at most `w`.

A deterministic saturation algorithm repeatedly adds every legal width-`<=w` resolvent until closure.

The interface is **complete within width w**: if a width-`w` Resolution refutation exists, saturation eventually derives the empty clause.

---

## 2. Exact universe count

The number of non-tautological clauses of exact width `k` over `n` variables is

`2^k * binom(n,k)`:

choose `k` distinct variables and one sign for each.

Hence the complete clause universe through width `w` has size

`U(n,w) = sum_{k=0}^w 2^k binom(n,k)`.

Consequences:

### Fixed `w`

For fixed universal constant `w`,

`U(n,w) = n^{O(w)} = n^{O(1)}`.

Thus complete width-bounded saturation is polynomial in the explicit input size up to the ordinary polynomial factor for pair scanning/canonical indexing.

### Logarithmic `w`

For `w = Theta(log n)`, the straightforward complete universe can already be

`n^{Theta(log n)}`,

i.e. quasi-polynomial rather than a fixed polynomial.

### Linear `w`

For any fixed `0 < alpha <= 1/2` and `w >= alpha n`,

`U(n,w) >= 2^{alpha n} binom(n, floor(alpha n)) = 2^{Omega(n)}`.

Even the weaker bound `U(n,w) >= 2^w` is exponential when `w=Omega(n)`.

So:

**COMPLETE_WIDE_CLAUSE_FRONTIER_CAN_HAVE_EXPONENTIAL_SERIALIZATION/ENUMERATION COST.**

---

## 3. External Resolution width barrier

### External theorem basis

Eli Ben-Sasson and Avi Wigderson, **Short Proofs are Narrow — Resolution Made Simple**, JACM 48(2), 2001 (earlier ECCC TR99-022 / CCC 1999).

Their width framework relates Resolution width and size and gives width lower bounds from expansion. In particular, the paper defines graph pigeonhole formulas `G-PHP` and proves large width for suitable bipartite expanders.

The frozen TOPA/O5 graph-PHP lane already imports this source theorem with explicit graph/input accounting and keeps the source theorem separate from our execution/interface deductions.

For the suitable expander regime used there, let

`W_G(n)`

be the required Resolution refutation width; the frozen hard-family choice has growing, and in the stated strong expander parameterization linear, width in the graph-size parameter.

### Consequence

If `w < W_G(n)`, then `CL_w(G-PHP)` cannot contain the empty clause. Therefore no selector whose entire proof-relevant state is just the complete root-clause frontier `CL_w` can decide UNSAT on this family while keeping width below the required bound.

For constant `w`, this yields a polynomial but incomplete interface.

If one repairs completeness by taking `w` into the linear-width regime, Section 2 shows that the complete clause universe has exponential size.

Thus, in the stated Resolution/root-clause interface:

`TRACTABLE_COMPLETE_LOW_WIDTH_FRONTIER`

and

`COMPLETE_ENOUGH_WIDE_FRONTIER`

cannot both be obtained by naive full saturation on the expander G-PHP family.

---

## 4. The dichotomy

For the frozen complete clause-frontier interface:

### Lane A — keep `w` small

- polynomially many possible clauses;
- deterministic exact saturation is feasible;
- but known expander G-PHP width lower bounds block refutation.

### Lane B — raise `w` to the hard-family requirement

- width obstruction is no longer excluded by definition;
- but enumerating/storing **all** width-`<=w` clauses incurs exponential universe size in the linear-width regime.

Therefore:

**COMPLETE_ROOT_CLAUSE_FRONTIER_IS_NOT_A_UNIVERSAL_POLYNOMIAL_AKINATOR_INTERFACE.**

This is an interface theorem derived from an external Resolution width lower bound plus our exact clause-universe accounting. The source does not prove an Akinator theorem.

---

## 5. Why this does not close sparse wide clauses

A short Resolution or ER proof need not contain every possible clause of a given width. It may use a tiny, highly selected subset.

Therefore the exponential size of the **complete** width-`w` frontier does not imply that every successful proof stores exponentially many clauses.

The correct next question is discovery:

> Can a deterministic polynomial selector find the sparse useful wide clauses / extension macros without saturating the whole width universe and without using a semantic oracle?

This is exactly where earlier selector-lift barriers apply:

- exact semantic usefulness can be coNP-hard;
- brute-force schema enumeration can be exponential;
- plain Resolution reason discovery is insufficient on selector-PHP;
- family-specific B2 schemas such as Cook's PHP construction can be polynomially generated.

So the exponent has moved from **complete proof-state representation** to **sparse proof-object discovery**.

---

## 6. Why B2/ER remains alive

Extension variables can name global functions so that clauses over extension variables stay syntactically narrow while representing globally mixed semantics. The graph-PHP O7 positive control already demonstrates a family-specific polynomial B2/ER generator where plain Resolution is hard.

Hence the root-clause width dichotomy does not refute B2/ER.

Instead it proves a design law for the next Akinator:

`DO_NOT_MATERIALIZE_COMPLETE_ROOT_CONSEQUENCE_FRONTIER.`

The selector must discover a sparse proof-carrying extension/reason sequence directly.

---

## 7. New exact gate — U1-B sparse derivational interface

Freeze an interface whose state consists only of a polynomial number of proof objects actually selected so far, with no claim of complete semantic or width closure.

Required obligations:

1. **SPARSE_STATE:** at most `N^c` retained objects/bytes for fixed universal `c`;
2. **POLY_PROPOSAL:** at each step only `N^c` candidates are generated;
3. **PROOF_CARRYING_ACCEPTANCE:** accepted candidate has a locally checkable derivation/progress certificate;
4. **NO_SEMANTIC_ORACLE:** acceptance does not call SAT, #SAT, exact circuit equivalence, or arbitrary symbolic intersection;
5. **NO_BACKTRACKING:** deterministic rule does not enumerate exponentially many candidate sequences;
6. **UNIVERSAL_AVAILABILITY:** every nonterminal target state has an accepted move;
7. **GLOBAL_PROGRESS:** a polynomially bounded sound potential reaches exact SAT/UNSAT termination.

Items 6–7 remain the decisive open obligations.

Current status:

**U1_COMPLETE_ROOT_CLAUSE_FRONTIER = CLOSED_IN_STATED_SCOPE**  
**U1_B_SPARSE_DERIVATIONAL_INTERFACE = OPEN**  
**POLYNOMIAL_AKINATOR = OPEN**  
**P_VS_NP = OPEN**

---

## 8. New laws

- `POLY_COMPLETE_LOW_WIDTH_CLOSURE != UNIVERSAL_RESOLUTION_POWER`
- `REQUIRED_WIDE_RESOLUTION != MATERIALIZE_ALL_WIDE_CLAUSES`
- `EXPONENTIAL_COMPLETE_FRONTIER != EXPONENTIAL_SPARSE_PROOF`
- `WIDTH_LOWER_BOUND != ER_LOWER_BOUND`
- `SPARSE_PROOF_EXISTS != CHEAP_SPARSE_PROOF_DISCOVERY`
- `EXTERNAL_WIDTH_THEOREM + INTERNAL_FRONTIER_ACCOUNTING != SOURCE_PROVES_AKINATOR_IMPOSSIBILITY`
