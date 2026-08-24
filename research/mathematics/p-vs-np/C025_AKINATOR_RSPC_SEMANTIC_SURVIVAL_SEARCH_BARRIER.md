# C025 — Akinator RSPC: semantic-survival search barrier and witness-frontier width

Status: **PROVED_IN_GENERAL_CIRCUIT_SCOPE / RESTRICTED_SELECTOR_FRONTIER_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Question

The active Akinator gate asks for a polynomially enumerable language of structural B2 macro-candidates such that, at every nonterminal state, at least one candidate has a cheap progress certificate which can be found deterministically in polynomial time, without a semantic oracle and without backtracking.

This note isolates the first exact obstruction inside the proposed robust structural progress certificate (RSPC):

> a certificate of semantic survival can be cheap to **verify** while still being hard to **discover**.

The result below is about general Boolean-circuit/B2-DAG representations. It does **not** automatically establish the same hardness for the exact Sokolov self-reduction family; that source-matched restriction remains a separate gate.

---

## 1. Residual semantic survival

Let `C` be a Boolean circuit (equivalently, a B2 extension DAG after expansion of the allowed AND/NOT basis), and let `rho` be a partial assignment to root variables.

Define

`SURVIVE(C,rho) = 1`

iff the residual Boolean function `C|rho` is **nonconstant**.

Equivalently, there exist two total completions `alpha,beta` extending `rho` such that

`C(alpha) != C(beta)`.

A proof-carrying survival witness is therefore simply the pair `(alpha,beta)`.

### Verification

Given `(C,rho,alpha,beta)`, verify in polynomial time that:

1. `alpha` and `beta` extend `rho`;
2. both assignments cover all roots needed by `C`;
3. evaluate `C(alpha)` and `C(beta)`;
4. check that the two output bits differ.

Thus survival has a cheap explicit witness.

---

## 2. Theorem A — residual nonconstancy is NP-complete in the general circuit scope

### Membership in NP

The pair `(alpha,beta)` above is a polynomial-size witness and circuit evaluation is polynomial in the serialized circuit size.

### NP-hardness

Reduce SAT to residual nonconstancy.

Given a CNF `F(x_1,...,x_n)`, introduce one fresh root bit `z` and construct

`C_F(z,x) := z AND F(x)`.

Use the empty restriction `rho = empty`.

- If `F` is satisfiable, choose a satisfying assignment `a` for `x`.
  Then `C_F(0,a)=0` and `C_F(1,a)=1`; hence `C_F` is nonconstant.
- If `F` is unsatisfiable, then `F(x)=0` for every `x`, hence `C_F(z,x)=0` for every assignment; therefore `C_F` is constant.

So

`F in SAT  <=>  SURVIVE(C_F, empty)=1`.

The construction has linear overhead in the circuit/CNF encoding.

Therefore:

**GENERAL_RESIDUAL_NONCONSTANCY = NP_COMPLETE.**

By complement:

**GENERAL_RESIDUAL_CONSTANCY = coNP_COMPLETE.**

### Exact scientific meaning

This is a search/discovery barrier, not a lower bound on every restricted structural selector.

It proves the law:

`CHEAP_SURVIVAL_WITNESS_VERIFICATION != CHEAP_SURVIVAL_WITNESS_DISCOVERY`.

Unless one proves additional structure for the candidate language, replacing a semantic oracle by “just find two surviving assignments” does not solve the selector problem: in the general circuit scope that discovery task is already SAT-hard.

---

## 3. A constructive escape language: inherited bi-witness macros

To avoid semantic search, define a restricted proof-carrying language in which witness pairs are **constructed compositionally** rather than searched for.

For every represented function `g`, carry two explicit root assignments:

- `W0(g)` with `g(W0(g))=0`,
- `W1(g)` with `g(W1(g))=1`.

For a root literal the two witnesses are trivial.

For negation, swap them:

- `W0(NOT g) := W1(g)`
- `W1(NOT g) := W0(g)`.

For a candidate AND macro

`e := a AND b`,

a positive witness can be inherited without search whenever `W1(a)` and `W1(b)` are compatible on their shared root support. Then

`W1(e) := W1(a) union W1(b)`.

A zero witness needs only force one operand to zero; variables outside that operand's support can be filled canonically because they cannot change that operand's value.

### Local complexity

If the current state contains `V` available literals/macros, all ordered operand pairs can be enumerated in `O(V^2)` candidates. Compatibility of two explicit witnesses is polynomial in their serialized support size. Candidate verification and witness construction are therefore polynomial in the explicit state size.

This gives a genuine **proof-carrying structural candidate language with no semantic oracle for accepted steps**.

But universal progress is not yet proved.

---

## 4. Theorem B — one retained positive witness is not compositionally complete

A single inherited `W1(g)` per function can block an AND step even when the target conjunction is nonconstant.

Concrete Boolean example:

`a(x,y) := x OR y`

`b(x,y) := x OR NOT y`.

Both functions are nonconstant and their conjunction is satisfiable/nonconstant because every assignment with `x=1` makes both true.

However the valid positive witnesses

`W1(a) = (x=0,y=1)`

and

`W1(b) = (x=0,y=0)`

are incompatible, even though the alternative common positive witness `(x=1,y=0)` (or `(x=1,y=1)`) exists.

Hence a compositional selector that retains only one positive witness can return “no admissible AND macro” for this pair although a surviving conjunction exists.

This establishes:

`ONE_WITNESS_PER_VALUE != COMPLETE_COMPOSITIONAL_SURVIVAL`.

The counterexample is finite and explicit. It does not prove that every possible restricted macro language needs exponentially many witnesses.

---

## 5. New exact resource: witness-frontier width

For a represented function `g`, let `W1_frontier(g)` be the retained set of constructive positive witnesses available to later composition.

Define

`omega(g) := |W1_frontier(g)|`

and for a proof/selector state `S`

`Omega(S) := max_g omega(g)`.

For an AND candidate, naive compatibility join costs

`O(omega(a) * omega(b) * support_check_cost)`.

Therefore a hidden exponent can move from semantic search into the retained witness frontier.

The next exact gate is:

> Is there a universally complete proof-carrying selector language for the target hard-family states with `Omega(S) <= N^c` for one fixed universal constant `c`, while every next-step candidate is enumerable and selectable deterministically in polynomial time?

If yes, this is a concrete route toward the requested polynomial Akinator layer.

If no, the failure must identify where witness-frontier width or compatibility-join width becomes superpolynomial.

No superpolynomial lower bound on `Omega` is claimed here.

---

## 6. Selector bridge theorem

Suppose a selector has all of the following for every CNF of encoded length `N`:

1. states have polynomial serialized size;
2. at each nonterminal state, a polynomial-size candidate set is deterministically enumerable in polynomial time;
3. at least one candidate has a progress certificate;
4. such a candidate and certificate are deterministically found in polynomial time without backtracking/oracle calls;
5. the certificate is polynomial-time verifiable;
6. a globally sound integer potential decreases by at least one per accepted step;
7. the initial potential is at most `N^c` for a fixed universal `c`;
8. terminal states decide SAT correctly.

Then the entire selector run takes polynomial time and decides SAT. Therefore SAT is in P and hence `P=NP`.

This is a **conditional bridge theorem**, not a proof that such a selector exists.

It identifies the exact burden of proof: universal local availability + polynomial discovery + a polynomially bounded globally sound progress measure.

---

## 7. Interaction with the previous F3/F3D barriers

Existing frozen results already eliminate two weaker shortcuts:

- purely NW-neighborhood-local B2/ER3 macro vocabularies are insufficient on the transferred NW hard family;
- low `(negative-frontier width, inversion depth)` vocabularies cannot provide a polynomial escape in the stated F3 transfer scope;
- large pre-restriction `(b,d)` does not imply semantic survival because the F3D.D0 kill-switch family collapses under one root restriction.

The present note adds a different barrier:

- even if semantic survival is expressed by a short explicit witness, discovering that witness is NP-complete in the unrestricted circuit representation.

Thus the remaining route must exploit a restricted **constructive** representation whose witness frontier stays polynomial and whose completeness under the exact source-matched restrictions is proved.

---

## 8. Next gates

### RSPC-S1 — constructive candidate language

Freeze a candidate language whose accepted macros inherit survival witnesses without SAT/model-counting search.

### RSPC-S2 — witness-frontier accounting

Charge every retained witness and every compatibility join in original input length `N`; no “polynomial in cache size” shortcut.

### RSPC-S3 — no-backtracking completeness

Prove that every nonterminal target state has at least one admissible candidate under the frozen deterministic selector rule.

### RSPC-S4 — source-matched survival

Prove the certificate survives the exact Sokolov self-reduction relation/distribution. General-circuit NP-completeness does not settle this restricted gate.

### RSPC-S5 — global progress

Exhibit a globally sound potential of polynomial initial magnitude that strictly decreases on every accepted step and reaches a SAT-decision terminal state.

Until S1–S5 are discharged:

**PROOF_CARRYING_STRUCTURAL_SELECTOR = OPEN**  
**POLYNOMIAL_AKINATOR = OPEN**  
**P_VS_NP = OPEN**

---

## 9. New laws

- `CHEAP_SURVIVAL_WITNESS_VERIFICATION != CHEAP_SURVIVAL_WITNESS_DISCOVERY`
- `SHORT_ASSIGNMENT_WITNESS != POLYNOMIAL_WITNESS_SEARCH`
- `ONE_WITNESS_PER_VALUE != COMPLETE_COMPOSITIONAL_SURVIVAL`
- `POLYNOMIAL_CANDIDATE_ENUMERATION != UNIVERSAL_PROGRESS`
- `POLYNOMIAL_WITNESS_FRONTIER_MUST_BE_PROVED_IN_ORIGINAL_INPUT_LENGTH`
- `GENERAL_CIRCUIT_HARDNESS != SOURCE_MATCHED_RESTRICTION_HARDNESS`
- `LOCAL_PROGRESS_CERTIFICATE != GLOBAL_POLYNOMIAL_DECISION_PROCEDURE`
