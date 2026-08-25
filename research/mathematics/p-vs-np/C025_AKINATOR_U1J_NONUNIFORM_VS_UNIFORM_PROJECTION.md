# C025 — Akinator U1-J: nonuniform versus uniform exact projection

Status: **NONUNIFORM_SIZE_EQUIVALENCE_PROVED / UNIFORM_CONSTRUCTOR_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The active projection-compression program must distinguish two different frontiers:

1. every existential projection **has** polynomial-size circuits;
2. such circuits can be **constructed deterministically in polynomial time**.

The first frontier is exactly the nonuniform question `NP subseteq P/poly` in the broad circuit-projection setting. The second is the uniform route which, with the frozen total-cost conditions, reaches `P=NP`.

---

## 1. Universal projection-size property

Define `UPS` (Universal Projection Succinctness): there is one fixed polynomial `p` such that for every Boolean/B2 circuit `C(w,y)` of size `s`, the projected function

`D_C(y) := exists w C(w,y)`

has some Boolean/B2 circuit of size at most `p(s)` (ordinary input-index encoding factors absorbed into the fixed polynomial).

No algorithm for finding `D_C` is required by UPS.

---

## 2. UPS implies NP subseteq P/poly

Let `L in NP`. For every input length n, compile a polynomial-time verifier into a polynomial-size circuit

`V_n(x,w)`

such that

`x in L iff exists w V_n(x,w)=1`.

By UPS, the projected function

`D_n(x)=exists w V_n(x,w)`

has polynomial-size circuits.

Therefore `L in P/poly`. Since L was arbitrary:

**UPS => NP subseteq P/poly.**

---

## 3. NP subseteq P/poly implies UPS

Assume `NP subseteq P/poly`.

Consider the universal projection language

`U = { (<C>, y) : exists w C(w,y)=1 }`.

`U` is in NP: `w` is a polynomial witness relative to the explicit circuit description and C can be evaluated in polynomial time.

Hence, by the assumption, U has a polynomial-size circuit family indexed by the total input length.

Now fix one particular circuit C. Take the appropriate circuit for U and hardwire the bits of `<C>` into it. The remaining live inputs are y, and the resulting circuit computes exactly

`y -> exists w C(w,y)`.

Hardwiring cannot increase circuit size. Since the U-circuit size is bounded by one fixed polynomial in the total encoding length, and the number of live variables/wires is bounded by the explicit size of C up to standard encoding factors, the resulting projected circuit has size polynomial in |C|.

Therefore UPS holds.

So:

**UNIVERSAL_POLY_PROJECTION_SIZE_EXISTENCE iff NP subseteq P/poly.**

This is a nonuniform equivalence.

---

## 4. External Karp–Lipton consequence

Karp–Lipton (with the standard Sipser refinement) gives

`NP subseteq P/poly => PH = Sigma_2^p`.

Thus UPS would collapse the Polynomial Hierarchy to its second level.

References: Karp–Lipton; Arora–Barak, *Computational Complexity*, circuit-complexity chapter / Karp–Lipton theorem; standard modern complexity lecture notes.

This is not an unconditional contradiction: neither `NP subseteq P/poly` nor the corresponding PH collapse has been ruled out unconditionally.

---

## 5. Negative size lower bound is a major circuit lower bound

Because UPS is equivalent to `NP subseteq P/poly`, disproving UPS by exhibiting a polynomial-size verifier/circuit family whose existential projections require superpolynomial circuit size would prove

`NP not subseteq P/poly`.

That would in particular imply `P != NP` and would constitute a major general circuit lower bound.

Therefore a general unconditional lower bound on minimum B2/circuit projection size is not a routine representation lemma; it reaches a central open circuit-complexity frontier.

---

## 6. Uniform construction remains stronger

A `P/poly` circuit family may contain nonuniform advice. Existence does not give a polynomial-time machine that finds the circuit.

Now assume instead a deterministic `PROJECT` algorithm which, for every polynomial-size current B2 state, constructs an exactly equivalent projected quantifier-free B2 state in globally polynomial total time/state and without hidden oracles/backtracking.

Eliminate all SAT variables and evaluate the zero-variable result. This decides SAT in deterministic polynomial time.

Hence

**UNIFORM_POLY_EXACT_PROJECTION_CONSTRUCTION => SAT in P => P=NP.**

The converse semantic uniform-compilation implication is recorded separately in U1-K: under `P=NP`, polynomial-time computation can be circuitized uniformly to construct the projected Boolean function.

---

## 7. Three obligations stay separate

### SIZE
Does a polynomial-size exact projected circuit exist?

### DISCOVERY / CONSTRUCTION
Can it be found deterministically in polynomial time?

### CERTIFICATION
Can exact projection equivalence be justified by a polynomial proof object in the chosen proof system?

None is free from the others. In particular, `P=NP` does not automatically imply that the specific Extended-Resolution system is p-bounded.

---

## 8. Current status

`UNIVERSAL_POLY_PROJECTION_SIZE_EXISTENCE iff NP_SUBSET_P_POLY = PROVED`

`KARP_LIPTON_CONSEQUENCE = EXTERNAL_THEOREM`

`UNIVERSAL_UNIFORM_PROJECTION_CONSTRUCTOR = OPEN`

`GENERAL_PROJECTION_SIZE_LOWER_BOUND_WOULD_IMPLY_NP_NOT_SUBSET_P_POLY`

`P_VS_NP = OPEN`

---

## 9. New laws

- `POLY_PROJECTION_SIZE_EXISTENCE = NONUNIFORM_FRONTIER`
- `UNIVERSAL_PROJECTION_SIZE_FRONTIER iff NP_SUBSET_P_POLY`
- `NONUNIFORM_COMPRESSION != UNIFORM_ALGORITHM`
- `GENERAL_PROJECTION_SIZE_LOWER_BOUND_IS_A_GENERAL_CIRCUIT_LOWER_BOUND`
- `PROJECTION_SIZE_THEOREM_MUST_NOT_BE_PROMOTED_TO_P_EQUALS_NP_WITHOUT_UNIFORMITY`
