# C025 — Akinator U1-B: the complete one-step B2 candidate language is polynomially enumerable

Status: **PROVED_IN_FROZEN_B2_SCOPE / GLOBAL_SELECTION_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Result

The active sparse-interface question asked for a polynomially enumerable structural macro language. For the frozen B2 extension rule, no special restricted vocabulary is needed at the **one-step proposal** level: every legal next extension definition can already be enumerated in polynomial time provided the current serialized state is polynomially bounded in the original input length.

The difficulty is therefore not candidate generation. It is selecting a globally useful candidate and proving global progress without semantic search or exponential backtracking across candidate sequences.

---

## 1. Frozen B2 rule

A new extension variable `e` is fresh and is defined by

`e <-> (a AND b)`

where `a,b` are signed literals over root variables or earlier extension variables, subject to the frozen legality rules (topological order, freshness, no forbidden self/forward reference, canonical operand handling, and `abs(a) != abs(b)` in the current B2 contract).

Its CNF definition uses the constant three-clause encoding

`(~e OR a)`,
`(~e OR b)`,
`(e OR ~a OR ~b)`.

---

## 2. Candidate-count theorem

Suppose the current state contains `V` available Boolean variables total (roots plus already admitted extension variables).

There are at most `2V` signed literals.

Hence the number of ordered literal pairs is at most

`(2V)^2 = 4 V^2`.

Applying legality filters can only reduce this number. If operand order is canonicalized for commutative AND, the actual number is smaller, but the quadratic upper bound is sufficient.

Therefore:

`#LEGAL_NEXT_B2_CANDIDATES <= 4 V^2`.

If the total serialized state is bounded by `N^c`, then necessarily `V <= N^c` up to ordinary encoding constants, and

`#CANDIDATES <= 4 N^(2c)`.

So the complete next-step B2 proposal deck is polynomial in the original input length whenever the state itself is polynomial.

---

## 3. Enumeration cost

A deterministic enumerator can:

1. list signed literals in canonical ID/sign order;
2. scan all ordered or canonical unordered pairs;
3. reject illegal pairs by syntactic checks;
4. assign the next fresh extension ID deterministically;
5. emit the constant-size three-clause definition.

Each pair check is polynomial in the bit-length of current IDs/metadata. Thus total one-step proposal work is polynomial in the explicit state size, and polynomial in original `N` under the frozen polynomial-state invariant.

No SAT oracle, model counting, semantic equivalence test, heuristic score, or backtracking is required merely to **enumerate** every legal next extension.

---

## 4. Important separation: one-step deck versus schema sequences

Polynomial one-step branching does not imply polynomial total search.

If there are at least two plausible choices at each of `K` extension steps, naive sequence enumeration can contain `2^K` branches. More generally, decks of sizes `M_1,...,M_K` produce

`product_i M_i`

possible sequences.

Therefore:

`POLY_ONE_STEP_CANDIDATE_DECK != POLY_GLOBAL_SCHEMA_SEARCH`.

The earlier schema-enumeration barrier remains intact.

---

## 5. What obligation is now discharged

For a polynomial-Akinator theorem built directly on frozen B2, the following local obligation can be marked **closed**:

**POLY_PROPOSAL:** enumerate all legal one-step extension definitions in polynomial time, assuming the current state remains polynomially bounded.

The remaining obligations are:

1. **POLY_STATE:** prove total retained proof/extension bytes stay polynomial in original `N`;
2. **PROGRESS_CERTIFICATE:** define a locally checkable certificate that an accepted candidate advances a globally sound potential;
3. **POLY_CERT_DISCOVERY:** find such a certificate/candidate deterministically in polynomial time;
4. **NO_BACKTRACKING:** never recover completeness by exponential candidate-sequence exploration;
5. **UNIVERSAL_AVAILABILITY:** every nonterminal state has an admissible certified move;
6. **GLOBAL_POTENTIAL:** initial potential `<= N^d` for fixed universal `d`, strict decrease per accepted step;
7. **TERMINAL_CORRECTNESS:** exact SAT/UNSAT decision at termination.

If all are proved, total SAT time is polynomial and `P=NP`. This remains a conditional closure chain.

---

## 6. Why exact usefulness remains the red point

Syntactic legality is cheap, but exact semantic usefulness is not.

Earlier selector-lift reductions show that questions such as whether a candidate extension is forced / whether a corresponding branch is semantically dead can encode UNSAT. Similarly, exact residual survival discovery is NP-complete in general circuit scope.

Therefore the selector cannot score all `O(V^2)` candidates using a free exact semantic oracle.

The next exact object must be a **proof-carrying progress certificate** whose verification is cheap and whose existence/discovery is proved structurally.

---

## 7. New gate — U1-C certified selection

Freeze a deterministic algorithm

`SELECT_CERTIFIED_B2(state)`

that scans at most the polynomial one-step candidate deck and either returns

`(candidate, progress_certificate)`

or `UNKNOWN`.

The universal closure burden is to prove that `UNKNOWN` never occurs on a nonterminal state while keeping certificate discovery and total state polynomial.

This is now the central Akinator question:

> not “can we list the possible next macros?” — yes;
> but “can we always recognize one globally progressing macro by a cheap proof-carrying certificate?”

Current status:

**B2_ONE_STEP_POLY_PROPOSAL = PROVED_IN_SCOPE**  
**B2_CERTIFIED_GLOBAL_SELECTION = OPEN**  
**POLYNOMIAL_AKINATOR = OPEN**  
**P_VS_NP = OPEN**

---

## 8. New laws

- `POLY_ONE_STEP_CANDIDATE_DECK != POLY_SCHEMA_TREE`
- `SYNTACTIC_LEGALITY != GLOBAL_USEFULNESS`
- `POLY_PROPOSAL != POLY_CERTIFICATE_DISCOVERY`
- `ALL_NEXT_B2_MACROS_CAN_BE_ENUMERATED_WITHOUT_A_SEMANTIC_ORACLE`
- `GLOBAL_EXPONENT_MUST_NOW_LIVE_AFTER_PROPOSAL_IF_POLY_STATE_IS_PRESERVED`
