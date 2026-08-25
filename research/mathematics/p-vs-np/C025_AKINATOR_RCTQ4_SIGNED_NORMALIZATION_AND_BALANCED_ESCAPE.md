# JANUS RCTQ-4 — typed signed normalization + balanced-polarity escape

Status before provider: **FROZEN PROTOCOL / NO RESULT YET**  
Primary goal: `RESOLVE_P_VS_NP`  
Claim ceiling: `P_VS_NP_OPEN`  
Global rule: `NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT`.

## 1. Promote the reverse-discovered exact normalization

For explicit CNF `F`, let `p(v)` and `m(v)` be positive and negative occurrence counts of variable `v`.

Deterministically complement every variable with `m(v) > p(v)` and leave all others unchanged.

Typed operator:

`SIGNED_POLARITY_COUNT_NORMALIZE : CNF -> CNF`.

The emitted flip vector defines a bijection on assignments.  Applying the same flip vector again returns the original formula.  Therefore SAT is preserved exactly and a witness is lifted by XOR with the flip vector.

Certificate: source hash + target hash + exact flip vector.  Construction/replay: polynomial in explicit CNF size.  This is representation normalization, **not state-count compression** and not universal progress.

This must extend the immutable RCTQ-3 15-operator catalog to 16 without mutating historical receipts.

## 2. Deterministic balanced family

Start from the frozen RCTQ-3 gauged family `G_n`, with gauge pattern `[0,0,1,1,0]`.

For every clause `C` in `G_n`, include both `C` and its literalwise complement `bar(C)`.

Then add the exact paired clauses

`P = (x_1 OR x_2 OR x_3)`

`N = (NOT x_1 OR NOT x_2 OR NOT x_3)`.

Call the resulting CNF `B_n`.

Frozen ladder: `n in {37,41,43,47}`. Primary state: `B_37`.

### Exact balance theorem

Each pair `C, bar(C)` contributes exactly one positive and one negative occurrence for every occurrence of each variable.  The pair `P,N` does the same for `x_1,x_2,x_3`.

Hence for every variable:

`p(v) = m(v)`.

Therefore `SIGNED_POLARITY_COUNT_NORMALIZE` has no variable in its strict domain `m(v)>p(v)` and must REFUSE.

### Explicit SAT witnesses

The two RCTQ-3 inherited mixed witnesses are retained:

- `w^1_j = NOT g_j`,
- `w^0_j = g_j`.

Every `E_n` clause has both a true and a false literal under all-ones and under all-zero. Signed gauge preserves literal truth values under the corresponding transformed witness. Therefore every `G_n` clause and its complement are both satisfied by `w^1` and `w^0`.

For variables 1,2,3 the gauge is `(0,0,1)`, so `w^1=(1,1,0)` and `w^0=(0,0,1)` on these coordinates. Thus both witnesses satisfy `P` and `N`.

## 3. Frozen exact escape checks

For `B_37`, independently evaluate all 16 operator domains. Required for an escape:

- no pure literal;
- no pivot with zero distinct non-tautological resolvents;
- no pivot with exactly one distinct non-tautological resolvent;
- no complementary twin;
- no strict subsumption;
- no SSR pair;
- one incidence component;
- clause width 3, so no 2-SAT source admission;
- no source-language admission to affine/ACI/symmetric/orbit-closed operators;
- swap-orbit quotient refuses on its frozen `N^4` cap;
- `UNIFORM_POLARITY_CLAUSE_WITNESS` refuses because `N` has no positive literal and `P` has no negative literal;
- `SIGNED_POLARITY_COUNT_NORMALIZE` refuses because `p(v)=m(v)` for every variable.

Both explicit mixed witnesses must replay.

If any older exact operator applies, the construction is **not** an escape and the failure must be preserved without changing this protocol.

## 4. Interpretation

If `B_37` escapes all 16 frozen domains, only:

`FROZEN_16_CATALOG_UNIVERSAL_NEXT_TRANSITION_AVAILABILITY = FALSE`.

This is not SAT hardness, not `P!=NP`, and not a lower bound against arbitrary exact transition algebras.

If the construction fails because an older exact operator applies, that is also useful: it identifies which exact algebra closes the balanced family.

## 5. Reverse obligation

After terminal RCTQ-4, replay immutable results in reverse then forward order and inspect only exact algebraic invariants. No score/ranking/heuristic candidate selection.

`P_VS_NP = OPEN` unless a separate universal theorem closes all global obligations.
