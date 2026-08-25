# C025 — Akinator RSPC: bounded-cover exact survival without a semantic oracle

Status: **PROVED_FOR_FROZEN_DIRECT_NW_PARITY_ENCODING / UNIVERSAL_SELECTOR_COMPLETENESS_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why this matters

The previous RSPC note proves that residual nonconstancy is NP-complete for unrestricted Boolean circuits/B2 DAGs. That does not rule out a restricted structural language in which exact survival is constructively discoverable.

For the frozen direct NW-parity hard family, such a restricted lane exists.

The key accounting fact is that the encoded input already pays exponentially in the single-neighborhood degree `Delta`: each output parity constraint is represented directly by all clauses forbidding wrong local assignments.

For each output neighborhood of size `Delta`, the direct parity CNF contributes exactly

`2^(Delta-1)`

width-`Delta` clauses.

Therefore for actual encoded input length `N`:

`2^(Delta-1) <= N`, hence `2^Delta <= 2N`.

This converts exhaustive evaluation on a **fixed number of neighborhoods** into a polynomial-in-`N` operation.

---

## 1. Explicit cover certificate

Do not ask for a minimum neighborhood cover; minimum-cover discovery could itself hide search complexity.

Instead every macro carries an explicit, proof-carrying cover certificate

`Cover(e) = [i_1,...,i_c]`

such that

`supp(e) subseteq Vars_{i_1} union ... union Vars_{i_c}`.

The certificate need not be minimum.

Verification is polynomial: compute the exact syntactic transitive root support already carried by B2, union the listed frozen NW neighborhoods, and check containment.

For a local macro, `c=1`.

For `e := a AND b` or `e := NOT a`, a deterministic inherited cover is obtained by canonical union of parent cover IDs.

Thus no set-cover oracle is required.

---

## 2. Theorem C — fixed-cover exact residual survival is polynomial in actual encoded input length

Let `e` be a serialized B2 macro/circuit over the frozen direct NW-parity instance. Suppose a verified cover certificate has size

`|Cover(e)| <= C`

for one universal fixed constant `C` independent of the input instance.

Each NW neighborhood has at most `Delta` roots, so

`|supp(e)| <= C*Delta`.

Under any supplied partial root restriction `rho`, determine whether `e|rho` is nonconstant by exhaustive evaluation of all completions on the unassigned roots in `supp(e)`.

The number of assignments is at most

`2^(C*Delta) = (2^Delta)^C <= (2N)^C`.

Circuit evaluation per assignment is polynomial in the serialized macro/state size.

Therefore, assuming the explicit state/macro serialization itself remains polynomial in original input length `N`, exact residual nonconstancy and an explicit differing-output witness pair can be found deterministically in

`poly(N) * (2N)^C = N^O(C)`

time.

Because `C` is a fixed universal constant, this is polynomial time in `N`.

### Consequence

For the bounded-cover lane:

`EXACT_SURVIVAL_DISCOVERY_REQUIRES_SEMANTIC_ORACLE = FALSE`.

A semantic oracle is unnecessary; exact enumeration suffices.

This is a positive algorithmic result for the restricted lane. It does not prove that the lane contains a globally sufficient selector step at every state.

---

## 3. Hidden exponent exposed

Let

`c(e) := |Cover(e)|`

for the inherited explicit cover certificate.

The same exact enumerator costs

`N^O(c(e))`.

If `c(e)` is allowed to grow with the input, the exponent is no longer a universal fixed constant.

Thus the relevant hidden-exponent law is

`N^O(c(N)) IS POLYNOMIAL ONLY IF c(N)=O(1) WITH A UNIVERSAL FIXED BOUND`.

Equivalent support-ratio form:

`r(e) := ceil(|supp(e)| / Delta)`.

Truth-table survival discovery costs at most approximately

`N^O(r(e))`.

This does **not** prove that every algorithm needs this cost. It identifies the exact exponent of the no-oracle exhaustive-survival route.

---

## 4. Interaction with earlier barriers

### C=1

The previously proved NW-neighborhood-local ER3 lower bound eliminates a universal polynomial escape restricted to `C=1` on the frozen hard family.

So the first positive exact-survival lane is algorithmically cheap but proof-complexity insufficient at `C=1`.

### C>1 fixed

For every fixed `C>1`, exact survival discovery remains polynomial by Theorem C.

What is **not** currently proved is whether some fixed `C` suffices for universal selector progress on the transferred hard family.

Therefore the new exact question is:

> Is there a universal constant `C*` such that a deterministic proof-carrying selector restricted to macros with verified cover size at most `C*` always has a globally useful next step?

If yes, the semantic-search obstruction is gone in that lane and the remaining burden is candidate completeness + global progress.

If no, then any successful selector must use `c(N) -> infinity`, and the exact truth-table route exposes the next growing exponent.

No lower bound excluding every fixed `C>1` is claimed here.

---

## 5. Polynomial candidate enumeration

Suppose the explicit selector state contains `V` available B2 literals/macros, each with verified cover size at most `C`.

One-step B2 candidates are:

- `NOT a`, at most `O(V)`;
- `a AND b`, at most `O(V^2)` ordered pairs.

For each candidate:

1. construct inherited cover by canonical union;
2. reject if cover size exceeds frozen `C`;
3. otherwise run exact residual-survival enumeration in `N^O(C)` time;
4. if nonconstant, export the first canonical differing-output witness pair as the proof-carrying survival certificate.

For fixed `C` and polynomial explicit `V(N)`, this entire candidate scan is deterministic polynomial time in original `N`.

Hence:

**BOUNDED_COVER_CANDIDATE_ENUMERATION_PLUS_EXACT_SURVIVAL_DISCOVERY = POLYNOMIAL_FOR_FIXED_C.**

No heuristic ranking and no semantic oracle are needed.

---

## 6. What is still missing from a polynomial Akinator

The above solves only the **discovery of a surviving bounded-cover macro**, assuming one exists.

It does not yet prove:

1. **Availability:** at every nonterminal target state, at least one candidate with cover `<=C` survives and is proof-progress useful.
2. **Progress:** semantic nonconstancy is not itself a proof-progress measure.
3. **Termination:** repeated accepted steps reach a SAT-decision terminal state in polynomially many steps.
4. **State-size control:** `V`, proof DAG bytes, witness bytes, and support/cover certificates remain polynomial in original `N`.
5. **Source transfer:** the exact accepted macro must satisfy the source-matched transfer conditions needed by the frozen lower-bound/self-reduction argument.

Thus:

`SURVIVAL != GLOBAL_PROGRESS`.

---

## 7. New frozen selector lane — BC-C

For a chosen universal constant `C`, define `BC-C`:

- explicit B2 state;
- explicit inherited neighborhood-cover certificate for each macro;
- candidate language `NOT` + ordered `AND` pairs;
- reject candidate if inherited cover exceeds `C`;
- exact truth-table residual survival test;
- canonical first surviving candidate in ID order;
- no heuristic score;
- no SAT/model-counting oracle;
- no backtracking.

Complexity ceiling:

`T_step <= poly(V, state_bytes) * 2^(C*Delta) <= poly(N) * N^O(C)`

provided all explicit state quantities are polynomial in original `N`.

### Frozen experiment sweep

Test `C=1,2,3,...` on finite transferred instances, but never infer a universal constant from finite success.

- `C=1`: analytically insufficient on the frozen hard family.
- `C>=2`: finite mechanics may be explored; universal completeness remains open.

---

## 8. Next theorem gates

### BC1 — fixed-C lower-bound transfer

Can the Sokolov heavy-width transfer be strengthened from one-neighborhood local functions to functions covered by at most fixed `C` neighborhoods?

If yes for every fixed `C`, then any successful selector requires `c(N)->infinity`.

### BC2 — fixed-C constructive progress

Alternatively, find a fixed `C` and prove every nonterminal target state has a BC-C candidate with a globally sound progress certificate.

### BC3 — cover-growth lower bound

If fixed-C fails, quantify the minimum necessary `c(N)` for polynomial-size escapes.

### BC4 — total exponent firewall

Charge

`V(N)`, `state_bytes(N)`, `c(N)`, `Delta(N)`, witness bytes, and evaluation bit complexity

in original encoded `N`.

---

## 9. Claim ledger

`GENERAL_RESIDUAL_NONCONSTANCY_NP_COMPLETE = PROVED_IN_GENERAL_CIRCUIT_SCOPE`

`FIXED_C_BOUNDED_COVER_EXACT_SURVIVAL = DETERMINISTIC_POLYNOMIAL_FOR_FROZEN_DIRECT_NW_PARITY_ENCODING`

`C_EQ_1_UNIVERSAL_SELECTOR_ESCAPE = REFUTED_IN_STATED_NW_LOCAL_ER3_SCOPE`

`EXISTS_FIXED_C_GT_1_UNIVERSALLY_SUFFICIENT = OPEN`

`EVERY_FIXED_C_INSUFFICIENT = NOT_PROVED`

`COVER_GROWTH_SUPERCONSTANT = NOT_PROVED`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 10. New laws

- `GENERAL_SEARCH_HARDNESS_CAN_DISAPPEAR_UNDER_A_SOURCE_MATCHED_BOUNDED_SUPPORT_REGIME`
- `INPUT_ALREADY_PAYS_2^DELTA`
- `2^(C*DELTA) <= (2N)^C FOR_FIXED_C_ON_DIRECT_PARITY_ENCODING`
- `FIXED_C != INPUT_DEPENDENT_C_N`
- `EXPLICIT_COVER_CERTIFICATE_AVOIDS_MINIMUM_SET_COVER_SEARCH`
- `EXACT_SURVIVAL_DISCOVERY != GLOBAL_PROOF_PROGRESS`
