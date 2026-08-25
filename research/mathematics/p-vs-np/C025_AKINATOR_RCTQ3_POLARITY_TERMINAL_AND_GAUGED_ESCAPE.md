# JANUS RCTQ-3 — typed polarity terminal + signed-gauge escape

Status before provider: **FROZEN PROTOCOL / NO RESULT YET**  
Primary goal: `RESOLVE_P_VS_NP`  
Claim ceiling: `P_VS_NP_OPEN`  
Global rule: `NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT`.

## 1. Promote the reverse-discovered exact terminal rule

For an explicit CNF `F`:

- if every clause contains at least one positive literal, the all-ones assignment satisfies `F`;
- if every clause contains at least one negative literal, the all-zero assignment satisfies `F`.

The certificate is one indicated literal of the required polarity per clause. Recognition and replay are linear in total literal occurrences; witness construction is linear in the number of variables.

Typed Keymaster operator:

`UNIFORM_POLARITY_CLAUSE_WITNESS : CNF -> TERMINAL`.

This must extend the immutable 14-operator catalog to 15 without mutating old receipts.

## 2. Stronger deterministic escape family

Start from the frozen RCTQ-2 family

`E_n = AND_i [(x_i OR x_(i+1) OR NOT x_(i+2)) AND (NOT x_i OR x_(i+3) OR x_(i+5))]`

with indices modulo `n`.

Apply the fixed signed-variable gauge

`g_j = [0,0,1,1,0][(j-1) mod 5]`.

Every occurrence of variable `x_j` is complemented iff `g_j=1`. Call the result `G_n`.

This is a literal-bijection, hence exact SAT equivalence. Two explicit witnesses are inherited from the all-ones/all-zero witnesses of `E_n`:

- `w^1_j = NOT g_j`,
- `w^0_j = g_j`.

Frozen ladder: `n in {37,41,43,47}`. Primary state: `G_37`.

## 3. Required escape checks

For `G_37`, independently verify all domains in the 15-operator exact catalog. In particular it must have:

- no pure literal;
- no pivot with zero distinct non-tautological resolvents;
- no pivot with exactly one distinct non-tautological resolvent;
- no complementary twin;
- no strict clause subsumption;
- no self-subsuming-resolution pair;
- one incidence component;
- width 3, hence no `TWO_SAT` source admission;
- no source-language admission to affine/ACI/symmetric/orbit-closed operators;
- swap-orbit construction must either refuse on the frozen polynomial cap or else the escape fails;
- at least one all-positive clause and at least one all-negative clause, so `UNIFORM_POLARITY_CLAUSE_WITNESS` refuses both all-ones and all-zero terminal rules.

The two inherited mixed witnesses must replay exactly.

## 4. Interpretation

If `G_37` escapes all 15 domains, only this is established:

`FROZEN_15_CATALOG_UNIVERSAL_NEXT_TRANSITION_AVAILABILITY = FALSE`.

This is **not** SAT hardness, **not** `P!=NP`, and not a lower bound against arbitrary exact transition algebras.

Because `G_n` is produced by a signed literal bijection, reverse JANUS must explicitly inspect whether the escape exposes a missing exact representation-normalization law. In particular, any discovered gauge normalization must be classified as a bijective representation change, not state-count compression, unless an independent quotient theorem proves otherwise.

## 5. Reverse obligation

After terminal RCTQ-3 CI, execute:

`RCTQ3 -> RCTQ2 -> RCTQ1 -> KANAMI -> UNIFIED -> KANAMI -> RCTQ1 -> RCTQ2 -> RCTQ3`

and require hash-stable replay for all immutable prior results.

`P_VS_NP = OPEN` unless a separate universal theorem closes every global obligation.
