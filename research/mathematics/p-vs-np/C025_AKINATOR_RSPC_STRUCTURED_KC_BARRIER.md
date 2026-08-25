# C025 — Akinator RSPC T2: structured knowledge-compilation barriers

Status: **STRUCTURED_DDNNF_TRANSFORM_ROUTE_CLOSED / SDD_UNIVERSAL_POLY_SERIALIZATION_CLOSED_IN_STATED_EXPANDER-CNF_SCOPE**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

T1 closed several natural exact frontier languages:

- Horn, Krom, affine: tractable but not expressively closed even under tiny B2 macros;
- OBDD: exact Boolean operations are tractable in representation size, but some polynomial-size circuits require exponential OBDD size.

The next repair is a more expressive structured knowledge-compilation language, especially structured deterministic DNNF (d-SDNNF / structured d-DNNF) or SDD.

This note records two distinct barriers:

1. general structured d-DNNF does not support polynomial negation/disjunction in the required universal sense;
2. even SDD, which does support tractable Boolean Apply, can require exponential representation size for a simple linear-size monotone CNF family.

These are representation-language barriers, not P-vs-NP lower bounds.

---

## 1. Structured d-DNNF transformation barrier

### External theorem

Harry Vinall-Smeeth, **Structured d-DNNF Is Not Closed under Negation**, IJCAI 2024, pp. 3593–3601, DOI 10.24963/ijcai.2024/398.

The result shows that structured d-DNNF does not support polynomial-time negation, disjunction, or existential quantification in the general representation language.

### Consequence for the RSPC semantic-frontier idea

The frozen B2 language uses signed earlier literals and AND definitions. If the semantic-frontier layer represents the positive set of each macro and expects to obtain the negative set by exact negation with polynomial representation/work, unrestricted structured d-DNNF cannot guarantee that operation.

A proposed dual-storage repair (store both `g` and `NOT g`) does not automatically solve the recursive update: for `e = a AND b`, the negative side is `NOT e = (NOT a) OR (NOT b)`, and general structured d-DNNF also lacks polynomial disjunction closure.

Therefore:

**UNRESTRICTED_STRUCTURED_DDNNF_IS_NOT_A_FREE_EXACT_B2_FRONTIER.**

Claim ceiling: a selector could restrict its operations, use a stronger language, or maintain special invariant subclasses. No universal selector impossibility follows.

---

## 2. SDD remains operationally stronger but can have exponential size

SDDs are a subclass of deterministic structured DNNFs with stronger sentential-decision structure. They support exact operations such as negation and Boolean Apply under their standard structural discipline.

The remaining question is universal polynomial serialization.

We close that route in a concrete bounded-degree monotone-CNF scope.

---

## 3. Expander vertex-cover CNF family

Let `G_n=(V,E)` be an explicit constant-degree vertex-expander family with `|V|=n` and fixed expansion constant `h>0`.

Define the monotone 2-CNF

`VC(G_n) := AND_{(u,v) in E} (x_u OR x_v)`.

Its satisfying assignments are exactly vertex covers of `G_n`.

### Input/B2 size

For constant degree:

- `|E|=O(n)`;
- the CNF has `O(n)` clauses of arity 2;
- each variable occurs only `O(1)` times;
- each OR clause has a constant-size B2 realization via De Morgan;
- an AND tree over all clauses has `O(n)` B2 gates.

Thus the Boolean function has a linear-size ordinary circuit/B2 representation, up to ordinary variable-index encoding factors.

---

## 4. Internal lemma — constant vertex expansion forces linear treewidth

A graph of treewidth `w` has a balanced vertex separator of size at most `w+1` (standard treewidth separator property).

For a constant vertex-expander family, every separator that separates a constant fraction of the vertices from the rest has size `Omega(n)`: if a side `A` has size between fixed constant fractions of `n`, all external neighbors of `A` must lie in the separator, while expansion gives `|N(A)\A| >= h|A|`.

Therefore any balanced separator has linear size, and hence

`tw(G_n) = Omega(n)`.

This step is graph-theoretic and independent of the knowledge-compilation lower bound.

---

## 5. External d-SDNNF lower bound and transfer to SDD

### External theorem

Antoine Amarilli, Mikaël Monet, Pierre Senellart, **Connecting Width and Structure in Knowledge Compilation**, ICDT 2018 / LIPIcs.

For monotone CNF/DNF formulas under constant arity and degree, their results give exponential lower bounds for structured (deterministic) DNNF representations in the formula treewidth (with the exact theorem hypotheses preserved in the source).

Our `VC(G_n)` family has:

- monotone CNF;
- arity 2;
- constant variable degree;
- treewidth `Omega(n)`.

Hence every d-SDNNF representation of the family has size

`2^{Omega(n)}`

(up to the fixed-parameter constants in the source theorem).

Every SDD is, in particular, a deterministic structured DNNF. Therefore the same lower bound applies to SDD representations of this family.

So:

**SDD_UNIVERSAL_POLY_SERIALIZATION = REFUTED_IN_THIS_EXPLICIT_EXPANDER_MONOTONE_2CNF_SCOPE.**

In encoded input length `N=O(n log n)` under explicit variable identifiers, this remains

`2^{Omega(N/log N)}`,

which is superpolynomial.

### Scientific attribution

The d-SDNNF lower bound is external. Our contribution here is the choice of a bounded-degree expander monotone 2-CNF, the linear-treewidth transfer, and its placement as an RSPC representation barrier. The source does not prove our Akinator theorem.

---

## 6. What this closes

The following naive route is closed:

`arbitrary B2 semantic frontier -> compile every current macro exactly to polynomial-size SDD -> use tractable exact Apply forever`.

Even a linear-size monotone 2-CNF function can force exponential SDD size.

Combined with earlier barriers:

- arbitrary circuits: compact, exact intersection NP-complete;
- explicit witnesses: exact compatibility cheap, complete frontier can be exponential;
- Horn/Krom/affine: tractable but fail B2 expressiveness;
- OBDD: representation can be exponential;
- structured d-DNNF: general negation/disjunction transform barrier;
- SDD: representation can be exponential on the expander-CNF family.

The hidden exponent has therefore survived several major knowledge-compilation repairs.

---

## 7. What remains open

This note does **not** rule out:

- family-specific hybrid representations;
- dynamically changing representation languages;
- proof objects that do not encode full semantic witness sets;
- local/partial certificates whose global soundness follows from a different invariant;
- a polynomial Akinator obtained by a yet-unidentified structural theorem.

The next admissible move should stop trying to represent the **entire semantic model set of every macro**.

Instead, seek a smaller proof-relevant interface.

---

## 8. New exact gate — RSPC-U1 proof-relevant interfaces

Freeze an interface object `I(g)` which is weaker than the full model set of `g` but sufficient for the selector's next-step proof obligations.

It must satisfy simultaneously:

1. `|I(g)| <= N^c` for fixed universal `c`;
2. deterministic construction/update in `N^c` total work;
3. exact polynomial verification;
4. no semantic SAT/model-counting oracle;
5. no need to compile arbitrary `g` to a full exact tractable knowledge representation;
6. a theorem that the interface is complete enough to guarantee a progress move for every target state;
7. a global polynomial potential.

The central question becomes:

> What is the minimum proof-relevant information needed to choose a correct globally-progressing B2 extension without representing or solving the entire residual Boolean function?

Current status:

**RSPC_U1_PROOF_RELEVANT_INTERFACE = OPEN**  
**POLYNOMIAL_AKINATOR = OPEN**  
**P_VS_NP = OPEN**

---

## 9. New laws

- `TRACTABLE_BOOLEAN_APPLY != UNIVERSAL_POLY_SERIALIZATION`
- `STRUCTURED_DDNNF_SUCCINCTNESS != POLY_NEGATION_CLOSURE`
- `SDD_TRACTABILITY_IN_EXPLICIT_SIZE != POLY_SIZE_IN_ORIGINAL_INPUT`
- `FULL_SEMANTIC_FRONTIER_MAY_BE_STRONGER_THAN_SELECTOR_NEEDS`
- `KNOWLEDGE_COMPILATION_BARRIER != P_VS_NP_LOWER_BOUND`
- `EXTERNAL_DSDNNF_LOWER_BOUND + INTERNAL_EXPANDER_TRANSFER != SOURCE_PROVES_AKINATOR_IMPOSSIBILITY`
