# PF5 Connected Boundary Adhesion v3.2 — compressed affine `J_B`

Status: **FROZEN REPAIR OF EXPLICIT-TABLE ESCAPE**  
Claim ceiling: **P_VS_NP = OPEN**

## Preserved negative receipt

v3.1 repaired the accidental OBDD-wing bottleneck without changing widths or caps. The provider then reached the intended nonzero-separator front:

- all SAT/UNSAT pairs through `k=12` passed exactly;
- at `k=14`, each wing still had a tiny affine residual;
- the explicit boundary language hit `MAX_PRIMARY_STATE_BYTES` during `ADHESION_BUILD`;
- SAT table bytes: `417818`;
- UNSAT table bytes: `278555`;
- each wing relation contained `8192 = 2^(14-1)` rows.

This is preserved as `ADH-002-EXPLICIT-BOUNDARY-TABLE-ESCAPE`.

It is a representation escape only, not a lower bound.

## v3.2 change

Change **only** the boundary representation.

The inner wing representation remains `AFFINE_GF2` from v3.1. Widths and all v0.1 caps remain unchanged.

Instead of materializing `Lambda`, `Rho`, and `J_B` as row sets, keep each boundary relation as a canonical affine GF(2) system.

For affine systems:

`Lambda(B) = A_L B = c_L`

`Rho(B) = A_R B = c_R`

exact conjunction/JOIN is simply the union of equations followed by deterministic GF(2) row reduction:

`J_B(Lambda,Rho) := RREF_GF2(Lambda UNION Rho)`.

A contradiction row `0=1` is the canonical UNSAT boundary state.

## Exact boundary projection

For `b in B`, existential projection is performed directly on the joined affine state:

1. if no equation contains `b`, choose canonical free value `b=0` for witness reconstruction and leave the relation unchanged;
2. otherwise select a deterministic pivot equation containing `b`;
3. XOR it into every other equation containing `b`;
4. remove the pivot equation;
5. deterministically row-reduce the remainder;
6. record pivot, input/output hashes and row-operation transcript.

Reversing the pivot transcript reconstructs an actual shared-boundary witness. That witness is then fed into the v3.1 private pivot proofs to recover all private roots and is checked against both original unprojected wings.

## Frozen replay contract

Unchanged:

- widths `[2,4,6,8,10,12,14]`;
- SAT and UNSAT control for every width;
- control formulas;
- `AFFINE_GF2` private wing representation;
- global caps;
- left-to-right shared-boundary projection order;
- strict witness provenance.

Changed:

- boundary language only: `EXPLICIT_TABLE -> AFFINE_GF2_RREF`.

No size threshold is tuned after observing ADH-002.

## Interpretation

A successful v3.2 replay establishes a finite closure law for the affine subalgebra:

`AFFINE_WING -> AFFINE_BOUNDARY -> J_B -> EXISTS -> AFFINE_BOUNDARY`.

It does **not** show that arbitrary SAT boundaries are affine, nor that an affine equivalent can be discovered cheaply.

The next genuine adversarial front after a v3.2 PASS is therefore a connected separator whose exact boundary relation is intentionally **non-affine**.

## Claim ledger

`ADH_002_EXPLICIT_TABLE_ESCAPE = PRESERVED`

`AFFINE_JOIN_EXACT = TO_BE_PROVIDER_VERIFIED`

`AFFINE_BOUNDARY_PROJECT_CLOSED = TO_BE_PROVIDER_VERIFIED`

`STRICT_SHARED_BOUNDARY_WITNESS_LIFT = TO_BE_PROVIDER_VERIFIED`

`WIDTHS_CHANGED = FALSE`

`CAPS_CHANGED = FALSE`

`INNER_WING_CHANGED = FALSE`

`ARBITRARY_BOUNDARY_IS_AFFINE = NOT_CLAIMED`

`CHEAP_BOUNDARY_LANGUAGE_DISCOVERY = OPEN`

`UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN`

`P_VS_NP = OPEN`
