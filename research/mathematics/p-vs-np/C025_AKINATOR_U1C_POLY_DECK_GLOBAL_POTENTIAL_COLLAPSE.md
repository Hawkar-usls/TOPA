# C025 — Akinator U1-C: polynomial B2 deck collapses selection to a cheap global descent potential

Status: **CONDITIONAL_CLOSURE_THEOREM_PROVED / POTENTIAL_CONSTRUCTION_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Main compression

U1-B proved that, under a polynomial current-state invariant, **all legal one-step frozen B2 extension candidates can be enumerated in polynomial time**. Therefore a separate mysterious candidate-generation oracle is unnecessary.

This note shows that if we can additionally construct a polynomially bounded, polynomially computable global descent potential, deterministic candidate selection becomes trivial by exhaustive scan of the already-polynomial one-step deck.

Thus the central positive route contracts to one object:

**CHEAP EXACT GLOBAL DESCENT POTENTIAL.**

---

## 1. Frozen assumptions

Let original CNF input length be `N`.

Assume a deterministic state machine with:

1. **POLY_STATE:** every reachable state `S` has at most `N^a` serialized bits for a fixed universal constant `a`;
2. **POLY_DECK:** every nonterminal state has a deterministically enumerable legal one-step candidate deck `D(S)` of size at most `N^b`; for frozen B2 this follows from the quadratic candidate-count theorem once state size is polynomial;
3. **POLY_TRANSITION:** for every candidate `c in D(S)`, `NEXT(S,c)` is computable in `N^t` time and either rejects the move syntactically or produces a valid next state;
4. **POTENTIAL:** an integer `mu(S)` is computable in `N^e` time, with `0 <= mu(S) <= N^d` for fixed universal `d`;
5. **UNIVERSAL_DESCENT:** for every nonterminal reachable state there exists at least one legal `c in D(S)` with
   `mu(NEXT(S,c)) < mu(S)`;
6. **TERMINAL_CORRECTNESS:** every state with no required continuation/with terminal potential condition yields an exact, independently checkable SAT witness or UNSAT proof/result according to the frozen solver semantics.

All exponents are fixed constants independent of the input/family.

---

## 2. Deterministic selection lemma

At a nonterminal state `S`:

1. enumerate all candidates in `D(S)`;
2. for each candidate in canonical order, compute `S' = NEXT(S,c)`;
3. compute `mu(S')`;
4. select the first legal candidate with `mu(S') < mu(S)`.

By UNIVERSAL_DESCENT, one exists.

The one-step work is bounded by

`|D(S)| * poly(N) = N^b * N^O(1) = N^O(1)`.

No semantic usefulness oracle and no candidate-sequence backtracking are required.

So:

**POLY_DECK + CHEAP_EXACT_DESCENT_POTENTIAL => POLY_ONE_STEP_CERTIFIED_SELECTION.**

---

## 3. Total-step bound

Because `mu` is a nonnegative integer, starts at at most `N^d`, and strictly decreases at every selected step, there are at most `N^d` accepted transitions.

Therefore total runtime is

`N^d * N^O(1) = N^O(1)`.

Together with terminal correctness this gives a deterministic polynomial-time SAT decider.

Hence:

**If all frozen assumptions 1–6 hold for every CNF, then `SAT in P`, and therefore `P = NP`.**

This is a conditional closure theorem, not evidence that the required potential exists.

---

## 4. What disappeared from the obligation list

Once POLY_STATE is assumed/proved and the frozen B2 deck theorem is used, the following is no longer an independent mystery:

- polynomial candidate proposal;
- choosing among polynomially many candidates, **provided** the exact potential is cheap.

The hidden exponent can therefore only survive in one or more of:

- state-size growth;
- transition/certificate update cost;
- potential evaluation cost;
- failure of universal descent;
- a potential range that is not polynomial in original `N`;
- terminal correctness/termination assumptions.

The candidate deck itself is not the source of exponential growth.

---

## 5. The tempting ideal potential hides proof search

A natural fantasy potential is

`mu(F) = length of a shortest refutation/proof from the current obligation`.

If this value and a decreasing next move were cheaply available, following an optimal proof would be immediate.

But even for the weaker Resolution proof system, proof search is known to be hard.

### External theorem

Albert Atserias and Moritz Müller, **Automating Resolution is NP-Hard**, Journal of the ACM 67(5), 2020, DOI 10.1145/3409472 (conference/preprint 2019).

They prove that finding a Resolution refutation only polynomially longer than a shortest one is NP-hard. More strongly, their gap result makes it NP-hard to distinguish formulas with polynomial-length Resolution refutations from formulas with no subexponential-length Resolution refutations.

Thus, unless `P=NP`, Resolution is not automatizable.

### Consequence for our route

This does **not** refute the JANUS goal — proving `P=NP` would of course invalidate the conditional `unless P=NP` obstruction.

It does establish a strict methodological law:

> `shortest-proof distance` / `distance to a proof` cannot be treated as a cheap known progress potential merely because short proofs exist.

For Resolution, exploiting that ideal distance generically already has NP-hard proof-search content.

The exact corresponding unconditional automatability status for full frozen B2/ER is not claimed here. Earlier project work records only the relevant ER/Extended-Frege p-equivalence and conditional cryptographic proof-search barriers with their own claim ceilings.

---

## 6. New exact gate — U1-D potential synthesis

We now seek a potential `mu` that is **strictly easier to compute than shortest-proof distance**, yet strong enough to guarantee a decreasing B2 move from every nonterminal state.

Admission requirements:

1. exact mathematical definition, not heuristic score;
2. `mu(S)` computable in polynomial time from the current serialized state;
3. `mu(S) <= N^d` with universal fixed `d`;
4. every legal transition's potential change computable without SAT/#SAT/equivalence oracle;
5. theorem of universal descent over the entire frozen solver state space;
6. no hidden dependence on producer-local history or exponentially large omitted frontier;
7. terminal zero/terminal condition implies exact solver completion.

Candidates to attack first:

- structural obligation count;
- unresolved proof-goal rank;
- extension/reason deficit under a frozen canonical goal decomposition;
- a lexicographic tuple of several polynomially bounded structural ranks.

Each must be falsified against selector-lifts, graph-PHP, NW-local/F3D collapse fixtures, and representation-reuse counterfamilies before admission.

---

## 7. Current state

`B2_ONE_STEP_POLY_PROPOSAL = PROVED_IN_SCOPE`

`CHEAP_EXACT_GLOBAL_DESCENT_POTENTIAL = OPEN`

`UNIVERSAL_DESCENT = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 8. New laws

- `POLY_DECK + CHEAP_EXACT_POLY_RANGE_DESCENT_POTENTIAL => POLY_SELECTION`
- `POLY_SELECTION + POLY_RANGE_STRICT_DESCENT => POLY_TOTAL_STEPS`
- `SHORTEST_PROOF_EXISTS != CHEAP_SHORTEST_PROOF_DISTANCE`
- `PROOF_DISTANCE_AS_POTENTIAL != FREE_PROGRESS_ORACLE`
- `CANDIDATE_ENUMERATION_IS_NO_LONGER_THE_PRIMARY_B2_EXPONENT`
- `THE_ACTIVE_RED_POINT_IS_GLOBAL_POTENTIAL_SYNTHESIS`
