# C025 — Akinator PF2: canonical-sharing trilemma

**Status:** `PF2_SYNTACTIC_CANONICALIZATION_AVAILABLE__STRONG_SHARING_GATE_OPEN`  
**Claim ceiling:** `P_VS_NP = OPEN`

## 0. Why PF2 exists

PF1 proves that one explicit CNF pivot can be eliminated before its complete pairwise Davis–Putnam resolvent family is materialized. The remaining resource is not the one-step pair cross-product; it is the total number of distinct factor-DAG objects created across many eliminations.

A natural response is: “canonicalize the DAG harder and merge equal subfunctions.” This note freezes the exact boundary around that sentence.

The word **equal** has three materially different meanings here:

1. syntactically identical;
2. identical inside a restricted canonical representation such as a fixed-order decision diagram;
3. semantically equivalent as arbitrary Boolean circuits.

Conflating them would hide the proof-discovery cost that PF3 is required to charge.

---

## 1. PF2-S — structural hash-consing is cheap and exact

For the frozen B2 basis, represent an AND node by a canonical structural key

`K = (AND, min(a,b), max(a,b))`

where `a,b` are signed references to roots or earlier nodes. Intern one node per exact key. NOT remains a sign on a reference.

This yields deterministic sharing for byte-identical recursive structure. A collision-prone machine hash is only an accelerator; admission equality is the explicit structural tuple, so hash collision cannot become semantic authority.

With a balanced search tree over canonical keys, insertion/lookup is polynomial in the number and bit-length of already-created nodes. A dictionary implementation is an engineering optimization, not the mathematical equality rule.

Therefore:

`PF2_STRUCTURAL_HASH_CONSING = POLYNOMIAL_AND_SOUND`.

But structural interning merges only the same syntax. It does not in general merge algebraically or semantically equivalent circuits.

---

## 2. PF2-E — complete semantic canonicalization is not a free primitive

Consider arbitrary Boolean formula/circuit `H(X)` and the constant-false circuit `0`.

`H ≡ 0  iff  H is UNSAT`.

Circuit/formula equivalence is in coNP because a nonequivalence witness is one assignment on which the outputs differ. The displayed reduction from UNSAT gives coNP-hardness. Hence exact semantic equivalence is coNP-complete in the ordinary succinct circuit/formula setting.

Consequently, a deterministic polynomial routine that, for arbitrary B2 circuits, always merges exactly all semantically equivalent nodes by first deciding their equivalence would already provide a polynomial UNSAT decision procedure.

This does **not** say semantic sharing is forbidden. It says its discovery cost must be explicit. Allowed routes include:

- a restricted equivalence class with a proved polynomial decision procedure;
- a proof-carrying equivalence witness with polynomial verification **and** polynomial discovery/total-cost accounting;
- an exact orbit/generator certificate whose forward/inverse action is independently verified.

Forbidden shortcut:

`SEMANTICALLY_EQUAL_THEREFORE_MERGE` without a paid derivation.

---

## 3. PF2-D — canonical decision diagrams do not erase worst-case representation growth

A second response is to use a canonical restricted representation such as a BDD/ZDD so that equality becomes structural after reduction.

This is legitimate as a restricted lane, but not a universal polynomial-size theorem.

Nakamura, Nishino and Denzumi, *Single Family Algebra Operation on BDDs and ZDDs Leads to Exponential Blow-Up*, ISAAC 2024, DOI `10.4230/LIPIcs.ISAAC.2024.52`, prove that for the family-algebra `Join`

`F ⊔ G = {A ∪ B : A in F, B in G}`

there are polynomial-size input ZDDs whose result requires exponential ZDD size, and the blow-up persists for every element order. This operation is algebraically the same cross-union used by a symbolic residual-family resolvent product before tautology filtering.

Precision boundary: their lower bound is against the ZDD family representation and compact ZDD inputs. It is **not** an unconditional lower bound against arbitrary B2 circuits, nor by itself a lower bound for the explicit one-pivot CNF input of PF1. It closes only the shortcut “ordinary ZDD Join is a universal polynomial prebirth quotient.”

Therefore:

`ZDD_CANONICALITY != UNIVERSAL_POLYNOMIAL_QUOTIENT_SIZE`.

---

## 4. PF2 trilemma

A universal PF2/PF3 route must now choose and pay for one of three resources:

### A. Pure structural sharing

Cheap and exact, but weak. The remaining obligation is a universal bound on syntactically novel factor nodes.

### B. Restricted canonical representation

Equality is cheap inside the representation, but the representation/operation size itself needs a universal polynomial bound. Known BDD/ZDD lower bounds forbid assuming this for free.

### C. Strong semantic/proof-carrying sharing

Potentially compresses beyond syntax, but equivalence/candidate discovery and all failed attempts must be polynomially charged. General semantic equivalence cannot be used as a free selector.

There is no fourth option called “canonicalize” with unpriced semantics.

---

## 5. Connection to the JANUS organism

This boundary matches already-frozen independent lessons without borrowing their authority:

- Tranception prebirth orbit lane: exact generator/inverse certificates may merge branches before birth on restricted families, but universal generator coverage is open;
- C2G charge lane: a small proof certificate is insufficient unless repeated discoveries are globally amortized;
- B2 extension-aware reasons: sound verification is distinct from proof discovery and total runtime;
- ROBDD lane: a compact representation under a favorable structural choice does not establish cheap universal discovery or small size.

The organism contributes candidate mechanisms. The PF2 theorem boundary is supplied only by the reductions and explicit representation facts stated here.

---

## 6. Exact successor experiment

Freeze `PF3_RESIDUAL_NOVELTY_NEGATIVE_CONTROL` before any universal promotion.

For each deterministic sharing lane, measure against original input length `N`:

- `D_t`: distinct live canonical DAG nodes after elimination stage `t`;
- `D_total`: all distinct canonical nodes ever constructed, including discarded temporaries;
- exact key-comparison / canonicalization work;
- proof bytes for every non-syntactic merge;
- failed merge-discovery work;
- witness-provenance bytes;
- maximum and cumulative state volume.

Required controls:

1. the C025 equality-family prebirth-orbit positive control;
2. expander graph-PHP / other already-frozen hard proof controls where applicable;
3. random and planted CNFs frozen before inspection;
4. a decision-diagram blow-up family only for lanes that actually claim BDD/ZDD authority.

No lane may switch representation after seeing a bad holdout without recording that switch as candidate-search work.

---

## 7. Claim ledger

`PF1_ONE_PIVOT_EXACT_FACTOR_COMPRESSION = PROVED_IN_PRIOR_ARTIFACT`

`PF2_STRUCTURAL_HASH_CONSING_SOUNDNESS = PROVED_BY_CONSTRUCTION`

`PF2_STRUCTURAL_HASH_CONSING_POLY_MECHANICS = PROVED_IN_EXPLICIT_KEY_MODEL`

`PF2_GENERAL_SEMANTIC_EQUIVALENCE = CO_NP_COMPLETE`

`PF2_FREE_COMPLETE_SEMANTIC_CANONICALIZER = FORBIDDEN_SHORTCUT`

`PF2_ZDD_JOIN_UNIVERSAL_POLY_QUOTIENT = REFUTED_AS_A_GENERAL_ZDD_SHORTCUT`

`PF3_UNIVERSAL_RESIDUAL_NOVELTY_BOUND = OPEN`

`PF4_PROOF_CARRYING_EQUIVALENCE_ORBIT_DISCOVERY = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 8. Laws

- `SYNTACTIC_EQUALITY != SEMANTIC_EQUIVALENCE`
- `CHEAP_VERIFICATION != CHEAP_DISCOVERY`
- `CANONICAL_REPRESENTATION != POLYNOMIAL_REPRESENTATION`
- `HASH_COLLISION != EQUALITY_AUTHORITY`
- `SMALL_FINAL_DAG != POLYNOMIAL_TOTAL_CONSTRUCTION`
- `STRONGER_SHARING_MUST_PAY_FOR_ITS_EQUIVALENCE_CERTIFICATE`
