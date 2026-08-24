# C024 / Issue #211 — Second Derivation Review

**Purpose:** re-derive the resolution-sink counterfamily from the registered machine and the primary Formula-Caching theorem without relying on the first proof document's conclusion.

**Result:** `PASS_WITH_ONE_REPAIR_APPLIED` — the missing universal root-affine-dispatch argument is supplied below. After that repair, no remaining logical obstruction was found in the residual-count refutation for the exact current Policy-0A.

**Claim ceiling:** `ISSUE_211_REFUTED_FOR_CURRENT_POLICY0A` does not imply `P != NP` and does not refute the conditional bridge theorem.

## 1. Source theorem scope

Primary published source: Beame, Impagliazzo, Pitassi, Segerlind, *Formula Caching in DPLL*, ACM Transactions on Computation Theory 1(3), 2010.

The required facts are:

1. Definition 4.24 defines `GT_n` from the directed graph-ordering formula on the complete graph and adds totality clauses.
2. The systems are nested in the needed direction: basic exact Formula Caching is a special case of Formula Caching with Weakening and Subsumption (`FCWS`).
3. Theorem 4.28 lower-bounds every `FCWS` refutation of `GT_n` by `2^(n-2)` nodes.
4. The proof explicitly constructs at least `2^(n-2)` distinct residual formulas at novelty level `n-2` and explicitly reasons through unit propagation.

Therefore a valid exact-FC execution projected onto theorem-matched `GT_n` inherits the same lower bound.

## 2. Registered Policy-0A parity

The canonical implementation performs, in order:

```text
visible affine root decision
exhaustive unit propagation
exact cache lookup
one-layer limited Resolution
exhaustive unit propagation
most-frequent-variable branch, min-id tie break, false first
```

The Resolution loop:

- visits pivots in increasing variable id;
- increments the attempt counter before testing whether the resolvent is tautological;
- stops when the next attempted pair would exceed `max(64,4L)`;
- accepts at most `max(8,m//4)` new clauses.

Dedicated GitHub Actions replay `Validate C024 Resolution Sink`, run `32697547130`, completed successfully against the registered imported primitives. For frozen `n=3` it reported:

```text
literal_count                  = 31140
attempt_budget                 = 124560
sink_pair_attempts_available   = 331776
resolution_attempts            = 124560
resolution_additions           = 0
selected branch variable       = core GT variable
```

This finite replay establishes implementation parity of the mechanics used by the proof; it is not the asymptotic lower bound itself.

## 3. Repair R0 — root affine shortcut cannot intercept H_n

The first counterfamily document relied on finite parity to observe that `visible_affine_root_decision` returns `None`. A universal proof is needed.

Each booster contains one clause on a fresh two-variable scope:

```text
(x OR b).
```

Its satisfying relation is

```text
{(0,1),(1,0),(1,1)},
```

which has cardinality `3`.

Every nonempty affine solution set over `F_2` has cardinality `2^k` for some integer `k`. Therefore this 3-point relation is not affine. Because every booster leaf is fresh, its scope is not completed by another clause into a different relation. The registered root detector requires every clause to be covered by exact affine scope relations before returning an affine decision.

Hence for every `n>=3` the padded family `H_n` contains uncovered non-affine booster clauses and

```text
visible_affine_root_decision(H_n) = None.
```

The counterfamily always enters Policy-0A's recursive cache/Resolution path. □

## 4. Resolution-sink induction

Freeze

```text
B = 256 n^2
p = 64 n^2.
```

The source `GT_n` contributes exactly

```text
L_GT = 3 n (n-1)^2
```

literal occurrences.

The booster contribution is

```text
L_boost = 2 * n(n-1) * B,
```

and the sink contributes

```text
L_sink = 6p.
```

Thus

```text
L0 = 3n(n-1)^2 + 512 n^3(n-1) + 384 n^2
   <= 512 n^4 + 3 n^3 + 384 n^2.
```

The sink pivot `d` has exactly `p^2=4096n^4` complementary parent pairs. Algebraically

```text
p^2 - 4L0 > 0
```

for every `n>=1`; using the displayed upper bound the difference is at least

```text
4n(512n^3 + 509n^2 - 378n - 3) > 0.
```

Every `d`-resolvent contains both `a` and `~a`, hence is tautological and is rejected after its attempt is charged. So the local pass consumes its complete attempt budget at the first pivot and adds zero clauses.

Since it adds zero clauses, restriction and unit propagation can only decrease the later literal count. The same inequality therefore holds inductively at every nonterminal state. Core Resolution is never reached. □

## 5. Branch-isolation induction

Every unassigned core variable retains `B=256n^2` private booster occurrences. The two largest sink frequencies are `2p=128n^2`; private leaves have frequency one. Thus a remaining core variable always strictly beats all padding variables under the registered frequency rule.

When a core variable is true, all its booster clauses disappear. When false, those clauses become private positive units and disappear after unit propagation. They cannot force any other core variable.

Therefore all branch decisions before contradiction are core decisions, and padding never controls the semantic search. □

## 6. Projection lemma, re-derived

For an augmented pre-resolution key `K`, let `P(K)` delete all clauses containing a padding variable.

Induct on core branch depth.

**Base.** Before the first branch, padding shares no variable with the GT clauses except that each booster contains exactly one core variable and one private leaf. With no core assignment, boosters do not produce units. Therefore projecting after exhaustive UP leaves exactly `unitprop(GT_n)`.

**Step.** Assume the projection at a state equals `unitprop(GT_n|rho)`. The selected branch variable is a core variable `x`. Applying `x=v` to the full state applies the same restriction to the core. Booster side effects are either clause deletion (`v=1`) or private unit assignments (`v=0`); neither changes another core clause. Sink clauses are unchanged. By the resolution-sink lemma, no local derived clause is ever introduced. Exhaustive UP on core clauses is therefore exactly the same in the full state and the isolated core.

Hence the child projection is

```text
P(K_child) = unitprop(GT_n | (rho union {x=v})).
```

This proves the invariant for all reached states. □

If two augmented exact keys are equal, applying deterministic projection gives equal core residuals. Therefore augmented caching cannot merge two distinct projected GT residuals.

The projected branch/cache execution is consequently a valid exact Formula-Caching execution on `GT_n`. Any augmented cache hit becomes a legal exact projected cache hit; the augmented execution may fail to exploit some equal projected residuals, which can only make it larger, not invalidate it.

## 7. Residual-count transfer

Theorem 4.28 applies to the projected exact-FC execution because exact FC is a restricted case of `FCWS`. The theorem's proof guarantees at least

```text
2^(n-2)
```

distinct projected residual formulas.

Distinct projected residuals require distinct augmented exact keys. Therefore

```text
S(H_n) >= 2^(n-2).
```

## 8. Exact parameter audit

Counts are polynomial in `n`:

```text
core variables          = n(n-1)
booster clauses/leaves  = B*n(n-1) = 256 n^3(n-1) = O(n^4)
sink clauses            = 2p = 128 n^2
sink variables          = 2 + 2p = O(n^2)
core clauses            = n((n-1)^2 + 1) = O(n^3)
literal occurrences     = O(n^4)
maximum variable id     = O(n^4)
```

Freeze the canonical complexity encoding to a standard signed-binary literal-list encoding with self-delimiting clause/list separators. A literal id at most `O(n^4)` uses `O(log n)` bits. Therefore

```text
N_n = O(n^4 log n).
```

For every fixed constant `c`, `N_n^c` is polynomial in `n`, while `2^(n-2)` dominates every polynomial. Hence

```text
S(H_n) / N_n^c -> infinity.
```

No universal fixed `c` can satisfy `S(F)<=|F|^c` for every CNF under this canonical encoding. □

## 9. Review verdict

All current gates are now derivationally closed:

```text
R0_ROOT_AFFINE_BYPASS                 = PROVED_IMPOSSIBLE
R1_REGISTERED_POLICY_PARITY           = CI_PASS
R2_SINK_BUDGET_STARVATION             = PROVED + FINITE_REPLAY_PASS
R3_CORE_ONLY_BRANCHING                = PROVED + FINITE_REPLAY_PASS
R4_CORE_PROJECTION                    = PROVED + FINITE_REPLAY_PASS
R5_SOURCE_GT_THEOREM_SCOPE            = PRIMARY_SOURCE_RECHECKED
R6_n_TO_INPUT_BITS                    = PROVED_UNDER_FROZEN_BINARY_ENCODING
```

Therefore the mathematical status recommended to the parent issue is:

```text
UNIVERSAL_POLYNOMIAL_RESIDUAL_COUNT_FOR_CURRENT_POLICY0A = REFUTED
```

The conditional theorem

```text
POLY_STATE_COUNT + POLY_STATE_SIZE + POLY_PRIMITIVES => P=NP
```

remains valid. What fails is the first premise for this specific Policy-0A.

`P_VS_NP = OPEN`.
