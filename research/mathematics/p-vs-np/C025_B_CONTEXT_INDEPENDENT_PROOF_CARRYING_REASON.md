# C025-B — Context-Independent Proof-Carrying Reason

**Status:** portable reason semantics and soundness theorem closed on paper; provider replay PASS; TOPA portable-v1 replay active.

**Claim ceiling:** this closes the **soundness and portability interface** for returned UNSAT reasons. It does **not** prove polynomial-time SAT, polynomial proof search, polynomial cache discovery, polynomial total certificate size, `P=NP`, or `P!=NP`.

## 1. Why a Boolean cache is insufficient

An exact cache entry

```text
residual K -> UNSAT
```

is sound only for the exact residual key. C025 needs a reusable object that remains valid under a different decision context without residual similarity, hash coincidence, or an unproved subsumption rule.

The C025 reason language is deliberately stricter than the formula-level `FCW_reason` object in Beame–Impagliazzo–Pitassi–Segerlind. The literature result is motivation only until a formal simulation is proved.

## 2. Frozen portable reason object

Let `F0` be the canonical root CNF. A returned Policy-0B reason is a **self-contained immutable certificate**

```text
R = (
  root_fingerprint,
  advertised_clause C,
  final_node,
  reachable_resolution_DAG pi
)
```

with:

1. `C` canonical and non-tautological;
2. every `AXIOM` leaf indexed into `F0` and checked byte-for-byte against that root clause;
3. every internal node an exact Resolution step;
4. `final_node` equal to `C`;
5. every serialized proof node reachable from `final_node` — unrelated proof garbage is rejected;
6. no decision assumption may appear as a proof axiom;
7. `root_fingerprint` binds provenance, while leaf verification against the supplied `F0` supplies the logical binding.

A verifier needs only `(F0,R)`. It shares **no producer `ProofStore`, node numbering, or mutable cache**.

This repairs the store-aliasing gap found after the first green C025-B replay: a reason reference of the form `(root_hash, local_node_number)` was sound inside one ledger but was not genuinely portable.

## 3. Applicability

For partial assignment `rho`:

```text
APPLIES(R,rho)
```

iff `rho` assigns every variable in `C` and makes every literal of `C` false.

The context need not equal, extend, or resemble the context where the reason was discovered.

## 4. Certificate and reuse theorems

### Theorem B1 — certificate soundness

If `VERIFY(F0,R)=PASS`, then

```text
F0 |= C.
```

**Proof.** Each accepted leaf is an actual clause of `F0`; exact Resolution preserves logical consequence. Induction over the topological proof order gives the advertised final clause. □

### Theorem B2 — context-independent reuse

If `VERIFY(F0,R)=PASS` and `APPLIES(R,rho)`, then

```text
UNSAT(F0 | rho).
```

**Proof.** Every model of `F0` satisfies `C`, while every total assignment extending `rho` falsifies `C`. □

This theorem is independent of how `R` was found.

## 5. Branch composition

Let `x` be unassigned in parent context `rho`. Let `R0,R1` be certified clauses applicable to `rho+x=0` and `rho+x=1`.

- if `rho` already falsifies one child clause, reuse that certificate unchanged;
- otherwise the false-child clause must contain `x` and cannot contain `~x`;
- the true-child clause must contain `~x` and cannot contain `x`;
- resolving them on `x` gives a globally implied clause falsified by `rho`.

### Theorem B3 — logical branch-composition overhead

In a **shared proof DAG**, composition requires at most one new Resolution node. □

### Representation correction exposed by TOPA

A **portable materialized certificate** cannot count the child DAGs as free. A simple self-contained export has size

```text
|R_parent| <= |R0| + |R1| + O(size(new_resolution_node)).
```

With content-addressed/global DAG sharing the physical duplication may be reduced, but that is a representation theorem to be proved, not assumed.

Therefore the earlier phrase “branch composition costs one node” is valid only for logical extension of an already-shared DAG, **not** for standalone serialized byte size. This cost is routed to C025-E/#212.

## 6. Unit-propagation conflict lifting

Each propagated literal `l` carries a globally certified antecedent

```text
(l OR A)
```

that was unit under the propagation prefix. Starting from a globally certified conflict clause, traverse propagations in reverse order and resolve away `~l` with the antecedent of `l` whenever it occurs.

### Theorem B4 — decision-only lifted reason

The final clause is derivable from `F0` and is falsified by the decision assignment alone. At most one new logical Resolution node is added per eliminated propagated variable in a shared producer DAG. □

Again, portable export must include the reachable antecedent/conflict proof sub-DAG and is charged by its actual encoded size.

## 7. Standalone verifier

Portable nodes have exactly two forms:

```text
AXIOM(source_clause_index)
RESOLVE(left_node, right_node, pivot)
```

The verifier:

1. canonicalizes the supplied root CNF;
2. checks root provenance binding;
3. checks every axiom against the indexed root clause;
4. recomputes every exact canonical resolvent;
5. rejects tautological derived reason clauses in v1;
6. checks final node = advertised clause;
7. checks all serialized nodes are reachable from the final node.

### Theorem B5 — verification cost

For encoded certificate size `M`, deterministic verification is polynomial in `M` (with sorted canonical clauses, each Resolution merge is polynomial in its parent encodings).

This is **not** a theorem that `M = poly(N)` for original input size `N`.

## 8. Replays and negative tests

The provider implementation in `Janus-Fundamentum` has already passed the first C025-B replay for:

```text
DIRECT_REASON
CROSS_CONTEXT_REUSE
BRANCH_COMPOSITION
UNIT_CONFLICT_LIFT
MALFORMED_CERTIFICATE_REJECTION
ROOT_FINGERPRINT_REJECTION
```

TOPA then reattacked the interface and found the store-local reference gap. Portable v1 adds explicit tests for:

```text
STANDALONE_PORTABLE_CERTIFICATE
STORE_ALIAS_INDEPENDENCE
ADVERTISED_CLAUSE_TAMPER_REJECTION
PROOF_TAMPER_REJECTION
UNREACHABLE_GARBAGE_REJECTION
```

No prior PASS is erased; it is preserved as an earlier, narrower in-store result.

## 9. Cost firewall and the now-smaller frontier

Keep these five quantities separate:

```text
REASON_VALIDITY                 = solved in C025-B scope
REASON_PORTABILITY              = solved in C025-B semantics; replay required
REASON_LOCAL_CONSTRUCTION       = bounded in supplied trace/shared-DAG size
REASON_DISCOVERY_IN_CACHE       = OPEN C025-C
TOTAL_REASON_DAG_SIZE           = OPEN C025-E / #212
GLOBAL_DETERMINISTIC_PROOF_SEARCH = OPEN C025-C/D
```

Hard laws:

```text
CHEAP_REASON_CHECK != CHEAP_REASON_DISCOVERY
SHORT_REASON_EXISTS != POLICY_FINDS_IT_IN_POLYTIME
POLY_LOCAL_WORK_IN_TRACE_SIZE != POLY_WORK_IN_ORIGINAL_INPUT_N
DAG_SHARING != POLY_TOTAL_DAG_SIZE_WITHOUT_A_BOUND
```

## 10. Literature boundary

Beame, Impagliazzo, Pitassi, and Segerlind, *Formula Caching in DPLL*, ACM TOCT 1(3), 2010, define formula-level `FCW_reason` and prove that system p-simulates regular Resolution.

C025 clause reasons are intentionally stricter. No regular-Resolution simulation or polynomial-search consequence is imported without a separate proof.

## 11. Exact frontier

```text
C025_B_REASON_SEMANTICS                 = FROZEN_PORTABLE_V1
C025_B_CERTIFICATE_SOUNDNESS            = PROVED
C025_B_CONTEXT_INDEPENDENT_REUSE        = PROVED
C025_B_BRANCH_COMPOSITION_LOGIC         = PROVED
C025_B_UNIT_CONFLICT_LIFT_LOGIC         = PROVED
C025_B_VERIFY_COST_IN_CERTIFICATE_SIZE  = PROVED
C025_B_FIRST_PROVIDER_REPLAY            = PASS
C025_B_PORTABLE_V1_REPLAY               = PENDING

C025_C_REASON_DISCOVERY                 = OPEN
C025_C_DETERMINISTIC_PROOF_SEARCH       = OPEN
C025_E_TOTAL_REASON_AND_STATE_SIZE      = OPEN
P_VS_NP                                 = OPEN
```
