# PF5 Dark Residual Structure Miner v27

v27 is a **post-hoc observer only** over the nine v26 residuals that remain OPEN after v24 closure and the fresh proof-carrying 2-SAT SCC lane.

It looks for structure that is much harder to track reliably by eye across many signed clauses:

1. **Strong 2-SAT backdoors of fixed size <=2.** A set B is accepted only if deleting B's literals from every clause leaves width <=2. Then every assignment to B reduces the residual to 2-CNF. Search is deterministic and capped at k=2 before results are viewed.
2. **Renamable Horn / renamable dual-Horn.** The observer builds a 2-SAT constraint system over variable-flip bits and uses the already proof-carrying v26 SCC engine only for class recognition. A found flip assignment is verified syntactically on the renamed CNF.
3. **Wide-clause pressure maps.** JANUS records how strongly each variable intersects width>2 clauses, plus the exact wide-clause variable sets.

No formula is rewritten and no SAT decision about the nine source residuals is made. Any selected lane must be validated on a new frozen holdout before admission.

Candidate actions are ranked by dark-residual coverage:

- `STRONG_2SAT_BACKDOOR_K_LE_1`
- `STRONG_2SAT_BACKDOOR_K_LE_2`
- `RENAMABLE_HORN`
- `RENAMABLE_DUAL_HORN`

`P_VS_NP = OPEN` remains mandatory.
