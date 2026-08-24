# C025-E1 — Resolution-Certificate Size Barrier

**Status:** universal polynomial portable-certificate-size target is refuted for the current clause-only C025-B Resolution-DAG language.

**Claim ceiling:** this does not prove `P != NP`, does not refute proof-carrying SAT solving in stronger proof systems, and does not refute C025-B's soundness theorem. It refutes one representation target for one certificate language.

## 1. Current C025-B language

A portable reason is

```text
R = (root_fingerprint, advertised_clause C, final_node, Resolution-DAG pi)
```

whose leaves are clauses of root CNF `F0`, internal nodes are exact Resolution steps, and `pi` derives `C`.

`R` applies to context `rho` only if `rho` falsifies every literal of `C`.

## 2. Root reason is a Resolution refutation

### Lemma E1

If a C025-B reason applies to the empty root context, then its advertised clause is the empty clause.

**Proof.** The empty assignment assigns no propositional variable. Therefore it cannot falsify every literal of any nonempty clause. The empty clause is vacuously falsified. □

### Corollary E2

A standalone C025-B UNSAT reason returned at the root is exactly a Resolution refutation of `F0`: a Resolution DAG deriving the empty clause from root clauses. □

## 3. External unconditional lower bound

Classical Resolution proof complexity supplies explicit polynomial-size CNF families requiring exponential-size Resolution refutations.

A canonical example is the pigeonhole principle. Haken's 1985 result proves superpolynomial/exponential lower bounds for Resolution proofs of pigeonhole formulas. A modern explicit formulation gives, for a standard pigeonhole CNF family, Resolution size at least

```text
2^(n/20)
```

for parameter `n`.

References:

- Armin Haken, **The intractability of resolution**, Theoretical Computer Science 39 (1985), 297–308, DOI 10.1016/0304-3975(85)90144-6.
- Modern proof-complexity course notes, theorem “an exponential lower bound for the pigeonhole principle,” giving a `2^(n/20)` lower bound for the stated standard PHP encoding.

The standard pigeonhole CNF has polynomially many variables/literals/clauses in `n`; under a deterministic signed-integer literal-list encoding its bit length `N_n` is `poly(n)`.

## 4. The barrier theorem

### Theorem E3 — no universal polynomial-size root certificate in C025-B-v1

There is no fixed constant `a` such that every unsatisfiable CNF `F` of encoded length `N` has a root-applicable C025-B-v1 certificate of encoded size at most `N^a`.

**Proof.** Apply the language to the pigeonhole family. By Corollary E2, any root-applicable C025-B certificate is a Resolution refutation. The Resolution lower bound is exponential in family parameter `n`, while input bit length is polynomial in `n`. Therefore certificate size is superpolynomial in input bit length. □

## 5. Algorithmic consequence for the current Policy-0B proof-carrying design

If the frozen solver requires every UNSAT recursive return — including the root — to materialize a standalone C025-B-v1 certificate, then on the hard Resolution family it must construct/output a superpolynomial object.

Hence the following target is false:

```text
FOR_ALL_UNSAT_F:
  ROOT_PORTABLE_RESOLUTION_REASON_SIZE <= poly(|F|)
```

This remains true even with:

- a perfect reason-cache index;
- perfect deterministic discovery of the shortest available Resolution proof;
- zero hashing overhead;
- perfect DAG sharing inside the producer.

DAG sharing is already part of the Resolution proof-size measure; the lower bound is on DAG refutations, not merely tree copying.

## 6. What survives

C025-B remains useful as a **local soundness language**:

```text
CERTIFIED_GLOBAL_CLAUSE + CONTEXT_FALSIFICATION => SAFE_REUSE
```

It can still certify individual learned clauses and local transformations.

What dies is the stronger universal hope that this exact Resolution-only language always admits polynomial-size standalone root reasons.

## 7. Design constraint for the next reason language

A universal proof-carrying P-vs-NP route must do at least one of:

1. use a proof system strictly stronger than plain Resolution for returned certificates;
2. introduce extension/abbreviation mechanisms with independently verified semantics;
3. use a heterogeneous certificate language whose non-Resolution rules each have standalone polynomial-time verifiers;
4. prove that the solver need not materialize a full root certificate and separately prove correctness/runtime without smuggling an equivalent exponential trace into storage or replay.

Moving to a stronger proof system **does not** establish polynomial proof size or polynomial proof search. It only removes this already-known Resolution lower-bound obstruction.

## 8. Updated frontier

```text
C025_B_REASON_SOUNDNESS                         = PROVED_IN_SCOPE
C025_B_PORTABILITY                              = PROVED_IN_SCOPE / CI PASS
C025_C1_CACHE_QUERY_IN_EXPLICIT_M               = PROVED / CI PASS
C025_E1_UNIVERSAL_POLY_RESOLUTION_CERT_SIZE     = REFUTED

C025_B2_STRONGER_REASON_LANGUAGE                = REQUIRED
C025_C2_DETERMINISTIC_GLOBAL_PROOF_SEARCH       = OPEN
C025_E2_STRONGER_LANGUAGE_PROOF_SIZE            = OPEN
C025_E3_ACTIVE_STATE_CACHE_SIZE                 = OPEN
P_VS_NP                                         = OPEN
```
