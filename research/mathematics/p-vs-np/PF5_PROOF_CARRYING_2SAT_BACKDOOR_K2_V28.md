# PF5 Proof-Carrying Strong 2-SAT Backdoor k<=2 — v28 frozen protocol

v27 found a machine-level structural signal on viewed dark residuals: 6/9 had a strong backdoor into 2-SAT of size at most two, and 3/9 already had one of size at most one. This is a discovery result only. v28 therefore uses a completely fresh holdout, frozen before provider code.

Fresh groups:

- `n=6, m=24, seeds 918600..918615`
- `n=7, m=28, seeds 918700..918715`

The provider will first run the already admitted v24 exact closure and v26 direct 2-SAT lane. For any residual still OPEN, it deterministically tests candidate backdoor sets in increasing size `k=0,1,2`, then lexicographically by variable id. Every failed candidate is charged.

A candidate `B` is a **strong 2-SAT backdoor** exactly when deleting literals whose variables belong to `B` leaves every clause with at most two remaining literals. This is a syntactic sufficient-and-necessary test for the promised strong reduction used here: after any total assignment to `B`, simplification cannot leave a clause wider than two.

If a backdoor is found, all `2^|B|` assignments are explored in a frozen order. Each branch is explicitly simplified and verified to be 2-CNF, then solved by the proof-carrying v26 SCC lane.

For SAT, one branch must provide its backdoor assignment, simplification receipt, SCC witness, merged residual witness, and a successful replay through the inherited v24 witness-lift transcript to the original source. For UNSAT, every branch must be present and carry a verified SCC contradiction certificate; the branch manifest certifies exhaustive coverage of all assignments to `B`.

No SAT oracle or truth-table enumeration is allowed in provider execution. Finite exhaustive truth tables may be used only after provider outputs are frozen and hashed, solely as a semantic audit. Discovery, branch generation, state, proof, verification, witness, lift, and cumulative costs are all charged.

Even a perfect finite v28 result admits only this restricted structural lane. `UNIVERSAL_EXACT_CLOSURE = OPEN` and `P_VS_NP = OPEN` remain unchanged.
