# PF5 Connected Boundary Adhesion v3.1 — ADH-001 affine-wing repair

Status: **FROZEN REPAIR / SAME CONTROLS / SAME CAPS**  
Claim ceiling: **P_VS_NP = OPEN**

## Why v3 needs a repair replay

The first frozen provider receipt for v3 reached exact JOIN/witness closure at `k=2,4`, but the first cap hit occurred at `k=6` in `PRIVATE_PROJECTION` because the chosen frozen-order OBDD wing exceeded `OBDD_MAX_NONTERMINAL_NODES=192`.

That receipt is preserved as `ADH-001`:

> the first v3 escape measured an **inner-wing representation cap**, not the cost of the nonzero separator itself.

No cap is raised and no width is removed.

## Replacement inner representation

The parity-chain controls are affine Boolean systems. v3.1 replaces only the inner wing representation with a proof-carrying `AFFINE_GF2` system.

An equation is stored canonically as

`XOR_{i in S} x_i = r`, with `r in {0,1}`.

For existential projection of a private variable `x`:

1. deterministically select one equation containing `x` as pivot;
2. XOR that pivot into every other equation containing `x`;
3. remove the pivot equation;
4. canonicalize/deduplicate the remaining system;
5. store pivot, before/after hashes and XOR count as the projection proof.

This is exact because the removed pivot can always be solved uniquely for `x` after values of all remaining variables are fixed.

Reversing the stored pivot sequence reconstructs the actual eliminated private witness; no family witness is injected.

## Frozen replay contract

The following remain exactly unchanged from v3:

- widths: `[2,4,6,8,10,12,14]`;
- SAT/UNSAT parity-chain pairs;
- explicit canonical boundary table language;
- `J_B(Lambda,Rho)=Lambda INTERSECT Rho`;
- every v0.1 global cap;
- left-to-right shared-boundary projection order;
- strict final witness verification against the original unprojected wing systems.

No new tuned cap is introduced.

## Expected diagnostic value

The affine wing has `O(k)` equations and exact private elimination with polynomial work on this frozen family. Therefore, if v3.1 now hits a cap during `ADHESION_BUILD` or `BOUNDARY_PROJECTION`, the experiment has finally isolated the explicit separator representation rather than the inner parity wing.

For this family each wing relation contains exactly `2^(k-1)` boundary rows. A cap hit in the explicit table is only a finite representation limit; it is not a lower bound against compressed affine/BDD/orbit boundary languages.

## Claim ledger

`ADH_001_OBDD_WING_BOTTLENECK = PRESERVED`

`AFFINE_GF2_PRIVATE_PROJECT_EXACT = TO_BE_PROVIDER_VERIFIED`

`AFFINE_GF2_PRIVATE_WITNESS_LIFT_EXACT = TO_BE_PROVIDER_VERIFIED`

`WIDTHS_CHANGED = FALSE`

`CAPS_CHANGED = FALSE`

`BOUNDARY_LANGUAGE_CHANGED = FALSE`

`UNIVERSAL_O_LOG_N_ADHESION_BOUND = OPEN`

`CHEAP_COMPACT_BOUNDARY_DISCOVERY = OPEN`

`P_VS_NP = OPEN`
