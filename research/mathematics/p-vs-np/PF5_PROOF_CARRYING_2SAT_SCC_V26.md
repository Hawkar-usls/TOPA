# PF5 Proof-Carrying 2-SAT SCC v26 — frozen protocol

This protocol was frozen **after** v25 nominated `BIJUNCTIVE_2SAT_SCC` from viewed v24 residuals and **before** any v26 provider code exists.

Fresh holdout:

- `n=6, m=24, seeds 917600..917615`
- `n=7, m=28, seeds 917700..917715`

The population is not conditioned on whether v24 leaves a 2-CNF residual.

Pipeline is fixed:

`SOURCE -> v24 exact closure -> terminal? -> if OPEN and max clause width <=2, 2-SAT SCC provider -> otherwise OPEN/UNSUPPORTED`.

For a 2-CNF residual, each clause contributes implication edges with clause provenance. SAT requires an explicit residual witness and a replayed lift to the original source. UNSAT requires a contradiction certificate containing a variable `x` plus two source-supported implication paths `x -> ¬x` and `¬x -> x`.

The provider may not call a SAT oracle or enumerate truth assignments. Exhaustive truth tables are permitted only in the later finite semantic-audit phase, after all provider outputs have been frozen and hashed.

All graph construction, SCC, condensation/topological work, proof bytes, witness bytes, failed eligibility checks, verification and witness-lift costs are charged. A finite PASS admits only this restricted lane on the frozen experiment. `P_VS_NP = OPEN` remains mandatory.
