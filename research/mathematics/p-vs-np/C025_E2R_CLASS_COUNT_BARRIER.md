# C025-E2R — Class-count barrier and the first surviving structural frontier

**Status:** `NAIVE_CLASS_COUNT_INVARIANT_REFUTED`; `SUPPORT_LOCALITY_FRONTIER_OPEN`.

**Claim ceiling:** this note does not prove a lower bound for full Extended Resolution / B2 / ER3. It proves that a broad family of naive semantic-counting invariants cannot yield the superpolynomial extension-count lower bound required by Issue #217, and it freezes a narrower structural attack.

## 1. Target recalled

Issue #217 asks whether every UNSAT CNF `F` of encoded length `N` admits some narrow Extended-Resolution (`ER3`) refutation using at most

```text
K(F) <= N^c
```

extension variables for one fixed constant `c`.

The previous reduction established that, up to polynomial proof translations,

```text
ER/B2 p-boundedness
<=> universal polynomial ER3 extension-count bound.
```

The proposed next idea was to find an invariant of the form

```text
one extension variable can merge / destroy only X independent classes.
```

This note attacks that idea before using it as a lower-bound engine.

## 2. Semantic-signature counting ceiling

Let the root CNF use `n` Boolean variables. Let `Omega={0,1}^n` be the set of root assignments.

After `K` deterministic extension definitions, every root assignment induces one extension signature

```text
sigma(alpha) in {0,1}^K.
```

Therefore the partition of root assignments induced **only by extension-bit signatures** has at most

```text
2^K
```

classes.

Suppose an argument identifies `M` root-assignment classes and claims they must all receive distinct extension signatures. Then necessarily

```text
K >= ceil(log2 M).
```

But `M <= |Omega| = 2^n`, hence

```text
ceil(log2 M) <= n <= N
```

under any ordinary explicit encoding.

### Barrier theorem E2R-C1

A lower-bound method whose entire invariant is only the number of distinguishable root-assignment classes encoded by the `K` extension bits can prove at most a **linear** lower bound `K >= Omega(n)`.

It cannot by itself prove the superpolynomial `K > N^c` required to refute Issue #217 for every fixed `c`.

This is an information-counting ceiling, not a statement about the full power of ER.

## 3. Recursive compression kills flat case-count measures

The stronger naive hope is that each extension can eliminate only polynomially many syntactic cases (clauses, DNF terms, branches, residual labels, etc.). Recursive extension definitions kill this hope as well.

The frozen B2 rule is

```text
e <-> (a AND b)
```

where `a,b` may be literals of root variables or earlier extension variables.

This is a fan-in-2 Boolean circuit gate with free literal negation.

### Parity compression construction

Let `y=x1`. To extend parity by a new root variable `x`, introduce

```text
t1 <-> ( y AND  x)
t2 <-> (~y AND ~x)
y' <-> (~t1 AND ~t2)
```

Then `y' = y XOR x`.

Iterating from `x1` to `xn` computes parity of `n` root variables with exactly

```text
K = 3(n-1)
```

extension variables.

However, any CNF representing `PARITY_n=1` over the root variables alone requires `2^(n-1)` clauses, and any DNF requires `2^(n-1)` terms.

Reason: every non-tautological implicate/implicant must mention all `n` variables. If it omitted a variable, two assignments differing only in that variable would both satisfy/falsify the same term/clause although parity flips. Hence each full-width clause can exclude at most one falsifying assignment, and there are `2^(n-1)` such assignments.

Thus linear extension count can compress an exponentially large flat CNF/DNF case expansion.

### Barrier theorem E2R-C2

Any invariant that charges extension variables only against the number of flattened CNF clauses, DNF terms, explicit branches, or semantically enumerated cases is not stable under recursive B2 extensions.

The parity family is a direct counterexample to an additive `one extension -> bounded flat collapse` principle.

## 4. What an invariant must now do

A surviving invariant must be **structural and proof-sensitive**, not merely semantic-cardinality based.

At minimum it must survive:

1. recursive extension composition;
2. polarity changes / De Morgan representations;
3. DAG sharing;
4. Resolution reuse;
5. restriction of the root formula;
6. polynomially many syntactically different but semantically equivalent extension circuits.

A useful measure `mu` would need a theorem of the form

```text
mu(after one legal extension) <= controlled_change(mu(before))
```

where the controlled change remains small enough across `K=poly(N)` recursive gates to contradict a superpolynomial requirement on an explicit formula family.

Simple partition cardinality and flat representation size do not satisfy this requirement.

## 5. Exact circuit interpretation of extension count

For a fixed list of B2 definitions, the extension-definition graph is a Boolean circuit DAG:

- root literals are circuit inputs;
- each extension variable is one fan-in-2 AND gate;
- negation is allowed on incoming wires;
- the number of non-input gates is exactly `K`.

So a proof of a superpolynomial extension-count lower bound must in some sense show that every useful auxiliary circuit family available to an ER3 refutation needs superpolynomially many gates, **or** exploit a proof-specific invariant stronger than ordinary semantic circuit representation.

This observation explains why unrestricted E2R is close to major circuit/proof-complexity barriers.

## 6. Restricted locality frontier

The first tractable restriction is **transitive root support**.

Define

```text
support(root literal x) = {x}
support(extension literal e_i) = support(a_i) union support(b_i)
```

for `e_i <-> (a_i AND b_i)`.

Call a B2/ER3 proof `kappa-local` when

```text
|support(e_i)| <= kappa
```

for every extension variable.

This is stronger and cleaner than merely requiring each extension gate to have fan-in 2, which is already true globally.

### Why locality is worth testing

Existing proof-complexity work obtains strong lower bounds in systems with **local extension variables** or bounded-support extension polynomials. In particular:

- Sokolov's heavy-width method proves exponential Resolution lower bounds for functional Nisan-Wigderson encodings containing many local extension variables;
- Impagliazzo–Mouli–Pitassi and follow-up work prove lower bounds for Polynomial Calculus with bounded-locality extension variables.

These results are **templates only**. They do not transfer automatically to full B2/ER3, or even to the frozen `kappa`-local ER3 restriction, because the proof rules and extension semantics differ. Any transfer requires object identity or an explicit simulation/reduction theorem.

## 7. New restricted gate E2R-L1

Freeze the following subsidiary target:

> For `kappa = O(log N)` (and then larger regimes), prove or refute that there is an explicit polynomial-size UNSAT CNF family `F_N` for which every `ER3[kappa-local]` refutation either requires superpolynomially many extension variables or does not exist inside the restriction.

This is deliberately a **restriction-only** target.

A positive lower bound here would not settle Issue #217 for unrestricted ER3. Its value is to test whether support locality admits a stable heavy-width / restriction invariant and to identify the precise escape move used by unrestricted recursive extensions.

## 8. Candidate families

Priority order:

1. functional encodings of Nisan-Wigderson generators — because local-extension lower-bound machinery already exists nearby;
2. XORified / lifted pigeonhole families — because locality-vs-extension tradeoffs are known in algebraic systems;
3. guarded-extension constructions — as adversarial syntax templates, not as lower bounds for full ER;
4. Tseitin / parity-based controls — useful for falsifying measures, since extension variables can compress parity efficiently.

## 9. Current status

```text
E2R_GLOBAL_EXTENSION_COUNT                = OPEN
E2R_NAIVE_SEMANTIC_CLASS_COUNT            = REFUTED_AS_SUPERPOLY_METHOD
E2R_FLAT_CNF_DNF_CASE_COUNT               = REFUTED_BY_LINEAR_PARITY_EXTENSION_CIRCUIT
E2R_EXTENSION_DAG_IS_K_GATE_CIRCUIT       = PROVED
E2R_SUPPORT_LOCALITY_DEFINITION            = FROZEN_V0
E2R_KAPPA_LOCAL_LOWER_BOUND                = OPEN_RESTRICTED_FRONTIER
E2R_TRANSFER_FROM_HEAVY_WIDTH_LITERATURE   = NOT_ESTABLISHED
P_VS_NP                                    = OPEN
```

## 10. Hard laws added

```text
MANY_SEMANTIC_CLASSES != SUPERPOLYNOMIAL_EXTENSION_COUNT
EXPONENTIAL_FLAT_REPRESENTATION != EXPONENTIAL_EXTENSION_COUNT
LOCAL_EXTENSION_LOWER_BOUND != FULL_ER_LOWER_BOUND
RECURSIVE_EXTENSION_COMPOSITION_MUST_BE_CHARGED
```
