# C025 Hidden Exponent Audit

**Frozen:** 2026-08-24  
**Canonical home:** `Hawkar-usls/TOPA`  
**Scope:** C024/C025 mathematical lane through `C025-E2R-L1G-F3-D`.  
**Status:** active complexity firewall.  
**Global ceiling:** `P_VS_NP = OPEN`.

## 0. Definition of a hidden exponent

For TOPA, a complexity statement counts as a polynomial bound in original input length `N` only if it has the form

```text
T(N) <= C * N^c
```

for all sufficiently large valid inputs, where **both `C` and `c` are fixed constants independent of the input instance and of every growing family parameter**.

The following is not enough:

```text
T <= S^f(N)
```

unless `S<=poly(N)` and `f(N)=O(1)` with a universal constant.

Likewise `poly(L)`, `poly(M)`, `poly(K)`, or `poly(|pi|)` is not `poly(N)` until the corresponding derived object is itself universally polynomially bounded in `N`.

---

# I. Exponents already exposed

## HX00 — unique residual/state count

**Old hiding place:** number of exact residuals.

Policy-0A had polynomial recursion depth and polynomial local work but could still encounter exponentially many unique residuals.

**Disposition:** `REFUTED_FOR_CURRENT_POLICY0A` by the padded directed-GT resolution-sink counterfamily.

**Lesson:**

```text
POLYNOMIAL_DEPTH != POLYNOMIAL_NUMBER_OF_STATES
```

This hiding place is closed for the old positive Policy-0A route because the required premise is false.

---

## HX01 — current representation size `L`

C025-A proves a fair layer has at most

```text
sum_x p_x q_x <= L^2/4
```

pair attempts.

This is polynomial **in current literal volume `L`** only.

**Open transfer:**

```text
L <= poly(N)
```

is not proved for all active C025 states.

**Status:** `OPEN_P0`.

---

## HX02 — repeated layer growth / retention

A single fair layer may expose `O(L^2)` distinct candidate resolvents. Even if each layer is polynomial in its input representation, repeated retention over polynomial branch depth can create a multiplicative recurrence.

Possible hidden form:

```text
L_(t+1) <= L_t + O(L_t^2)
```

or another superlinear retained-state recurrence, depending on the final retention rule.

No total recurrence can be proved yet because Policy-0B retention/deletion is not fully frozen.

**Status:** `OPEN_P0`.

---

## HX03 — reason-cache volume `M`

C025-C1 proves exact applicability maintenance in work polynomial in

```text
M = sum_i |C_i|.
```

Hidden exponent/resource can reside in the number and total size of cached reasons.

Required missing theorem:

```text
M <= N^c
```

for one universal fixed `c`, under the exact final retention/deletion rules.

**Status:** `OPEN_P0`.

---

## HX04 — shared logical DAG versus portable bytes

A branch composition may add only `O(1)` new logical proof nodes while portable standalone export includes the reachable child sub-DAGs.

Therefore:

```text
ONE_NEW_LOGICAL_NODE != O(1) NEW_PORTABLE_BYTES
```

The exponent can hide in repeated serialization/materialization even when logical sharing is cheap.

**Disposition:** interface bug already repaired locally; global total portable-byte bound remains open.

---

## HX05 — extension count `K`

For ER3 with `V=n0+K`, the width-3 clause universe is `O(V^3)` and some deduplicated DAG proof has size

```text
O(N + K + (N+K)^3)
```

up to normal encoding factors.

This is polynomial in `N` **iff `K<=poly(N)`** with a universal fixed exponent.

The missing global theorem is precisely Issue #217.

**Status:** `OPEN_MAJOR_EXTERNAL_FRONTIER`.

---

## HX06 — extension-definition discovery

Even if some proof uses `K<=poly(N)` extensions, a deterministic generator may have to search among many candidate operand pairs and nested definitions.

For `V` currently available variables there are already `Theta(V^2)` literal-AND pairs at one introduction step. Naively iterating this for `K` introductions creates a search tree whose size can be roughly

```text
(V^2)^K
```

before pruning.

This is not asserted as a lower bound for the final algorithm; it identifies the exact location where a deterministic discovery theorem is required.

**Status:** `OPEN_P0_C025_C2`.

---

## HX07 — proof search versus proof verification

A certificate verifier can be polynomial in encoded proof length `|pi|` while the deterministic search for a suitable proof is superpolynomial.

Required firewall:

```text
VERIFY(pi) IN poly(|pi|) != FIND(pi) IN poly(N)
```

**Status:** `OPEN_P0`.

---

# II. Exponents in the current NW / crossing / polarity line

## HX08 — crossing elimination `2^t`

L1F gives

```text
S_local <= S * 2^t
```

for eliminating `t` crossing extensions.

The exponential is explicit. The theorem is useful because comparison with the source lower bound forces a minimum amount of crossing structure in any polynomial-size escape.

**Status:** `EXPOSED_NOT_A_BUG`.

---

## HX09 — F2 factorial exponent

F2 gives an analytical macro-cut ceiling

```text
S_local <= S^((q+5)!)
```

where `q` is the number of negative crossing dependency edges.

### Critical language rule

This is a fixed-degree polynomial in `S` only for fixed `q`.

If `q=q(N)` grows, the exponent grows and the expression can be superpolynomial or much larger in `N`.

The theorem is used correctly as a tradeoff to derive

```text
q = Omega(log N / log log N)
```

for a polynomial-size escape on the frozen restricted family. It must never be summarized as an unconditional polynomial simulation.

**Status:** `EXPOSED_AND_FIREWALLED`.

---

## HX10 — F3 width-depth exponent

F3 gives

```text
S_local <= S^(7*(b+2)^(d+1)).
```

Again, this is polynomial in `S` only when

```text
(b+2)^(d+1) = O(1).
```

If either negative-frontier width `b` or inversion depth `d` grows with `N`, the exponent grows.

This dependence is not an implementation accident: it is the structural resource being measured. Comparison with the NW lower bound yields

```text
(d+1)*log(b+2) = Omega(log N)
```

for polynomial-size escapes in the stated restricted regime.

**Hidden-exponent verdict:** the exponent is mathematically visible but must be made linguistically impossible to hide.

**Status:** `EXPOSED_AND_FIREWALLED`.

---

## HX11 — restriction survival can erase the measured exponent resource

The original proof may have large `b,d`, but after an NW root restriction macros can become constants, aliases or local functions. Then the surviving

```text
b_rho, d_rho
```

may collapse.

Thus even a large pre-restriction F3 exponent resource does not automatically survive into the heavy-width residual formula.

**Current exact front:** `F3-D`.

**Status:** `OPEN_P0`.

---

# III. Parameter-map exponent risks

## HX12 — `n` versus encoded input length `N`

Every source lower bound stated in a structural parameter `n` must be converted into the actual explicit bit length `N` of the generated CNF.

A lower bound such as

```text
exp(n^a)
```

can become polynomial, quasipolynomial or superpolynomial in `N` depending on the encoding blow-up.

**Rule:** every asymptotic receipt must contain both directions needed for the claimed transfer, not just an informal `N=poly(n)` statement.

**Status:** partially done; unified parameter ledger still required.

---

## HX13 — `Delta` regime drift

The locality line uses more than one `Delta` regime. In particular, receipts distinguish an L1E regime around `Delta=log^(2-delta)n` from later polynomial-input regimes using `Delta=C log n`.

A hidden exponent can enter if a bound derived in one regime is substituted into another without re-deriving `N(n)` and the final exponent.

**Status:** `OPEN_AUDIT`.

---

## HX14 — hidden `eta` in `exp(N^eta)`

F2/F3 compare against a source lower bound summarized as

```text
L(N) >= exp(N^eta)
```

for some fixed `eta>0` in the selected polynomial-input regime.

The claim is scientifically adequate only after one explicit derivation freezes a concrete admissible `eta` or a symbolic formula whose positivity is proved from fixed source constants.

**Status:** `OPEN_AUDIT`.

---

## HX15 — constants/exponents inside imported p-simulations

A theorem that system A p-simulates system B guarantees a polynomial translation, but a local project statement must still identify:

- the exact source theorem;
- what the size measure counts;
- whether extension definitions/variable names are included;
- that the translation exponent is a universal constant independent of the formula family.

**Status:** `SOURCE_TRANSFER_LEDGER_REQUIRED`.

---

# IV. Bit-complexity and representation exponents

## HX16 — canonicalization and set operations

Python/set/dict operations are not unit-cost mathematical primitives when keys contain growing clauses, proof nodes or serialized objects.

A rigorous total bound must charge at least:

```text
key construction bytes
hash/equality bytes touched
sorting/canonicalization comparisons
integer/variable-id bit length
serialization/deserialization
```

This does not imply the implementation is slow; it prevents a RAM-model shortcut from becoming a proof claim.

**Status:** `OPEN_FOR_TOTAL_RUNTIME`.

---

## HX17 — hash/fingerprint collision semantics

A cryptographic fingerprint is a practical provenance tool, not an exact mathematical equality oracle unless the formal model treats the full underlying canonical object as authoritative and the hash only as an index/check.

A complexity proof must not obtain exact cache soundness from an assumed collision-free finite hash without specifying the model.

**Required rule:** exact canonical object equality is semantic authority; fixed-length hash is an optimization/index and collision handling must fail closed.

**Status:** `FIREWALL_REQUIRED_IN_COMPLETE_POLICY0B_SPEC`.

---

## HX18 — probabilistic/existential hard instance construction

The NW restricted lower-bound line can use existential/high-probability graph families for a mathematical existence theorem. But an executable adversarial suite cannot silently treat existence as a cheap deterministic constructor.

Potential hidden cost:

```text
search for a graph satisfying expansion property
```

may itself be expensive unless an explicit family or efficiently checkable certificate/construction is supplied.

**Status:** `OPEN_EXPLICITNESS`.

---

# V. Heuristic exponent traps now banned

The Strict Science Gate forbids the following from complexity promotion:

```text
FIT runtime on small n -> extrapolate exponent c
BEST observed seed -> report as family behavior
LOG-LOG straight line -> universal polynomial theorem
NO counterexample found -> polynomial bound
MODEL says likely polynomial -> polynomial bound
FIXED benchmark timeout -> asymptotic lower bound
MEAN runtime -> worst-case polynomial runtime
AVERAGE proof size -> universal proof-size bound
```

Experiments may falsify exact finite claims and validate implementation mechanics. Universal asymptotics require proofs/counterfamilies.

---

# VI. Current hidden-exponent ledger

| ID | Resource | State | Blocks |
|---|---|---|---|
| HX01 | active literal volume `L(N)` | OPEN | scheduler -> total time |
| HX02 | retained resolvent/state recurrence | OPEN | active representation |
| HX03 | reason cache `M(N)` | OPEN | C1 -> input-relative cost |
| HX04 | portable proof bytes | OPEN globally | certificate accounting |
| HX05 | ER3 extension count `K(N)` | OPEN major frontier | E2 |
| HX06 | extension-definition search tree | OPEN | C2 |
| HX07 | proof discovery | OPEN | deterministic solver |
| HX09 | factorial exponent in `q` | exposed | language firewall |
| HX10 | exponent in `(b,d)` | exposed | language firewall |
| HX11 | semantic survival of `b_rho,d_rho` | OPEN / NEXT | F3-D |
| HX12-14 | parameter maps / `eta` | OPEN audit | source lower-bound transfer |
| HX16 | bit complexity | OPEN | total runtime |
| HX17 | hash/equality model | OPEN spec | exact caching |
| HX18 | hard-instance construction | OPEN explicitness | executable regression |

---

# VII. Next scientific attack order

1. **F3-D semantic survival:** define residual Boolean function of each macro under the exact NW restriction and canonical simplification; count only semantically nonlocal surviving negative frontiers.
2. **Parameter ledger:** derive `N(n,Delta,m)` and one fixed valid `eta` for each imported lower-bound regime.
3. **Policy0B.1 complete machine:** freeze retention, deletion, extension proposal, search order and exact equality model.
4. **Active-byte recurrence:** derive or refute a universal bound for clauses + reasons + indexes + extensions + proof DAGs.
5. **Only then C2:** analyze deterministic proof/extension discovery.

No heuristic ranking is permitted to decide whether a gate is closed. A gate closes only by a checkable proof, counterexample/counterfamily, source-bound fact, reproducible finite mechanics result at its finite scope, or a specified statistical inference at its stated uncertainty.
