# C025 — Akinator RSPC T1: tractable representation kill sweep

Status: **MULTIPLE_NATURAL_CLASSES_CLOSED / UNIVERSAL_TRACTABLE_LANGUAGE_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Target

After the explicit-witness/symbolic-intersection dichotomy, the next proposed escape is a restricted representation language `L` with:

1. polynomial serialization;
2. exact polynomial-time intersection/compatibility;
3. polynomial-time closure under the updates needed by the selector;
4. enough expressiveness for universal proof-carrying progress.

This note audits four natural candidates: Horn CNF, Krom/2-CNF, affine GF(2) systems, and OBDDs.

The first three fail expressiveness already on constant-size B2 macros. OBDDs recover Boolean expressiveness/operations but fail universal polynomial serialization by a known exponential lower bound.

This is not an impossibility theorem for every conceivable representation language.

---

## 1. Horn relations: exact XOR already escapes

### Closure lemma

The model set of every Horn CNF is closed under coordinatewise Boolean AND.

Proof: consider a Horn clause. It has at most one positive literal. If two assignments satisfy the clause but their coordinatewise AND falsified it, then all negative literals would be false in the AND (hence their variables are 1 in both assignments), and the possible positive literal would be false in the AND (hence is 0 in at least one assignment). That assignment would falsify the clause, contradiction. Clausewise closure gives formula closure.

### Constant-size counterexample

`XOR_2(x,y)` has positive set

`{01,10}`.

Both are models, but their coordinatewise AND is `00`, which is not a model.

Therefore no Horn CNF, of any size, exactly represents the positive set of `XOR_2`.

But `XOR_2` has a constant-size B2 AND/NOT gadget.

Hence:

**HORN_FRONTIER_LANGUAGE_IS_NOT_B2_EXPRESSIVELY_CLOSED.**

This is stronger than a size lower bound: exact representation is impossible inside the Horn relation class.

---

## 2. Krom / 2-CNF relations: exact 3-parity escapes

### Closure lemma

The model set of every 2-CNF formula is closed under coordinatewise majority of any three models.

For one 2-clause `(l1 OR l2)`, suppose the majority assignment falsifies both literals. Then at least two of the three input assignments falsify `l1`, and at least two falsify `l2`. Among three assignments these two size-2 sets intersect, so some input assignment falsifies both literals, contradicting that it satisfies the clause. Apply clausewise.

### Constant-size counterexample

Odd `PARITY_3` has, among its models,

`100`, `010`, `001`.

Their coordinatewise majority is `000`, which has even parity and is not a model.

Therefore odd 3-parity is not representable by any 2-CNF formula.

Yet it has constant-size B2 representation.

Hence:

**KROM_FRONTIER_LANGUAGE_IS_NOT_B2_EXPRESSIVELY_CLOSED.**

---

## 3. Affine GF(2) relations: exact OR escapes

An affine relation is the solution set of a linear system `A x = b` over GF(2).

### Closure lemma

For any three solutions `a,b,c` of the same affine system,

`a XOR b XOR c`

is also a solution, since

`A(a+b+c) = b+b+b = b` over GF(2).

### Constant-size counterexample

`OR_2(x,y)` has positive set

`{01,10,11}`.

But

`01 XOR 10 XOR 11 = 00`,

and `00` is not a model of OR.

Therefore no affine GF(2) system exactly represents the positive set of OR_2.

OR_2 has constant-size B2 representation via De Morgan.

Hence:

**AFFINE_FRONTIER_LANGUAGE_IS_NOT_B2_EXPRESSIVELY_CLOSED.**

This does not diminish affine/XOR solving as a family-specific module; it only closes affine relations as a universal exact semantic-frontier language for arbitrary B2 macros.

---

## 4. OBDDs: tractable operations, but representation size can be exponential

Ordered binary decision diagrams support canonical representation for a fixed order and standard exact operations such as restriction, complement, satisfiability, and Boolean apply in time polynomial in the explicit diagram sizes (with the usual product-size caveat for binary apply).

However universal polynomial serialization fails.

### External lower bound

The hidden weighted bit function `HWB_n` is a standard function with exponential OBDD size independent of variable ordering. See:

- Beate Bollig, Martin Löbbing, Martin Sauerhoff, Ingo Wegener, **On the Complexity of the Hidden Weighted Bit Function for Various BDD Models**, RAIRO Theoretical Informatics and Applications 33(2), 1999, 103–115, DOI 10.1051/ita:1999108.
- The paper describes HWB as a canonical example with exponential OBDD size and discusses the order-independent lower-bound phenomenon, building on Bryant's OBDD lower-bound work.

### Small-circuit side

`HWB_n(x)=x_|x|` is computable by polynomial-size Boolean circuits: compute the Hamming weight in binary using an adder network and select the indexed input bit with a multiplexer. AND/NOT B2 gates simulate the resulting Boolean circuit with constant-factor/standard polynomial overhead.

Thus a polynomial-size B2 macro can require exponential OBDD representation.

Hence:

**OBDD_FRONTIER_LANGUAGE_FAILS_UNIVERSAL_POLY_SERIALIZATION.**

The external theorem supplies the OBDD lower bound; our role is only the B2/circuit representation comparison.

---

## 5. Four-way picture

The first T1 sweep now gives:

- arbitrary Boolean circuits: compact and expressive, but exact frontier intersection is NP-complete;
- explicit assignment frontiers: exact compatibility is cheap, but partner-complete frontiers can be exponential;
- Horn/Krom/affine symbolic languages: exact reasoning is tractable, but constant-size B2 functions already escape the language;
- OBDDs: exact Boolean manipulation is tractable in explicit diagram size, but the diagram itself can be exponentially larger than a polynomial-size circuit/B2 macro.

Therefore the next representation must avoid **all** of:

`SEMANTIC_SEARCH_HARDNESS`,
`EXPLICIT_FRONTIER_EXPLOSION`,
`EXPRESSIVENESS_LOSS`,
`REPRESENTATION_SIZE_EXPLOSION`.

No theorem here proves that no such language exists.

---

## 6. New exact gate — T2 hybrid/structured languages

The next candidate deck should include languages more expressive than Horn/Krom/affine and potentially more succinct than OBDDs, while preserving exact tractable operations under a frozen structural discipline.

Candidates include structured decomposable representations (for example d-DNNF/SDD-style objects), bounded-treewidth incidence decompositions, and explicitly typed hybrid sums/products of Horn, affine, and local components.

Each candidate must be audited for five costs in original input length `N`:

1. serialization size;
2. exact intersection/compatibility;
3. complement/negation or a proof that complement is not required by the frozen selector interface;
4. restriction and composition closure;
5. deterministic discovery/construction cost.

Only after these pass may universal progress be tested.

---

## 7. Claim ceilings

This note does **not** claim:

- all tractable representation languages are impossible;
- OBDD lower bounds imply circuit lower bounds;
- Horn/Krom/affine modules are useless as family-specific solvers;
- a source-matched NW hard family forces HWB-like OBDD explosion;
- P != NP or P = NP.

Current status:

**RSPC_T1_NATURAL_CLASS_SWEEP = MULTIPLE_ROUTES_CLOSED**  
**RSPC_T2_STRUCTURED_HYBRID_LANGUAGE = OPEN**  
**POLYNOMIAL_AKINATOR = OPEN**  
**P_VS_NP = OPEN**

---

## 8. New laws

- `TRACTABLE_INTERSECTION != B2_EXPRESSIVE_CLOSURE`
- `B2_EXPRESSIVENESS != POLYNOMIAL_REPRESENTATION_IN_A_RESTRICTED_LANGUAGE`
- `CANONICAL_EXACT_REPRESENTATION != POLYNOMIAL_SERIALIZATION`
- `HORN_OR_KROM_OR_AFFINE_SOLVER != UNIVERSAL_SEMANTIC_FRONTIER`
- `OBDD_LOWER_BOUND != CIRCUIT_LOWER_BOUND`
- `EXTERNAL_OBDD_THEOREM + INTERNAL_B2_COMPARISON != SOURCE_PROVES_SELECTOR_IMPOSSIBILITY`
