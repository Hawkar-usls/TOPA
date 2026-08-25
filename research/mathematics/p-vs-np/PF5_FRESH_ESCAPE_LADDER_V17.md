# PF5 Fresh Exact-Closure Escape Ladder v17

## Why this exists

The original finite v11 corpus `907000..907015` is exhausted by the theorem-only v12+v13+v15 closure. That corpus must not be rescanned as if it still contained an unknown obstruction.

v17 therefore freezes a fresh connected-3CNF ladder before provider execution. Its purpose is only to locate the first source that survives the already-admitted exact closure. It does not add a new solver or reduction rule.

## Frozen ladder

For each pair `(n,m)` below, generate 8 sources with the unchanged deterministic `random_connected_3cnf` generator:

- `(6,24)` seeds `911600..911607`
- `(7,28)` seeds `911700..911707`
- `(8,32)` seeds `911800..911807`
- `(9,36)` seeds `911900..911907`
- `(10,40)` seeds `912000..912007`
- `(12,48)` seeds `912200..912207`

The entire 48-source manifest is hashed before any reduction result is inspected. No adaptive extension is permitted.

## Runtime closure

Apply only the already-admitted exact operators to fixed point:

1. `PURE_LITERAL_EXISTENTIAL_PROJECTION`
2. `TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION`
3. `SINGLE_NONTAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION`

The first non-empty residual in the fixed `(n,m,seed)` order is the next obstruction. No score, entropy, crystal size, SAT result, PS-width value, truth table, or Slime trace selects it.

## Hephaestus role

Hephaestus Crystal records canonical source/residual hashes and byte counts and flags exact syntactic recurrence. These measurements have no decision authority.

## Audit

Only after all 48 reductions are frozen, the first surviving source (if any) receives a bounded exhaustive semantic projection audit. This audit is a verifier only and is not part of runtime discovery.

## Claim ceiling

`FRESH_ESCAPE_LADDER = FINITE_ADVERSARIAL_REPLAY`

`HEPHAESTUS_CRYSTAL = ACCOUNTING_RECURRENCE_ONLY`

`UNIVERSAL_EXACT_CLOSURE = OPEN`

`P_VS_NP = OPEN`
