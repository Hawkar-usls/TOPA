# PF5 Slime Capped PS-width Compiler v12

Status: **FROZEN BEFORE PROVIDER RUN**  
Claim ceiling: **P_VS_NP = OPEN**

## Purpose

Remove the forbidden exact-PS-score selector from the Slime incidence-decomposition lane.

PF5 v9-v11 used an independent exponential scorer only as an audit oracle. That is valid for finite evaluation but cannot select a runtime candidate in a polynomial SAT claim. v12 instead runs each frozen Slime candidate through a **bounded exact PS-state compiler** derived directly from the Sæther–Telle–Vatshelle (STV) preprocessing recurrence.

A candidate may terminate only as:

- `CLOSED_PSWIDTH_CAP` — every required precisely-satisfiable state family was constructed under the frozen cap;
- `OPEN_STATE_CAP` — the first state family exceeded the cap, with partial failure receipt;
- `INVALID_ORDER` / `INVALID_SOURCE` — structural rejection.

There is no general SAT fallback and no exact-width oracle.

## Published bridge

For a CNF formula with a supplied branch decomposition of PS-width `k`, STV prove:

1. all `PS(F_v)` and `PS(F_bar_v)` families can be computed in
   `O(k^2 log(k) m (m+n))`;
2. #SAT and weighted MaxSAT can then be solved in
   `O(k^3 s (m+n))`.

Therefore, if one could universally generate in polynomial time a polynomial-sized candidate family containing a decomposition of PS-width at most `N^q` for one **fixed universal exponent q**, then a bounded dovetailing compiler over the portfolio would be polynomial and would imply a polynomial SAT algorithm.

v12 does **not** prove that universal candidate-completeness statement.

## Pinned Slime producer

The runtime producer is the already validated order-equivalent amortized v3 implementation:

`Hawkar-usls/Janus-Demiurge@421794b5c7e3b96f52550cf710fe2d8d2f3b59db`

Module:

`models/slime/slime_semantic_candidate_swarm_v3_amortized.py`

Its 16 candidate orders are exactly equal to v2 on the frozen v10/v11 corpus, while charged candidate discovery is lower.

## Native incidence decomposition

No C039/C040 variable-vtree coercion is used.

Each Slime order is an order of the **incidence leaves**:

`{v:x} union {c:i}`.

v12 interprets that order as the leaf order of a right-linear / caterpillar branch decomposition of the formula, exactly matching the STV/C032 PS-width type.

This avoids the type error of treating an incidence decomposition as a C039 variable-only vtree.

## Exact recurrence implemented

For a branch-decomposition node `v` with children `c1,c2`:

`PS(F_v) = { (A union B) \ cla(delta(v)) : A in PS(F_c1), B in PS(F_c2) }`.

For child `v`, sibling `s`, parent `p`:

`PS(F_bar_v) = { (A union B) intersect cla(delta(v)) : A in PS(F_s), B in PS(F_bar_p) }`.

Base states are computed directly:

- variable leaf `x`: at most two signatures, one for `x=0`, one for `x=1`;
- clause leaf: `{empty}`;
- complement of root: `{empty}`.

All clause identities are original source clause indices, so duplicate clauses remain distinct exactly as in the STV definition.

## Frozen runtime cap

Let

`r = #variables + #clauses`

be the number of incidence leaves.

v12 freezes the state cap exponent **before provider execution**:

`q = 1`

and therefore

`K(F) = max(2, r)`.

This is an engineering theorem-probe cap, not a claimed universal exponent.

Every state constructor inserts canonical signatures one by one and stops immediately when it would store `K+1` distinct signatures. Since every successful operand has size at most `K`, every binary recurrence attempts at most `K^2` pairs. With `O(r)` tree nodes, each candidate attempt is polynomially bounded by construction.

The complete 16-candidate portfolio is therefore bounded by a fixed constant factor times this polynomial work, plus the already charged polynomial Slime v3 generation cost.

## Proof-carrying certificate

A `CLOSED_PSWIDTH_CAP` result stores, for every leaf/internal node:

- canonical leaf-set digest;
- canonical `PS(F_v)` signature list + digest;
- canonical `PS(F_bar_v)` signature list + digest;
- cardinalities;
- recurrence parent/sibling references;
- total and peak state sizes;
- exact pair-attempt / set-operation ledger.

An independent replay function reconstructs every state from the source formula and candidate order and compares the full certificate digest.

An `OPEN_STATE_CAP` result stores:

- phase (`FORWARD` or `COMPLEMENT`);
- exact node;
- frozen cap;
- first `K+1` distinct canonical signatures;
- pair attempts and work performed before refusal.

`OPEN_STATE_CAP` is portfolio/cap scoped and is never promoted to hardness.

## Frozen controls

### Fresh connected-3CNF runtime controls

Seeds frozen now, after the v3 producer was fixed:

`[908000, 908001, 908002, 908003, 908004, 908005, 908006, 908007, 908008, 908009, 908010, 908011, 908012, 908013, 908014, 908015]`

Each source uses the unchanged connected signed 3-CNF generator:

- `n=7`
- `m=10`
- five chain-backbone clauses plus seeded random signed 3-clauses.

### Larger fresh connected-3CNF controls

Seeds:

`[908100, 908101, 908102, 908103, 908104, 908105, 908106, 908107]`

- `n=9`
- `m=14`.

These may return either CLOSED or OPEN; CI must not assume the outcome.

### Known positive semantic-gap control

`DUPLICATE_K6_6`: six identical copies of `(x1 OR ... OR x6)`.

C032 proves every cut PS-value is at most two; v12 must close under `K=12`.

### Fail-fast canaries

`UNIT_N8_LEXICAL` and `UNIT_N10_LEXICAL` are manual lexical incidence orders for unit-clause families. Their exact bad cuts have `2^8` and `2^10` signatures respectively, so under the frozen linear cap (`K=16` and `K=20`) they must return `OPEN_STATE_CAP` **without constructing the full exponential family**.

These lexical canaries are validation-only and are not inserted into the Slime selectable portfolio.

## Selection rule

All 16 Slime candidates are attempted under the same frozen cap. No candidate is created or repaired after outcomes.

Among `CLOSED_PSWIDTH_CAP` candidates choose deterministically by:

`(peak_ps_state, total_ps_states, pair_attempts, certificate_bytes, order_digest)`.

If none closes:

`OPEN_PORTFOLIO_CAP_EXHAUSTED`.

The selector uses only bounded compiler receipts; it never asks for the true optimal width.

## Frozen questions

1. Can the STV PS-state preprocessing be replayed exactly from Slime incidence orders with no assignment enumeration?
2. Do the unit canaries fail immediately near `K+1`, rather than materializing 2^n states?
3. On fresh connected 3-CNF controls, how many of the 16 v3 candidates close under the fixed linear cap?
4. Are all candidate failures globally polynomially bounded and charged?
5. Does the selected candidate certificate independently replay from source bytes/order only?

## The exact remaining theorem gate

After v12, the universal statement needed for P=NP would be:

`EXISTS_FIXED_q_AND_POLY_SLIME_PORTFOLIO_SUCH_THAT_FOR_EVERY_CNF_SOME_CANDIDATE_HAS_PSWIDTH_AT_MOST_N^q`.

Equivalently, the engineering problem is no longer “how do we score a candidate?”; bounded compilation already supplies a polynomial fail-closed selector **conditional on a fixed polynomial cap**.

What remains open is the universal completeness of the candidate/decomposition family under one fixed exponent.

## Prohibitions

- no exponential assignment enumeration inside the runtime compiler;
- no call to the v9 exact audit scorer for runtime selection;
- no input-dependent cap exponent;
- no raising `q` after seeing an OPEN source;
- no post-probe candidate generation;
- no general SAT fallback;
- no OPEN-to-hardness promotion;
- no `P=NP` claim.

`P_VS_NP = OPEN`
