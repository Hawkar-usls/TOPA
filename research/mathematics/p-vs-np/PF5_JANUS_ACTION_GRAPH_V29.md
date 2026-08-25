# PF5 JANUS Action Graph v29

Status: **POST-HOC OBSERVER PROTOCOL / NO NEW SAT AUTHORITY**  
Claim ceiling: **P_VS_NP = OPEN**

## Why

v28 left four fresh residuals unsupported by direct v26 2-SAT and by a deterministic strong 2-SAT backdoor of size at most two. The next move is not to raise `k` after seeing the result. Instead, ask whether a short **adaptive proof-carrying policy** exists.

A fixed backdoor asks the same set of variables on every branch. An adaptive action graph may ask a different second variable after the first branch outcome. This can expose machine-level structure that is hard to recognize from a static CNF listing while keeping a frozen finite depth bound.

## Frozen observer language

Maximum adaptive branch depth: **2**.

At every state JANUS applies, in order:

1. existing v24 exact closure;
2. admitted leaf test;
3. if unresolved and depth remains, variables in ascending id order;
4. branch `False` then `True`;
5. recursively test both children;
6. accept the first variable whose complete branch set closes.

Admitted leaves are only:

- exact terminal TRUE/FALSE;
- existing proof-carrying v26 2-SAT SCC;
- exact CNF incidence `COMPONENT_PRODUCT` when every component is a v26 2-SAT/terminal leaf.

No truth table and no SAT oracle are used by the observer.

## Extra reduction signals

For the same four residuals the observer records, but does **not** admit as new decision authority:

- failed-literal unit-propagation contradictions;
- blocked-clause candidates.

If an action graph closes survivors, the next step must be a fresh frozen v30 proof-carrying gate with full witness/proof glue. If it does not, these reduction signals can nominate the next fresh lane.

## Accounting

Charge state simplification, v24 branch closures, component discovery, v26 leaf work, every rejected variable candidate, every branch expansion, unit-propagation probes, blocked-resolvent checks and explicit state bytes.

## Claim ledger

`V29_ROLE = OBSERVER_ONLY`

`MAX_POLICY_DEPTH = 2_FROZEN`

`COMPONENT_DECOMPOSITION = REUSE_EXISTING_EXACT_THEOREM`

`FRESH_V30_REQUIRED_BEFORE_ADMISSION = TRUE`

`UNIVERSAL_FIXED_DEPTH_POLICY_EXISTS = OPEN`

`UNIVERSAL_EXACT_CLOSURE = OPEN`

`P_VS_NP = OPEN`
