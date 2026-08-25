# C025 — Akinator BC1-A: C-local substitution and restriction stability

Status: **PARTIAL GATE CLOSED / DIRECT SOURCE-ENCODING REUSE REFUTED FOR C>1**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Question

The bounded-cover lane showed that for every universal fixed constant `C`, exact residual survival of a B2 macro with an explicit cover by at most `C` frozen NW neighborhoods can be discovered in deterministic polynomial time in the actual direct-parity input length.

The next falsification-first gate is whether Sokolov's one-neighborhood functional-encoding machinery can be lifted from `C=1` to fixed `C>1`.

This note separates three statements that must not be conflated:

1. **cover/restriction stability**;
2. **a generalized C-hyperlocal functional-form substitution lemma**;
3. **identity with Sokolov's published functional encoding / heavy-width theorem**.

The first two hold. The third does not hold automatically for `C>1`.

---

## 1. Frozen definitions

Let `G=(L,R,E)` be the NW dependency graph and for `i in L` let

`Vars_i := N_G(i)`.

For a Boolean function `g` over root variables define an explicit `C`-cover certificate

`Cover(g)=I subseteq L`, `|I|<=C`,

such that

`Vars(g) subseteq U_I := union_{i in I} Vars_i`.

The cover is proof-carrying and need not be minimum.

A function is **C-local** iff it has such a verified cover.

For a B2 macro the inherited cover is the canonical union of the parent cover IDs; a gate is admitted into lane `BC-C` only when the inherited cover has size at most the frozen universal constant `C`.

---

## 2. Lemma BC1-A1 — support monotonicity under restriction

For every Boolean function `g` and every partial root assignment `rho`,

`Vars(g|rho) subseteq Vars(g) \ dom(rho)`.

### Proof

Fix any root variable `x` outside `Vars(g) \ dom(rho)`.

- If `x` was not in `Vars(g)`, changing `x` never changed `g` before restriction, hence cannot change `g|rho`.
- If `x in dom(rho)`, it is fixed and is not a free argument of `g|rho`.

Therefore every essential/free variable of the residual function comes from the original support and remains unassigned. QED.

---

## 3. Lemma BC1-B — exact cover stability under a Sokolov self-reduction

Let `rho` be a source self-reduction assigning exactly the right-side variables

`N_G(L_rho)`

for some set `L_rho subseteq L`, and let

`G' := G \ (L_rho union N_G(L_rho))`.

For a verified cover `I=Cover(g)`, define

`I' := I \ L_rho`.

Then

`Vars(g|rho) subseteq union_{i in I'} N_{G'}(i)`

and hence

`|I'| <= |I| <= C`.

### Proof

Take an arbitrary free variable `x in Vars(g|rho)`.

By BC1-A1, `x in Vars(g)` and `x notin N_G(L_rho)`. Since `I` covers `g`, there exists `i in I` with `x in N_G(i)`.

If `i in L_rho`, then `x in N_G(L_rho)`, contradiction. Hence `i in I'`.

Because `x notin N_G(L_rho)`, the edge/neighbor survives in the residual graph, so `x in N_{G'}(i)`.

Thus every free residual variable is covered by `I'`, and the cover cardinality cannot increase. QED.

### Consequence

`C_LOCALITY_IS_STABLE_UNDER_SOURCE_SELF_REDUCTION = PROVED`.

This statement is independent of the heavy-width lower bound.

---

## 4. Generalized C-hyperlocal functional form

Sokolov's published functional form groups literals into bags indexed by one output vertex `i`, because every source-local function depends on one `Vars_i`.

For fixed `C`, define instead **hyperbags** indexed by explicit cover sets `I subseteq L`, `|I|<=C`.

For a clause

`D = y_{g_1}^{c_1} OR ... OR y_{g_l}^{c_l}`

choose hyperbags `B_I` such that every literal assigned to `B_I` has a verified cover contained in `I`.

Define

`h_I(x) := OR_{y_g^c in B_I} (1 XOR c XOR g(x))`.

A generalized C-functional form is

`F_C(D) := OR_I (h_I(x)=1)`.

Non-uniqueness of covers/bags is allowed, just as source functional forms are non-unique.

---

## 5. Lemma BC1-A2 — generalized functional-form substitution survives restriction

For every partial root assignment `rho`, if `F_C(D)` is a generalized C-functional form of `D`, then

`F_C(D)|rho`

is a generalized C-functional form of `D|rho^y`, after replacing each function by its residual and each cover `I` by any verified residual subcover (in particular `I\L_rho` for a source self-reduction).

### Proof

Restriction commutes with the Boolean operations used inside each hyperbag:

`(1 XOR c XOR g(x))|rho = 1 XOR c XOR (g|rho)(x)`.

Therefore each restricted hyperbag function is exactly the OR of the restricted literals assigned to that hyperbag. By BC1-A1/BC1-B the old cover remains valid after deleting output vertices whose neighborhoods were fully assigned. Taking the OR of all residual hyperbags yields the restricted clause under normal assignment semantics. QED.

### Consequence

`C_HYPERLOCAL_FUNCTIONAL_FORM_RESTRICTION_LEMMA = PROVED_IN_GENERALIZED_ENCODING`.

This is an internal generalization of the syntactic mechanism behind Sokolov Lemma 12; it is **not** a claim that Sokolov published the C-local theorem.

---

## 6. The direct source-encoding identity fails for C>1

Sokolov's published functional encoding introduces `y_g` only when there exists a **single** output neighborhood `Vars_i` containing every variable on which `g` depends.

Take the finite graph

`Vars_1={x_1}`, `Vars_2={x_2}`

and

`g(x_1,x_2)=x_1 XOR x_2`.

Then `g` is 2-local with explicit cover `{1,2}`, but it is not source-local because neither `Vars_1` nor `Vars_2` contains both essential variables.

Hence the source functional encoding contains no variable `y_g` for this function.

Therefore:

`C_LOCAL_GENERALIZED_ENCODING == SOKOLOV_PUBLISHED_FUNCTIONAL_ENCODING`

is false in general for every `C>=2`.

### Exact verdict

`DIRECT_SOURCE_FUNCTIONAL_ENCODING_REUSE_FOR_C_GT_1 = REFUTED`.

This does **not** refute the possibility of a new fixed-C lower-bound transfer. It refutes only the shortcut of treating the enlarged proof language as if it were already covered by the published theorem.

---

## 7. Why the published single-output kill step also does not lift unchanged

In the source encoding, a function in bag `i` is fully determined once all roots in `Vars_i` are assigned. This is crucial to the one-output restriction/heavy-width mechanism.

For a 2-local function such as

`g=x_1 XOR x_2`, with `x_1 in Vars_1`, `x_2 in Vars_2`,

assigning only `Vars_1` does not determine `g`; it leaves dependence on `x_2`.

Thus a source step that chooses one output vertex and assigns its neighborhood cannot, in general, kill/determine a C-local hyperbag that spans multiple neighborhoods.

So:

`SOURCE_SINGLE_OUTPUT_KILL_LEMMA_EXTENDS_VERBATIM_TO_C_LOCAL = REFUTED`.

A valid BC1-C proof would need a new multi-output/hyperbag restriction argument, or a reduction from C-local macros back to the one-local source language with a proved polynomial overhead.

---

## 8. What the organism contributes

The cross-repository JANUS line points to one consistent architecture:

- pre-birth quotienting/orbit discovery: historical Tranception P-vs-NP diagnostics;
- candidate-generator / exact-verifier separation: Quantum/Physarum fail-closed result;
- lineage/EXIT accounting: OdontoForge bridge;
- total-work rather than latency accounting: P-N selective distributed field;
- proof authority: Janus-Fundamentum;
- epistemic/claim firewall: TOPA;
- adversarial decomposition and preserved disagreement: Demi_Head;
- provenance memory: janus-meta-registry.

These patterns motivate the next construction, but none is imported as a mathematical theorem without an explicit reduction.

---

## 9. New next gate — BC1-C-HYPER

The falsification-first question is now narrower:

> Can one prove a heavy-width/size lower bound for a proof system with fixed-C hyperlocal extension variables, where each extension function depends on the union of at most C original NW neighborhoods?

Two admissible routes:

1. **Multi-output restriction:** choose/assign bounded sets of output neighborhoods so every selected hyperbag is fully determined, while preserving enough expansion and obtaining a size-to-hyperwidth reduction.
2. **Simulation reduction:** compile every fixed-C hyperlocal proof into a one-local/source proof with only polynomial overhead.

The second route is immediately suspect for arbitrary Boolean functions on a union of C neighborhoods and must be attacked with explicit counterexamples before being assumed.

---

## 10. Claim ledger

`BC1_A_C_LOCAL_SUBSTITUTION = PROVED_FOR_GENERALIZED_C_HYPERLOCAL_ENCODING`

`BC1_B_RESTRICTION_STABILITY = PROVED`

`DIRECT_SOURCE_ENCODING_IDENTITY_FOR_C_GT_1 = REFUTED`

`SOURCE_SINGLE_OUTPUT_KILL_EXTENDS_VERBATIM = REFUTED`

`BC1_C_FIXED_C_HEAVY_WIDTH_TRANSFER = OPEN`

`FIXED_C_GT_1_UNIVERSAL_SELECTOR_SUFFICIENCY = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 11. New laws

- `COVER_STABILITY != SOURCE_THEOREM_TRANSFER`
- `GENERALIZED_FUNCTIONAL_FORM != PUBLISHED_FUNCTIONAL_ENCODING`
- `ONE_OUTPUT_DETERMINES_ONE_LOCAL_FUNCTION != ONE_OUTPUT_DETERMINES_C_LOCAL_FUNCTION`
- `FIXED_C_EXACT_SURVIVAL_CAN_BE_POLYNOMIAL_WHILE_FIXED_C_PROOF_COMPLEXITY_REMAINS_OPEN`
- `DO_NOT_PROMOTE_A_SYNTACTIC_GENERALIZATION_TO_A_SOURCE_THEOREM_WITHOUT_REPROVING_THE_LOWER_BOUND`
