# PF5 Slime q=1 Dense 3-CNF Falsification v13

Status: **FROZEN BEFORE PROVIDER RUN**  
Claim ceiling: **P_VS_NP = OPEN**

## Purpose

Attack the strongest finite interpretation left by PF5 v12:

> the current frozen polynomial Slime portfolio might always contain an incidence decomposition whose PS-width is at most linear in the number of incidence leaves.

v13 does not change the Slime producer, candidate count, runtime compiler, cap exponent, selection rule, or proof language. It changes only the fresh source distribution to a much denser connected random 3-CNF ladder.

A single source with

`OPEN_PORTFOLIO_CAP_EXHAUSTED`

is enough to refute **q=1 completeness for this exact frozen portfolio**. It does not refute polynomial PS-width with a larger fixed exponent, other candidate generators, or P=NP.

## Frozen producer and compiler

Slime producer:

`Hawkar-usls/Janus-Demiurge@421794b5c7e3b96f52550cf710fe2d8d2f3b59db`

Runtime compiler:

`PF5-SLIME-CAPPED-PSWIDTH-COMPILER-V12`

Cap remains exactly:

`q = 1`

`K(F) = max(2, #variables + #clauses)`.

No input-dependent exponent and no cap escalation is allowed.

## Frozen dense source ladder

For each `(n,m,seed)` below, generate a connected signed 3-CNF by:

1. inserting the same signed chain backbone on triples `(i,i+1,i+2)` for `i=1..n-2`;
2. adding distinct seeded random signed 3-clauses until exactly `m` clauses are present.

The clause density is approximately `m/n = 4.2`.

Frozen rows:

| n | m | seeds |
|---:|---:|---|
| 10 | 42 | `909010, 909011` |
| 12 | 50 | `909012, 909013` |
| 14 | 59 | `909014, 909015` |
| 16 | 67 | `909016, 909017` |
| 18 | 76 | `909018, 909019` |
| 20 | 84 | `909020, 909021` |

All twelve raw formulas and all twelve Slime manifests must be generated and hashed before the first bounded compiler attempt.

## Runtime protocol

For each source:

1. generate the frozen 16-order Slime v3 manifest;
2. attempt all 16 candidates under the unchanged linear state cap;
3. every candidate returns `CLOSED_PSWIDTH_CAP` or `OPEN_STATE_CAP`;
4. CLOSED candidates are ranked by the unchanged v12 deterministic certificate-cost key;
5. if none closes, emit `OPEN_PORTFOLIO_CAP_EXHAUSTED` and preserve all 16 failure receipts.

No exact scorer is allowed in v13 provider execution.

## Storage discipline

To prevent output volume from becoming the experiment itself:

- every CLOSED candidate is replayed immediately;
- non-selected CLOSED full state payloads may then be discarded after recording certificate digest, peak/total state counts and full work ledger;
- the selected CLOSED certificate, if any, is retained in full;
- OPEN candidates retain their fail-fast refusal receipt;
- the manifest/order hashes are retained for every candidate.

Discarding a non-selected full certificate after successful replay does not alter selection, state construction or work accounting.

## Frozen questions

1. Does any source exhaust all 16 candidates under `q=1`?
2. If yes, what is the first frozen ladder row and what phase/node produces the earliest cap refusal?
3. How does the number of CLOSED candidates change with `n` under fixed density?
4. Does `peak_ps_state / K` approach the cap before total portfolio exhaustion?
5. Is every OPEN candidate bounded at exactly `K+1` distinct states at refusal?

## Interpretation terminals

If an exhausted source exists:

`CURRENT_SLIME_V3_Q1_UNIVERSAL_COMPLETENESS = REFUTED_BY_FINITE_COUNTEREXAMPLE`.

This means only:

- current 16-candidate Slime v3;
- current right-linear incidence decomposition language;
- fixed exponent q=1.

The next allowed question would be whether a **predeclared fixed q>1** or a richer polynomial candidate family survives a new fresh domain. One may not raise q retroactively on the same source and call that the same hypothesis.

If no exhausted source exists:

`NO_Q1_ESCAPE_FOUND_ON_THIS_FROZEN_DENSE_LADDER`.

That is finite evidence only.

## Prohibitions

- no q escalation after seeing results;
- no candidate generation after compiler outcomes;
- no exact PS scorer in runtime/provider selection;
- no SAT oracle or SAT-status filtering;
- no source-seed replacement;
- no dropping OPEN failures from accounting;
- no `OPEN_PORTFOLIO_CAP_EXHAUSTED -> hardness` promotion;
- no `all CLOSED -> P=NP` promotion.

## Surviving theorem gate

Even if q=1 is refuted, the universal target remains:

`EXISTS_FIXED_q_AND_POLY_CANDIDATE_CONSTRUCTION_SUCH_THAT_EVERY_CNF_HAS_A_CANDIDATE_OF_PSWIDTH_AT_MOST_N^q`.

`P_VS_NP = OPEN`
