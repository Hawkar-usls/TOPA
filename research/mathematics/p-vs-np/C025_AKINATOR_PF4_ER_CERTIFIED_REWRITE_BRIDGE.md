# C025 — Akinator PF4: ER-certified rewrite bridge

Status: **INTERNAL FRONTIER-IDENTIFICATION THEOREM**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Question

PF3 closes several universal exact-container shortcuts. The remaining attractive route is to keep a general Boolean/B2 DAG and use strong **proof-carrying exact rewrites** so that compact equivalent/equisatisfiable structure is discovered before exponential residuals are materialized.

But if rewrite correctness is certified using the frozen B2/Resolution language, this may not be a new proof-complexity system at all.

This note freezes the exact boundary.

---

## 1. ER-certified rewrite lane

A rewrite trace is

`S_0 -> S_1 -> ... -> S_T`

where `S_0` is the encoded CNF and each accepted transformation carries an explicit certificate made only from:

- fresh B2 extensions `e <-> (a AND b)` with the frozen topological/freshness rules;
- Resolution inferences over root and extension clauses;
- explicit local Boolean identities that are compiled to a polynomial number of the same B2/Resolution clauses;
- deterministic bookkeeping/witness-provenance records that have no logical authority by themselves.

For UNSAT, the final logical state contains a certified contradiction/empty clause.

Call this lane `ER-CERTIFIED-REWRITE`.

---

## 2. Theorem R1 — concatenated rewrite certificates are an ER/B2 proof

Assume the total serialized logical certificate volume of the rewrite run is `B`.

Every logical rewrite certificate is, by definition, already a B2/Resolution derivation fragment over the current conservative extension context. Fresh extension definitions can be alpha-renamed globally in trace order so that extension IDs remain topological across the whole run.

Concatenate the reachable derivation fragments, retain the root CNF axioms once, retain every extension definition used by a reachable proof node, and prune certificate/bookkeeping records that have no logical role.

The resulting object is one B2 derivation/refutation whose serialized size is polynomial in `B` under the frozen encoding conventions; in the direct concatenation model it is `O(B)` up to remapping/index metadata.

By the already-proved B2/Extended-Resolution p-equivalence,

`ER-CERTIFIED-REWRITE` is p-simulated by standard Extended Resolution.

Therefore a universal polynomial total-certificate theorem for UNSAT in this lane implies polynomial-size ER refutations.

This is not a new external lower bound. It identifies the lane with the already-open ER proof-size frontier.

---

## 3. Consequence — proof availability collapses back to #216/#217

If for every UNSAT CNF `F` of length `N` the deterministic rewrite language merely **has** some accepting run with

`B(F) <= N^c`

for one universal fixed `c`, then ER is p-bounded up to the frozen polynomial translations.

Equivalently, in the ER3 reduction already established by C025, there would be a universal polynomial extension-count bound.

Thus:

`UNIVERSAL_SHORT_ER_CERTIFIED_REWRITE_EXISTS`

is not an easier theorem than the active ER/ER3 p-boundedness frontier already tracked by issues #216/#217.

It may be a useful constructive presentation of the same frontier, but it is not a bypass.

---

## 4. Discovery is strictly another obligation

Even if a short rewrite trace exists, the Akinator needs to **find** it.

A deterministic procedure that enumerates/chooses rewrite certificates and always halts within `N^d` total work would give an automating algorithm for this ER-certified trace family.

When the trace itself is a complete exact SAT decider with witness return, a polynomial total runtime directly yields

`SAT in P`

and hence

`P=NP`.

But:

`POLY_PROOF_EXISTS != POLY_PROOF_DISCOVERY`.

This is exactly the C025-C2/#215 distinction already frozen in Fundamentum.

---

## 5. Why local rewrite verification is not the hidden miracle

PF1 is a good example: the distributive pivot-factor identity is cheap to verify and cheap to detect in the specific syntactic pivot block.

The hard universal question is not whether one PF1 certificate can be checked. It is whether a deterministic polynomial sequence of such locally certified operations always exists and can be found before state/candidate explosion.

Likewise, an exact orbit generator is useful when a compact generator is structurally available, but universal generator discovery/coverage remains an independent obligation.

Hence:

`LOCAL_PROOF_CARRYING_REWRITE != GLOBAL_AUTOMATABILITY`.

---

## 6. Two non-equivalent ways forward

### PF4-A — stay inside ER-certified rewrites

Then the project should stop pretending the proof-size part is a new lower/easier frontier and attack the known exact obligations directly:

- ER/ER3 proof availability / extension-count bound;
- deterministic proof/rewrite discovery;
- total representation/runtime.

PF1/orbit/live-width become **candidate generators** for the discovery algorithm.

### PF4-B — use a stronger certificate system

If a rewrite needs certificates not p-simulated by B2/ER, the new proof system must be frozen explicitly:

- syntax;
- verifier;
- soundness theorem;
- certificate bytes;
- discovery cost;
- simulation relations to known systems.

Calling the system “quotient”, “wave”, “orbit”, or “semantic rewrite” is not enough to escape proof-complexity accounting.

No stronger system is promoted here.

---

## 7. Akinator interpretation

The current exact Akinator can be understood as a proof-search controller over a portfolio of certified operators:

- PF1 prebirth pivot factorization;
- low-live-width exact relational DP;
- ROBDD/decision-diagram certificates when under cap;
- exact orbit/generator quotients on certified families;
- B2/ER reason and extension derivations;
- family-specific constructive schemas such as Cook/PHP.

The key open theorem is whether this portfolio, or a polynomial extension of it, is **universally complete with polynomial deterministic discovery and polynomial total work**.

If yes, P=NP follows. If no, the failing family/operator boundary is the next negative theorem.

---

## 8. Claim ledger

`ER_CERTIFIED_REWRITE_TRACE_P_SIMULATED_BY_B2_ER = PROVED_BY_CONCATENATION_IN_FROZEN_LANE`

`UNIVERSAL_POLY_ER_CERTIFIED_REWRITE_SIZE_IMPLIES_ER_P_BOUNDED = PROVED_IN_SCOPE`

`ER_CERTIFIED_REWRITE_IS_A_PROOF_SIZE_BYPASS = REFUTED`

`DETERMINISTIC_POLY_REWRITE_DISCOVERY = OPEN`

`ER3_UNIVERSAL_POLY_EXTENSION_COUNT = OPEN`

`ER_P_BOUNDEDNESS = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 9. Laws

- `NEW_REWRITE_SYNTAX != NEW_PROOF_POWER_IF_CERTIFICATES_COMPILE_TO_ER`
- `LOCAL_REWRITE_CHECKING != GLOBAL_REWRITE_DISCOVERY`
- `POLY_TRACE_EXISTENCE != POLY_TRACE_SEARCH`
- `A_QUOTIENT_OPERATOR_MUST_DECLARE_ITS_PROOF_SYSTEM`
- `PF1_ORBIT_LIVE_WIDTH_ARE_DISCOVERY_OPERATORS_NOT_AUTOMATIC_P_VS_NP_THEOREMS`
