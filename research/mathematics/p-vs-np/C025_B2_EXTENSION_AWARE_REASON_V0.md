# C025-B2 — Extension-Aware Portable Reason v0

**Status:** `PROVED_IN_SCOPE` for certificate soundness, context-independent original-variable reuse, and frozen verifier admission rules. Provider replay PASS after post-PASS definition-closure repair.

**Claim ceiling:** this does **not** establish universal polynomial proof size, polynomial active representation, deterministic polynomial proof search, `P=NP`, or `P!=NP`.

## 1. Frozen language

Let `F0` be the canonical root CNF. An extension definition is

```text
EXTEND(e, a, b)
e <-> (a AND b)
```

with exact definitional CNF

```text
(~e OR a)
(~e OR b)
(e OR ~a OR ~b)
```

The frozen v0 rules are:

1. `e` is fresh and strictly larger than every root variable and every earlier extension variable;
2. `a,b` are literals over root variables or earlier extension variables only;
3. definitions are therefore topologically ordered and cyclic/forward dependencies are rejected;
4. proof nodes are only `ROOT_AXIOM`, `EXTENSION_AXIOM`, or exact `RESOLVE`;
5. the advertised reusable clause contains root/original variables only;
6. every serialized proof node must be reachable from the advertised final node;
7. every declared extension definition must lie in the transitive definition closure required by reachable extension axioms;
8. portable export prunes unused proof nodes and unused extension definitions.

## 2. Portable reason object

```text
R_ext = (
  root_fingerprint,
  extension_definitions,
  advertised_clause C,
  final_node,
  reachable_proof_DAG
)
```

The verifier recomputes the root fingerprint, every definitional clause and every Resolution step. Local proof-store numbering is not trusted.

## 3. Conservative-extension lemma

For any assignment `alpha` to root variables, process definitions in order and set

```text
e := value_alpha(a) AND value_alpha(b).
```

Because each operand is a root or earlier extension literal, the value is well-defined. The resulting extended assignment satisfies all three exact CNF clauses for each definition.

Therefore every model of `F0` has an extension satisfying all admitted extension definitions. □

## 4. Soundness theorem

If `VERIFY(F0,R_ext)=PASS` and the advertised clause `C` contains root variables only, then

```text
F0 |= C.
```

**Proof.** Take any model of `F0`. Extend it sequentially by the conservative-extension lemma. Root axioms and verified extension axioms are true in the resulting assignment. Resolution preserves consequence, so the accepted final clause `C` is true. Since `C` contains root variables only, its truth depends only on the original assignment. Thus every model of `F0` satisfies `C`. □

Hence for any partial root assignment `rho`,

```text
VERIFY(F0,R_ext)=PASS
AND rho falsifies C
=> UNSAT(F0 | rho).
```

This is the context-independent reuse theorem for B2.

## 5. Extension-participating fixture

Root CNF:

```text
(a OR c)
(b OR c)
(~a OR ~b OR d)
```

Define `e <-> (a AND b)`. Verified Resolution derives

```text
(e OR c)
(~e OR d)
(c OR d)
```

The extension participates internally while the reusable result `(c OR d)` contains root variables only. Context `{c=0,d=0}` therefore makes the root CNF UNSAT.

This fixture validates mechanics only; the theorem above supplies the semantic scope.

## 6. Adversarial admission replay

The strengthened provider suite rejects:

- root-variable collision;
- duplicate/nonfresh extension id;
- descending extension ids;
- forward dependency;
- explicit cyclic dependency attempt;
- extension-variable leak in the advertised clause;
- tampered extension-axiom clause;
- invalid extension-axiom slot;
- tampered Resolution node;
- advertised-clause/final-node mismatch;
- wrong root binding;
- unreachable proof-node garbage;
- syntactically valid but unused extension-definition garbage.

The exporter also proves by replay that unused definitions are pruned from portable output.

## 7. Provider receipt

Canonical receipt:

`data/TOPA-C025-B2-EXTENSION-AWARE-REASON-PROVIDER-PASS-2026-08-24-v1.0.json`

Provider:

```text
repo        = Hawkar-usls/Janus-Fundamentum
branch      = c025-policy0b-fair-reason
PR          = #214
head        = 736f4b7e532ee285bcb6f05b48e47c483a2c0613
workflow    = Validate C025 Fair Scheduler and Reasons
run         = 32720170819
job         = 97409694435
conclusion  = SUCCESS
```

The second run is authoritative because it occurred **after** TOPA found the unused-definition payload loophole and the verifier was strengthened.

## 8. Exact mathematical boundary

```text
C025_B2_EXTENSION_RULE_SEMANTICS             = FROZEN_V0
C025_B2_CONSERVATIVE_EXTENSION_SOUNDNESS     = PROVED
C025_B2_ORIGINAL_CLAUSE_REUSE                = PROVED
C025_B2_STANDALONE_VERIFIER                  = PROVIDER_PASS
C025_B2_ADVERSARIAL_ADMISSION_SUITE          = PROVIDER_PASS
C025_B2_DEFINITION_CLOSURE                   = PROVIDER_PASS
C025_B2_STATUS                               = PROVED_IN_SCOPE

C025_E1_PLAIN_RESOLUTION_CERT_SIZE           = REFUTED
C025_E2_UNIVERSAL_EXTENSION_AWARE_PROOF_SIZE = OPEN
C025_C2_EXTENSION_DEFINITION_DISCOVERY       = OPEN
C025_C2_GLOBAL_DETERMINISTIC_PROOF_SEARCH    = OPEN
ISSUE_212_ACTIVE_REPRESENTATION              = OPEN
P_VS_NP                                      = OPEN
```

## 9. Non-equivalences that remain hard laws

```text
SOUND CERTIFICATE != SHORT CERTIFICATE
SHORT CERTIFICATE != SMALL CACHE
SMALL CACHE != EASY PROOF DISCOVERY
SHORT PROOF EXISTS != DETERMINISTIC POLICY FINDS IT IN POLYTIME
POLY VERIFY IN CERTIFICATE SIZE != POLY CERTIFICATE SIZE IN INPUT N
PROOF DISCOVERY != TOTAL SAT RUNTIME
```

B2 closes the **soundness/interface** layer for this frozen language. The next mathematical front is no longer verifier correctness; it is proof size and deterministic discovery.
