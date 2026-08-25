# C025 — Akinator U1-L1: bounded-induced-width exact projection grammar

Status: **LOG_WIDTH_POSITIVE_CONTROL / ORIGINAL_GRAPH_ONLY_UNIVERSAL_ROUTE_CLOSED_BY_EXPANDERS**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

After showing that an unrestricted uniform projection compiler is essentially equivalent to P=NP, useful progress must come from an independently analyzable structural mechanism.

A broad positive control is exact variable elimination on low-induced-width graphical structure.

This gives a rigorous class where the Akinator/projection idea really is polynomial, and a rigorous reason why merely searching the **original** CNF graph for small separators cannot be universal.

---

## 1. External bucket-elimination bound

Rina Dechter's bucket-elimination framework gives, for a graphical model with variable domain size `d` and an elimination ordering of induced width `w`, time/space exponential in `w` and polynomial in the remaining explicit problem size.

A standard bound is of the form

`time = O(r * d^(w+1))`

and

`space = O(n * d^w)`

(up to the exact notation/variant in the source), where `r` counts local functions/constraints and `n` variables.

For Boolean variables, `d=2`.

Therefore, given a valid elimination ordering with

`w <= c log_2 N`

for one fixed constant c, exact bucket elimination takes

`N^O(1)`

time and space.

Thus:

**LOG_INDUCED_WIDTH + AVAILABLE_ORDER => EXACT_POLYNOMIAL_PROJECTION/SAT.**

The external theorem supplies the bucket-elimination complexity bound; this note only places it in the Akinator projection map.

---

## 2. Proof-carrying structural interpretation

A width-w ordering itself can be treated as a structural certificate:

- its variable permutation is explicit;
- simulate graph fill-in along the ordering;
- verify that each elimination bucket has at most w live neighbors/scope variables.

Given such an ordering, each local elimination step combines only factors over O(w) Boolean variables and projects one variable, producing a factor on at most O(w) remaining variables.

The complete truth table of one factor has at most

`2^O(w)`

entries.

At `w=O(log N)`, every local exact message/factor is polynomially representable.

This is a real local-to-global projection grammar:

`VERIFY_ORDER -> ELIMINATE_BUCKET -> EMIT_EXACT_MESSAGE -> DECREASE_VARIABLE_RANK`.

No SAT oracle or exponential branch tree is required in this class.

---

## 3. Positive scope

The result covers, with the appropriate factor/CNF encoding and an ordering certificate:

- bounded-treewidth formulas;
- logarithmic-induced-width families;
- many sparse/local graphical CSP families;
- any state transformed by previous certified steps into such a bounded-width factorization.

It is substantially broader than one named family such as PHP or Inner Product.

---

## 4. Why original-graph-only structure is not universal

Constant-degree vertex expanders have linear treewidth.

The project already used the standard balanced-separator argument:

- a graph of treewidth w has a balanced separator of size O(w);
- in a constant vertex expander, separating a constant-fraction vertex set requires Omega(n) boundary/separator vertices;
- hence treewidth is Omega(n).

Therefore there are linear-size bounded-degree CNF/CSP incidence/primal structures whose original graph does not admit `O(log N)` induced width.

For such families, the exact bucket-elimination bound becomes exponential in the root structural width.

Hence:

**DISCOVER_SMALL_SEPARATOR_IN_THE_ORIGINAL_GRAPH != UNIVERSAL_PROJECTION_GRAMMAR.**

---

## 5. Why this is not a B2 lower bound

B2/Extended Resolution may introduce new extension variables that **change the representation** of the Boolean obligation.

Cook's PHP construction is already a positive example where adding extension variables exposes a recursive structure unavailable to plain Resolution.

Thus high treewidth of the original root CNF does not imply that every extension-augmented proof/state representation has high effective width or exponential size.

The correct universal target is stronger:

> when root structure is bad, deterministically **create** a new certified representation with a small exact projection interface.

New law:

**DISCOVER_STRUCTURE != CREATE_STRUCTURE.**

---

## 6. Structural synthesis formulation

A useful universal grammar could alternate between:

1. **EXPLOIT:** if the current certified representation has low induced width, run exact bucket projection;
2. **CREATE:** otherwise introduce proof-carrying B2 macros that transform the obligation into a representation with lower effective projection width / a known algebraic stage;
3. repeat while a global polynomial state/rank invariant is maintained.

The unresolved piece is CREATE.

It cannot be implemented by:

- semantic usefulness oracle (coNP-hard barriers);
- exhaustive macro-block search (2^K schema barrier);
- complete cofactor enumeration (Inner Product barrier);
- full exact knowledge compilation with guaranteed poly size (OBDD/SDD barriers).

---

## 7. New exact gate — U1-L2 certified structure creation

Given a current state whose certified elimination width is too high, construct in polynomial time a polynomial-size B2 extension/proof block that either:

- reduces the certified effective width enough for tractable elimination; or
- exposes another family-independent exact reduction rank.

Required theorem:

For every nonterminal state, a bounded sequence of such CREATE/EXPLOIT stages exists and is deterministically found with global `N^O(1)` state/work.

If this theorem is proved, repeated exact elimination gives P=NP.

---

## 8. Current status

`LOG_WIDTH_EXACT_PROJECTION_WITH_ORDER = POLYNOMIAL_POSITIVE_CONTROL`

`ORIGINAL_GRAPH_SMALL_SEPARATOR_UNIVERSALITY = REFUTED_BY_EXPANDER_SCOPE`

`B2_CERTIFIED_STRUCTURE_CREATION = OPEN`

`UNIVERSAL_LOCAL_TO_GLOBAL_GRAMMAR = OPEN`

`P_VS_NP = OPEN`

---

## 9. New laws

- `LOG_INDUCED_WIDTH => POLY_EXACT_ELIMINATION_WITH_CERTIFIED_ORDER`
- `HIGH_ROOT_TREEWIDTH != B2_ER_LOWER_BOUND`
- `DISCOVER_STRUCTURE != CREATE_STRUCTURE`
- `ORIGINAL_GRAPH_SEPARATOR_SEARCH != UNIVERSAL_EXTENSION_GRAMMAR`
- `THE_CREATE_STAGE_IS_NOW_THE_ACTIVE_STRUCTURAL_FRONT`
