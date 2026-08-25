# C025 — Akinator U1-L2C: proof-carrying ACI shared-factor quotient

Status: **FROZEN_PROTOCOL / PROVIDER_PENDING**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-L2B2 proved that the fixed context-closed `k=4,g<=3` local grammar is not universally complete.  The explicit `SF_4(m)` escape keeps `Omega(G)` projected affected-cone mass under every admitted local saturation even though the whole Boolean obligation has a linear-size exact quotient with `AC_x=1`.

The missing operation is not another bounded local rewrite.  It is a representation-changing quotient which exposes exact shared conjunction factors before the projected cone is copied or resolved.

This gate freezes that operation for the **pure conjunction language only**.

It does **not** claim universal SAT compression and it does not yet close sequential existential projection.

---

## 1. Admitted source language

An admitted source is an explicit finite acyclic single-output DAG whose reachable nodes are only:

1. signed root/boundary literals, treated as exact syntactic factor IDs; or
2. positive binary `AND` gates whose two inputs are earlier admitted signals.

The output cone must be closed: every reachable internal operation is an admitted positive `AND`.

Internal negation, OR, XOR, ITE, unresolved quantifier wrappers, opaque semantic macros, or an unknown operation cause exact

```text
REFUSE_NON_ACI_CONE
```

rather than fallback or semantic guessing.

A signed boundary literal such as `~x` is a leaf token.  This gate does not invoke a semantic complement simplifier; it only applies associativity, commutativity, and idempotence of conjunction.

---

## 2. Exact quotient object

For a source cone `S` define recursively

```text
FACTORS(literal L) = { canonical_signed_id(L) }
FACTORS(A AND B)    = FACTORS(A) union FACTORS(B)
```

where set union performs duplicate removal only for byte-identical canonical signed factor IDs.

The quotient is

```text
Q_ACI(S) = (
    source_fingerprint,
    canonical_sorted_factor_ids,
    source_to_factor_certificate,
    canonical_target_dag,
    accounting
)
```

The canonical target DAG is rebuilt from the sorted unique factor IDs by one fixed deterministic binary-chain convention.

If a projected root `x` is supplied for accounting, factors syntactically independent of `x` are placed before factors marked dependent on `x`; this changes only presentation, not the represented function.

---

## 3. Exactness theorem C.1

For every admitted source cone `S`,

```text
S <=> AND_{f in FACTORS(S)} f.
```

### Proof

Induct on the source DAG.

A leaf literal is equal to the conjunction of its singleton factor set.

For an internal gate `v=A AND B`, by induction `A` and `B` equal conjunctions of their factor sets.  Associativity and commutativity flatten those two conjunctions, and idempotence removes duplicate identical factors.  Hence `v` equals the conjunction over `FACTORS(A) union FACTORS(B)`.

Applying the induction at the output proves the statement.  QED.

The theorem is structural and does not use SAT, model counting, sampled assignments, or general circuit equivalence.

---

## 4. Proof-carrying certificate

The provider must emit enough data for an independent verifier to replay:

- source node IDs and topological operation list;
- source output ID and source SHA-256;
- for every source node, the canonical factor-ID set derived from its children;
- duplicate factor eliminations identified by exact canonical ID equality;
- final sorted unique factor set;
- deterministic target gate list;
- target SHA-256;
- source/target gate counts;
- source/target projected dependency counts when a root `x` is supplied;
- operation and serialized-certificate byte ledger.

The verifier recomputes every factor set from the source DAG.  It does not trust a claimed factor set supplied by the producer.

---

## 5. Polynomial construction bound

Let

- `G` be the number of reachable internal AND gates;
- `L` the number of distinct canonical leaf IDs in the reachable cone;
- `B` the explicit serialized source bytes.

A memoized bottom-up implementation visits every reachable source edge once and maintains deterministic exact factor sets.  With sorted-set or hash-set accumulation plus final sorting, a conservative explicit bound is polynomial in `B`, for example

```text
O(B^2 log B)
```

under a simple copy-on-merge implementation, with certificate/state bytes `O(B^2)` in the deliberately unoptimized replay format.

No asymptotically sharper bound is required for this gate; the requirement is one fixed polynomial in the original explicit state size and no hidden exponential family enumeration.

A later implementation may tighten this to near-linear union/memoization without changing the theorem.

---

## 6. `SF_4(m)` positive-control theorem

For the U1-L2B2 family

```text
a_i = x AND y_i
C_r = z_r AND a_1 AND ... AND a_m
OUT = C_1 AND C_2 AND C_3 AND C_4,
```

exact ACI flattening yields

```text
FACTORS(OUT) = {x, y_1,...,y_m, z_1,z_2,z_3,z_4}.
```

Thus the canonical target has `m+4` AND gates when all `m+5` factors are chained and, with `x` placed last,

```text
AC_x = 1.
```

This closes the specific escape exhibited by B2.

It does not establish that every arbitrary B2/CNF obligation becomes a pure conjunction cone.

---

## 7. Mandatory adversarial controls

The provider must retain exact refusal controls, including at least:

1. a cone with a negated internal gate;
2. a cone with an explicit non-AND operation marker;
3. a mixed cone whose output depends on both an admitted AND region and an opaque non-ACI child.

All must return `REFUSE_NON_ACI_CONE` before any quotient is advertised.

No refusal may be counted as a solved SAT instance.

---

## 8. Frozen verification ladder

Before seeing provider results, freeze:

```text
m in {2,4,8,16,32,64,128}
```

For every positive rung verify:

- exact source gate count;
- exact source factor set;
- duplicate count;
- target factor set;
- exact factor-set equality;
- deterministic target SHA;
- source and target `AC_x`;
- construction-operation count;
- certificate bytes;
- replay of the certificate by a logically separate verifier routine.

The provider may not require that compression ratio exceed any empirical threshold.  A no-compression admitted cone remains a valid exact quotient result.

---

## 9. Claim ledger

Success may establish only:

```text
PURE_AND_ACI_QUOTIENT_EXACTNESS = PROVED_IN_SCOPE
PURE_AND_ACI_QUOTIENT_DETERMINISTIC_POLY_CONSTRUCTION = PROVED_IN_SCOPE
SF4_SHARED_FANOUT_ESCAPE_REPAIRED_BY_ACI_QUOTIENT = PROVED_IN_SCOPE
```

It must not establish:

```text
ARBITRARY_B2_ACI_QUOTIENT = PROVED
UNIVERSAL_CREATE_GRAMMAR = PROVED
SEQUENTIAL_EXISTENTIAL_CLOSURE = PROVED
P_EQUALS_NP = PROVED
P_NOT_EQUALS_NP = PROVED
```

---

## 10. Next exact gate

Immediately after a successful provider, do **not** broaden the ACI identity catalog.

Attack:

```text
U1-L2C1 ACI QUOTIENT EXISTENTIAL UPDATE CLOSURE
```

The required question is whether a remaining root variable can be existentially projected **directly from the quotient representation**, with exact witness lift and polynomial state/work, without reconstructing the original shared-fanout DAG.

For the first subcase, freeze conjunctions of signed root literals, where the update can be characterized exactly.  Then introduce the smallest nontrivial factor objects that themselves depend on the projected variable.

```text
P_VS_NP = OPEN
```
