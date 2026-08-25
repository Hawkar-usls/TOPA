# C025 — Akinator U1-J: nonuniform versus uniform exact projection

Status: **CLAIM_CEILING_FIREWALL_PROVED / UNIFORM_CONSTRUCTOR_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The active projection-compression program must distinguish two very different statements:

1. every relevant existential projection **has** a polynomial-size circuit;
2. such a circuit can be **constructed deterministically in polynomial time**.

The first is nonuniform and does not by itself prove `P=NP`. The second, with the frozen exactness and total-cost conditions, would.

---

## 1. Nonuniform projection-size hypothesis

Let `L` be any language in NP. There is a polynomial-time verifier `V(x,w)` with polynomial witness length such that

`x in L iff exists w V(x,w)=1`.

For each input length `n`, compile the verifier into a polynomial-size Boolean/B2 circuit

`C_n(x,w)`.

Assume the following **existence-only** hypothesis:

> there is one fixed polynomial `p` such that for every such polynomial-size circuit `C_n`, the projected Boolean function
>
> `D_n(x) := exists w C_n(x,w)`
>
> has some Boolean/B2 circuit of size at most `p(|C_n|)`.

Then `D_n` decides `L` on n-bit inputs and has polynomial size.

Therefore

`L in P/poly`.

Since `L` was arbitrary:

**UNIVERSAL_POLY_PROJECTION_SIZE_EXISTENCE => NP subseteq P/poly.**

No algorithm for finding the circuits `D_n` is implied.

---

## 2. External Karp–Lipton consequence

Karp–Lipton (with the standard Sipser refinement) gives:

`NP subseteq P/poly => PH = Sigma_2^p`.

Thus a universal polynomial existential-projection size theorem would already have a major complexity-theoretic consequence even without a uniform constructor.

References:

- Richard M. Karp and Richard J. Lipton, classic Karp–Lipton theorem.
- Arora–Barak, *Computational Complexity*, Theorem 6.13: if `NP subseteq P/poly`, the polynomial hierarchy collapses to its second level.
- Modern university lecture notes state the same theorem.

This is not a contradiction: `NP subseteq P/poly` and the corresponding PH collapse are not known to be false unconditionally.

---

## 3. Why existence alone is insufficient for P=NP

A `P/poly` circuit family may contain nonuniform advice. The definition only asserts that for every input length a suitable polynomial-size circuit exists; it does not require a polynomial-time Turing machine to construct that circuit family.

Therefore:

`SMALL_PROJECTED_CIRCUIT_EXISTS != POLYNOMIAL_PROJECTION_ALGORITHM`.

In particular, the existence-only theorem must not be promoted to `SAT in P` or `P=NP`.

---

## 4. Uniform constructor implication

Now assume a much stronger statement in the frozen JANUS setting:

There is a deterministic algorithm `PROJECT` which, for every polynomial-size current B2 state and selected root variable/block, outputs in polynomial total time an exactly equivalent quantifier-free projected B2 state, with globally polynomial serialized size and a polynomially checkable correctness certificate.

If this operation can eliminate all SAT variables while preserving the global polynomial bounds, the algorithm reaches a zero-variable state in polynomially many certified stages and decides SAT exactly.

Hence:

**UNIFORM_POLY_EXACT_PROJECTION_CONSTRUCTION => SAT in P => P=NP.**

This is the actual positive closure target.

---

## 5. Three distinct obligations

The projection program should therefore track separately:

### SIZE

Does a polynomial-size exact projected B2 circuit exist?

### DISCOVERY / CONSTRUCTION

Can such a circuit be found deterministically in polynomial time?

### CERTIFICATION

Can exact projection equivalence be verified by a polynomial proof object without a semantic oracle?

None of these implies the other for free.

The current research has already exposed barriers in each direction:

- naive projection representations can grow exponentially;
- cofactor enumeration can be exponential even when a small projection exists;
- semantic target recognition is coNP-complete;
- brute-force polynomial-size block search is exponential;
- proof verification can be cheap while proof/circuit discovery remains hard.

---

## 6. New exact gate — U1-K uniformity before closure

Any future `P=NP` claim from projection compression must explicitly prove all of:

1. a fixed polynomial global size bound in original input `N`;
2. a deterministic polynomial-time constructor;
3. polynomial total proof/certificate bytes;
4. polynomial certificate verification;
5. no hidden nonuniform advice/table of exceptional circuits;
6. no semantic SAT/#SAT/equivalence oracle;
7. no exponential search over candidate replacement blocks;
8. exact terminal SAT/UNSAT correctness.

If only item 1 is proved in the broad verifier-projection setting, the correct ceiling is at most the nonuniform implication `NP subseteq P/poly`, with the Karp–Lipton PH-collapse consequence.

---

## 7. Current status

`POLY_PROJECTION_SIZE_EXISTENCE = OPEN`

`UNIVERSAL_UNIFORM_PROJECTION_CONSTRUCTOR = OPEN`

`EXISTENCE_ONLY_WOULD_IMPLY_NP_SUBSET_P_POLY = PROVED`

`KARP_LIPTON_CONSEQUENCE = EXTERNAL_THEOREM`

`P_VS_NP = OPEN`

---

## 8. New laws

- `POLY_CIRCUIT_EXISTENCE != POLY_CIRCUIT_CONSTRUCTION`
- `NONUNIFORM_COMPRESSION != UNIFORM_ALGORITHM`
- `NP_SUBSET_P_POLY != P_EQUALS_NP`
- `PROJECTION_SIZE_THEOREM_MUST_NOT_BE_PROMOTED_TO_P_EQUALS_NP_WITHOUT_UNIFORMITY`
- `DISCOVERY_REMAINS_A_SEPARATE_CLOSURE_OBLIGATION`
