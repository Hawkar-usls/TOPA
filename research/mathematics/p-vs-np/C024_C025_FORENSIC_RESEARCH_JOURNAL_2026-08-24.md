# C024 → C025 Forensic Research Journal

**Date frozen:** 2026-08-24  
**Canonical home:** `Hawkar-usls/TOPA`  
**Provider:** `Hawkar-usls/Janus-Fundamentum`  
**Scope:** the mathematical P-vs-NP / proof-complexity line from the C024 residual-cache bridge through the current C025-E2R-L1G-F3-D frontier.  
**Global claim ceiling:** `P_VS_NP = OPEN`.

This is not a victory log. It is a forensic dependency journal. Every stage records what we tried, what survived, what failed, what was repaired, and which obligation was merely moved downstream.

---

## 0. Status grammar

- `PROVED` — analytical derivation accepted in the stated scope.
- `PROVIDER_PASS` — executable finite mechanics replayed successfully in Fundamentum CI; this does not by itself prove an asymptotic theorem.
- `REFUTED` — a frozen claim or route has a rigorous counterexample/counterfamily or a decisive source-theorem obstruction.
- `CONDITIONAL` — implication proved, but one or more premises remain open.
- `OPEN` — no proof or refutation.
- `DEFERRED` — intentionally not attacked until an upstream gate is resolved.
- `DRIFT` — repository/status surface no longer matches the current proof state.

Hard law:

```text
PROVIDER_PASS != UNIVERSAL_THEOREM
SHORT_PROOF_EXISTS != DETERMINISTIC_POLICY_FINDS_IT
POLY_WORK_IN_CURRENT_STATE != POLY_WORK_IN_ORIGINAL_INPUT
SOUNDNESS != CERTIFICATE_SIZE != CACHE_SIZE != DISCOVERY != TOTAL_RUNTIME
```

---

# I. C024 — the residual-cache bridge

## J00 — Conditional bridge architecture

**Goal.** Turn exact residual caching into a mathematically explicit SAT complexity bridge rather than infer polynomiality from finite runs.

**Established.** For uncapped exact Policy-0A:

- soundness/completeness;
- exact-cache soundness;
- recursion depth bounded by number of variables;
- `recursive_calls <= 2 * unique_states + 1`;
- local primitive work polynomial in the current representation size;
- conditional theorem:

```text
POLY_UNIQUE_STATES
AND POLY_STATE_SIZE
AND POLY_PRIMITIVE_COSTS
=> POLY_CNF_SAT
=> P = NP.
```

**What was still missing.** Two universal premises:

- #211: polynomial number of distinct exact residuals;
- #212: polynomial encoded size of every active residual/state.

**Why this stage was insufficient.** It proved an implication, not the premises.

Canonical continuation receipt: `data/JANUS-P-VS-NP-POLYNOMIAL-RESIDUAL-CACHE-BRIDGE-CONTINUATION-2026-08-24-v1.2.json`.

---

## J01 — theorem-object identity repair

**Attack.** Transfer Formula-Caching lower-bound information from `GT_n` into Policy-0A.

**Failure found.** The older compact “smart GT” proxy was not literally the theorem object. It used one variable per unordered pair with orientation encoded by sign, whereas source `GT_n` uses directed variables `x(i,j)` for `i != j`.

**Repair.** Reject direct theorem transfer and implement theorem-matched directed `GT_n`.

**Extracted law.**

```text
SIMILAR_ENCODING != THEOREM_OBJECT
THEOREM_TRANSFER_REQUIRES_IDENTITY_OR_PROVED_REDUCTION
```

**Residual gap.** A correct source object was necessary, but still did not settle #211.

---

## J02 — positive invariant attempt A1

**Candidate.** Preserve an incomparability signature through unit propagation/local Resolution.

**Survivor.** The original totality clause for pair `{i,j}` remains exactly when the pair is still incomparable after exhaustive UP; exact cache-key equality preserves the incomparability graph.

**Failure/limit.** Undirected incomparability does not recover the directed orientation/prune information needed for the intended lower-bound transfer.

**Decision.** Preserve A1.1 as a valid partial invariant, but do not pretend A1.2 is proved. Switch to a direct counterfamily attack.

---

## J03 — Issue #211 killed by the resolution-sink counterfamily

**Frozen target.** Universal `S(F) <= N^c` for current Policy-0A.

**Counterfamily.**

```text
H_n = GT_n AND BOOST_n AND SINK_n
B = 256 n^2
p = 64 n^2
```

The smallest-ID sink pivot has enough complementary pairs to consume the entire frozen `max(64,4L)` attempt budget while every resolvent is tautological and no clause is added. Uniform private boosters keep the branch rule inside the directed GT core.

Projection of augmented exact keys gives the theorem-matched Formula-Caching residuals of `GT_n`. Therefore:

```text
S(H_n) >= 2^(n-2)
N_n = O(n^4 log n)
```

so no fixed polynomial in `N_n` bounds all exact residuals.

**Status.** `#211 = REFUTED_FOR_CURRENT_POLICY0A`; issue closed completed.

**Provider receipt.** Dedicated C024 replay run `32697547130 = SUCCESS`.

**What died.** Only the first premise for current Policy-0A.

**What survived.** The conditional bridge theorem itself.

**Extracted design constraint.**

```text
LOCAL_INFERENCE_SCHEDULING_MUST_NOT_BE_ADVERSARIALLY_STARVABLE_BY_IRRELEVANT_EARLY_PIVOTS
```

Canonical receipt: `data/TOPA-P-VS-NP-ISSUE-211-REFUTATION-FINAL-2026-08-24-v1.0.json`.

---

## J04 — Issue #212 remained open

**Frozen original target.** Universal polynomial bound on Policy-0A residual representation size.

Known worst-case recurrence exposes the gap:

```text
m_(t+1) <= m_t + max(8,floor(m_t/4))
m_t + 32 <= (5/4)^t (m_0 + 32)
```

This is an upper envelope, not a lower bound. It proves neither polynomiality nor exponential growth.

**Why #212 matters later.** C025 adds clauses, reasons, proof DAGs, extension definitions and indexes. A solver can have cheap local operations and still hide a superpolynomial active representation.

**Forensic warning.** The issue title/body are still specifically about **Policy-0A residual size**, while later work uses `#212` as shorthand for a broader C025 active-representation gate. This scope drift must be repaired by either updating the issue or creating a separate C025-E representation issue.

---

# II. C025 — convert the killer into a successor design

## J05 — C025-A fair scheduler

**Goal.** Remove the exact starvation class that killed Policy-0A.

For a frozen layer with `L` literal occurrences and complementary incidence counts `p_x,q_x`:

```text
A(K) = sum_x p_x q_x <= L^2/4.
```

A complete frozen-layer scan can therefore visit every eligible pivot in polynomial work in the **current** representation size.

### Preserved first CI failure

Run `32698179359 = FAILURE`.

The fixture expected `p^2+1` attempts, but both sink variables `d` and `a` occur with both polarities. A truly fair scheduler must charge both.

**Repair.** Fix fixture accounting only; algorithm and lemma unchanged.

Second run `32698305504 = SUCCESS`:

```text
literal_occurrences = 484
attempts = 12801
sink_d = 6400
sink_a = 6400
core = 1
```

**Closed.** Exact early-pivot starvation class.

**Not closed.** What to retain after the scan, state growth, proof search, total runtime.

Canonical failure/repair receipt: `data/TOPA-C025-FAIR-SCHEDULER-FAILURE-REPAIR-2026-08-24-v1.0.json`.

---

## J06 — C025-B context-independent proof-carrying reason

**Goal.** Replace bare `residual -> UNSAT` with a reusable, checkable reason.

Final plain-Resolution object:

```text
R = (
  root_fingerprint,
  advertised_clause C,
  final_node,
  reachable Resolution-DAG pi
)
```

Accepted `R` proves `F0 |= C`; if a later partial assignment falsifies `C`, then `F0|rho` is UNSAT.

### Post-PASS portability hole

Old shape used a local node number in a producer `ProofStore`. It was sound inside one store but not genuinely standalone: the same integer could mean something else in another store.

**Repair.** Materialize the reachable proof DAG inside the portable certificate and reject unreachable serialized proof garbage.

Provider run `32699409560 = SUCCESS`.

**New cost exposed.**

```text
ONE_NEW_SHARED_DAG_NODE != CONSTANT_PORTABLE_BYTES
```

**Status.** Soundness/portability `PROVED_IN_SCOPE`; size/discovery remain open.

Canonical receipt: `data/TOPA-C025-B-PROOF-CARRYING-REASON-2026-08-24-v1.1.json`.

---

## J07 — C025-C1 exact existing-reason query

**Goal.** Remove ambiguity from “look up a cached reason”.

For current partial assignment `rho`, define `FALSE(rho)`. A certified clause reason `C` is applicable iff:

```text
C subseteq FALSE(rho).
```

Occurrence lists + per-reason falsification counters + exact trail rollback give total forward update cost at most

```text
M = sum_i |C_i|
```

along a monotone assignment path.

Provider run `32699767758 = SUCCESS`.

**Closed.** Query over an already-materialized certified cache is polynomial in explicit cache volume `M`.

**Open.** `M = poly(N)`.

**Extracted law.**

```text
FAST_INDEX_IN_M != SMALL_CACHE_IN_N
```

Canonical receipt: `data/TOPA-C025-C1-REASON-CACHE-QUERY-2026-08-24-v1.0.json`.

---

## J08 — C025-E1 plain Resolution certificate barrier

At the root context, a reusable reason must be falsified by the empty assignment. Therefore its advertised clause must be empty. A root reason is consequently a Resolution refutation.

Classical Resolution lower bounds, including pigeonhole formulas, therefore refute a universal polynomial-size root-certificate theorem for the plain Resolution reason language.

**Status.**

```text
C025-B SOUNDNESS = SURVIVES
C025-B PORTABILITY = SURVIVES
UNIVERSAL_POLY_PLAIN_RESOLUTION_ROOT_REASON = REFUTED
```

**Design response.** Keep plain Resolution reasons as a local learned layer, but strengthen the universal certificate language.

Canonical receipt: `data/TOPA-C025-E1-RESOLUTION-CERTIFICATE-SIZE-BARRIER-2026-08-24-v1.0.json`.

---

## J09 — C025-B2 extension-aware portable reason

**Frozen extension rule.**

```text
e <-> (a AND b)
(~e OR a)
(~e OR b)
(e OR ~a OR ~b)
```

Fresh IDs are strictly topological. Extension variables may appear internally, but the reusable advertised clause must use root variables only.

### First green run was not accepted as final

TOPA found a payload-accounting hole: the verifier rejected unreachable proof nodes but still allowed valid unused extension definitions to be serialized.

**Repair.** Require the exact transitive definition closure of reachable extension axioms; exporter prunes unused definitions and remaps indices.

Authoritative provider run after repair:

```text
run = 32720170819
job = 97409694435
SUCCESS
```

Negative suite covers freshness, duplicate IDs, descending IDs, forward/cyclic dependency, extension leak, axiom/slot tamper, Resolution tamper, wrong advertised clause/root, unreachable proof garbage and unused-definition garbage.

**Status.** `B2_SOUNDNESS = PROVED_IN_SCOPE`.

**Still open.** Universal proof size; extension discovery; total active representation; global proof search.

Canonical receipt: `data/TOPA-C025-B2-EXTENSION-AWARE-REASON-PROVIDER-PASS-2026-08-24-v1.0.json`.

---

# III. E2 — certificate-size frontier becomes proof complexity

## J10 — B2 is polynomially equivalent to Extended Resolution

Object audit showed that frozen B2 is a normal form of standard Extended Resolution on CNF refutations, up to polynomial translations. Therefore the global question

```text
DOES_EVERY_UNSAT_CNF_HAVE_POLY_SIZE_B2_CERTIFICATE?
```

is the classical Extended-Resolution p-boundedness frontier.

**Consequence if positive.** Polynomially verifiable UNSAT certificates would give `NP = coNP`; this still would not give `P = NP` without deterministic proof discovery.

**Consequence if negative.** A superpolynomial B2 lower bound would be a major ER/Extended-Frege lower-bound breakthrough.

**Decision.** Do not pretend this is a local Policy-0B lemma. Split:

```text
E2A B2<->ER equivalence = PROVED
E2B global ER p-boundedness = OPEN_MAJOR_EXTERNAL_FRONTIER
```

Canonical receipt: `data/TOPA-C025-E2-ER-P-BOUNDEDNESS-FRONTIER-2026-08-24-v1.0.json`.

---

## J11 — ER3 extension-count reduction

External theorem used: Narrow Extended Resolution (`ER3`, resolvent width <= 3) p-simulates Extended Resolution.

With `K` extension variables and `V=n0+K`, the width-3 clause universe is

```text
1 + 2V + C(2V,2) + C(2V,3) = O(V^3).
```

After duplicate elimination, some ER3 DAG proof can be bounded by

```text
O(N + K + (N+K)^3)
```

up to ordinary encoding factors.

Hence global ER/B2 p-boundedness is equivalent, up to polynomial translations, to a universal polynomial bound on extension count in **some** ER3 refutation.

**New exact global gate.** Fundamentum Issue #217.

**Bibliographic audit performed in this forensic pass.**

- Nicolas Prcovic, *Narrowing Extended Resolution*, ICTAI 2012, DOI `10.1109/ICTAI.2012.81`; available metadata/abstract explicitly states “Narrow Extended Resolution p-simulates (unrestricted) Extended Resolution” and Theorem 1 is `ER3 p-simulates ER`.
- A stronger source-package audit should still freeze the exact proof translation and encoding conventions locally; see gap G07.

Canonical receipt: `data/TOPA-C025-E2R-ER3-EXTENSION-COUNT-REDUCTION-2026-08-24-v1.0.json`.

---

## J12 — naive extension-count invariants were killed before use

### Semantic class count

`K` extension bits yield at most `2^K` signatures, but there are at most `2^n` root assignments. Pure partition counting can therefore force at most linear-in-`n` lower bounds, never the desired superpolynomial `K`.

### Flat CNF/DNF case count

Frozen B2 computes parity with exactly `3(n-1)` AND extensions, while flat root-only parity CNF/DNF needs `2^(n-1)` cases.

**Refuted routes.**

```text
MANY_SEMANTIC_CLASSES => SUPERPOLY_K     FALSE AS METHOD
EXPONENTIAL_FLAT_FORM => EXPONENTIAL_K   FALSE
```

**Next survivor.** Structural locality.

---

# IV. Locality → restricted lower bounds

## J13 — transitive support and the kappa-local/NW-local mismatch

Define transitive root support recursively. It is polarity-invariant and shrinks under root restrictions.

A tempting route was to identify `|support(e)| <= kappa` with the “local extension” notion in Nisan-Wigderson functional encodings.

**TOPA refuted this transfer.** Sokolov locality means that the whole function lives in one fixed NW neighborhood `Vars_i`, not merely that support cardinality is small.

Correct same-neighborhood admission:

```text
exists i:
  support(a) union support(b) subseteq Vars_i
```

Provider locality replay passed; the direct `kappa-local -> NW-local` transfer is explicitly refuted.

Canonical receipt: `data/TOPA-C025-E2R-L1-LOCALITY-PROVIDER-PASS-2026-08-24-v1.0.json`.

---

## J14 — L1E first genuine restricted superpolynomial extension-count lower bound

Using Sokolov’s heavy-width Resolution lower bound for the full functional NW encoding, parity base functions, and a direct root-only parity CNF family `DIRPARITY(G,b)`, we proved the transfer for **NW-neighborhood-local ER3**.

Direct input size:

```text
N_n = O(m * 2^Delta * Delta * log n)
```

In the source regime `m=n^(2-delta)`, `Delta=log^(2-delta)n`, Sokolov gives Resolution size `exp(n^Omega(delta))`, which remains superpolynomial in the direct encoded input.

Therefore, for every fixed `c`, sufficiently large members require

```text
K > N_n^c
```

in every **NW-neighborhood-local ER3** refutation.

Provider transfer-mechanics run `32729767369 = SUCCESS`.

**Critical ceiling.** This is not unrestricted ER3. Escape resource: cross-neighborhood mixing.

**External theorem rechecked in this forensic pass.** Dmitry Sokolov, *Pseudorandom Generators, Resolution and Heavy Width*, CCC 2022, DOI `10.4230/LIPIcs.CCC.2022.15`. The published paper’s Theorem 14 is the formal heavy-width lower bound and Theorem 15 gives the high-probability `exp(n^Omega(delta))` regime. Lemma 12 states functional forms are stable under partial `x`-assignments; Algorithm 1/Definition 20 constructs the self-reductions used later.

Canonical receipt: `data/TOPA-C025-E2R-L1E-NW-LOCAL-ER3-LOWER-BOUND-2026-08-24-v1.0.json`.

---

## J15 — L1F crossing-elimination tradeoff

A topologically last crossing extension can be eliminated from the Resolution derivation at line-count factor at most 2. Iterating over `t` crossings gives

```text
S_local <= S * 2^t.
```

Thus if local Resolution requires size `L`:

```text
S * 2^t >= L.
```

In a separate fixed-constant `Delta = C log n` polynomial-input regime, every polynomial-size proof requires

```text
t >= Omega(N^alpha)
```

for some fixed `alpha>0`.

**Important parameter firewall.** This is a different parameter regime from the maximal-degree L1E theorem. They must not be silently merged. See gap G11.

Provider run `32746842601 = SUCCESS`.

**Still possible.** Polynomially many crossing gates may be enough.

Canonical receipt: `data/TOPA-C025-E2R-L1F-CROSSING-TRADEOFF-PROVIDER-PASS-2026-08-24-v1.0.json`.

---

# V. Polarity structure of the crossing escape

## J16 — generic polynomial elimination refuted; monotone crossing restricted

Parity again kills a generic `poly(t)` decompression theorem: a linear B2 circuit can expand to exponentially many root clauses.

Restrict instead to **crossing-monotone** dependency: crossing macros are never used negatively as operands of later crossing macros. Then every crossing macro flattens to a conjunction of local literals and ER3 macro clauses expand only polynomially.

Result on the NW hard family:

```text
POLY_SIZE_CROSSING_MONOTONE_ER3_REFUTATION = IMPOSSIBLE
```

Therefore any polynomial-size unrestricted escape needs at least one negative dependency edge between crossing macros.

### Preserved L1G CI failure

Run `32747919279 = FAILURE` because a fixture incorrectly asserted exact Cartesian product count `2*3*4=24`. Overlapping macros canonicalized to 11 distinct clauses.

**Repair.** Correct theorem is an upper bound, not equality:

```text
|EXP(C)| <= product_j leaves(e_j).
```

Authoritative repaired run `32748097836 = SUCCESS`.

Canonical receipts:

- `data/TOPA-C025-E2R-L1G-FIRST-CI-FAILURE-REPAIR-2026-08-24-v1.0.json`
- `data/TOPA-C025-E2R-L1G-MONOTONE-CROSSING-PROVIDER-PASS-2026-08-24-v1.0.json`

---

## J17 — F1 negative-edge representation budget

Let `q(e)` count distinct negative crossing dependency edges in a macro cone. Positive-closure decomposition yields a structural CNF representation bound

```text
|CNFEXP(±e)| <= S^((q(e)+2)!).
```

**Implementation mistake caught.** The first replay tried to materialize the astronomical integer `S^((q+2)!)`. The theorem needs only comparison, not construction.

**Repair.** Compare logarithms.

Extracted law:

```text
BOUND != OBJECT_TO_MATERIALIZE
```

Representation alone still did not imply a small proof after macro cuts. F2 became the next gate.

---

## J18 — F2 proof-level macro cut elimination

Initial proof route used weakening as scaffolding. Before promotion we found a cleaner route:

```text
RESTRICT -> REFUTE -> LIFT
```

Pure Resolution is stable under restriction; contextual proofs can be recovered as a subclause of the desired context. This avoids silently strengthening the proof system.

Final bound:

```text
S_local <= S^((q+5)!).
```

On the stated existential polynomial-input NW-parity family, every polynomial-size B2/ER3 escape must satisfy

```text
q = Omega(log N / log log N).
```

Authoritative provider:

```text
run = 32753914462
job = 97516954725
SUCCESS
```

**Meaning.** Constant polarity-inversion complexity is impossible in the stated restricted transfer.

**Not meaning.** No superpolynomial total extension-count lower bound for unrestricted ER3.

Canonical receipt: `data/TOPA-C025-E2R-L1G-F2-MACRO-CUT-PROVIDER-PASS-2026-08-24-v1.0.json`.

---

## J19 — F3 depth alone dies; width × depth survives

**Failed invariant.** Inversion depth alone.

Take disjoint `G_j = x_j AND y_j` and aggregate `AND_j (~G_j)` with positive aggregate reuse. The inversion depth is 1, the circuit has size `O(k)`, yet the exact CNF of the negation has `2^k` clauses.

So:

```text
BOUNDED_INVERSION_DEPTH != POLY_EXPANSION
```

Define instead:

- `d` = maximum negative-edge depth;
- `b` = maximum negative-frontier width exposed by positive closure.

Paired representation theorem:

```text
|CNFEXP(±e)| <= S^((b+2)^(d+1)).
```

Paired proof-level macro-cut theorem:

```text
S_local <= S^(7*(b+2)^(d+1)).
```

Therefore every polynomial-size escape on the stated hard family obeys

```text
(d+1) * log(b+2) = Omega(log N).
```

Provider:

```text
run = 32754807213
job = 97519752439
SUCCESS
```

**Interpretation.** A short escape must be wide in negative frontier, deep in serial inversion, or both.

Canonical receipt: `data/TOPA-C025-E2R-L1G-F3-WIDTH-DEPTH-PROVIDER-PASS-2026-08-24-v1.0.json`.

---

# VI. Current endpoint — F3-D

## J20 — surviving polarity structure under the actual NW self-reduction

This is the first currently-unclosed mathematical front.

Original `(b,d)` is not enough. Under a root restriction, extension functions can:

- lose support;
- become constants;
- become aliases;
- become NW-local even if originally crossing;
- remove negative crossing edges from the surviving semantic circuit.

Therefore we need residual measures

```text
b_rho(e), d_rho(e)
```

after **semantic simplification/reclassification**, not merely syntactic deletion.

Sokolov’s published machinery helps but does not automatically solve this:

- Lemma 12: functional forms are stable under partial x-assignments;
- Definition 20 / Algorithm 1: the proof is hit by structured self-reductions produced by assigning neighborhoods/output constraints;
- the restricted formula remains equivalent to a smaller NW instance.

The missing bridge is:

```text
LARGE_ORIGINAL_POLARITY_STRUCTURE
    -> ENOUGH_SURVIVING_SEMANTIC_POLARITY_STRUCTURE
       UNDER_THE_EXACT_SOURCE_SELF_REDUCTION
```

Hard law:

```text
SYNTACTIC_SUPPORT_SURVIVES != SEMANTIC_MACRO_SURVIVES
```

**Current status.** `F3-D = OPEN / NEXT`.

---

# VII. Forensic gap ledger — ranked

## P0 — blocks any algorithmic P=NP bridge

### G00 — Policy-0B is not yet one fully frozen deterministic machine

We have a fair scheduler, certificate grammars, cache query, proof-complexity analyses and structural attacks, but not one final deterministic transition system specifying all of:

```text
lookup -> propagation -> fair scan -> retention -> extension proposal -> branch -> returned reason
```

Missing or not globally frozen: candidate-retention rule, deletion/subsumption rule, exact extension-definition proposal rule, tie/order rules for new reason generation, and their interaction.

**Risk.** A runtime theorem cannot be about “Policy-0B” if the full machine is not a unique mathematical object.

**Repair target.** Freeze `POLICY0B.1_COMPLETE_TRANSITION_SYSTEM` before C2 proof-search claims.

### G01 — active representation in original input length is still open

Issue #212 never established a universal polynomial bound. C025 now has more representation classes than C024:

- active clauses/candidates;
- reason cache;
- applicability index;
- extension definitions;
- proof DAGs;
- portable certificate materializations;
- canonicalization/hash/index structures.

**Repair target.** Split or broaden #212 into an exact C025-E representation theorem with an explicit byte accounting model.

### G02 — F3-D semantic restriction survival

Current most important mathematical gap. Need to measure surviving semantic crossing/inversion structure under the exact NW self-reduction, not arbitrary restrictions.

**Exit:** theorem or counterexample for `(b,d) -> (b_rho,d_rho)` plus semantic collapse.

### G03 — deterministic extension/reason/proof discovery

Issue #215 C2 remains deferred/open. Efficient verification and existence of short proofs do not give an efficient search algorithm.

**Repair target.** After the proof-size gate is sufficiently understood, freeze deterministic extension proposal/extraction and charge all failed proposals/states.

---

## P1 — threatens theorem transfer or validation coverage

### G04 — global #217 remains the ER/EF frontier

Restricted lower bounds do not settle unrestricted ER3 extension count. Do not spend local finite compute as though it can brute-force this asymptotic frontier.

### G05 — hard NW family is existential/high-probability, not deterministically explicit

L1E uses suitable random graphs with high probability. We do not yet have a deterministic explicit hard graph generator/certificate integrated into the adversarial suite.

**Repair target.** Either construct explicit graphs satisfying the required expansion properties or freeze verifiable graph-property certificates for generated instances.

### G06 — C025-F adversarial regression suite is incomplete/not verified

Umbrella Issue #213 explicitly requires at minimum:

- theorem-matched GT;
- padded GT sink;
- masked/lifted Tseitin;
- PHP;
- near-threshold random 3-SAT controls;
- synthetic pivot/frequency/index padding.

The current C025 provider workflow clearly runs the scheduler/reason/B2/E2R structural probes. The branch contains several Tseitin programs, including a Policy-0A masked-Tseitin script, but this audit did **not** verify a dedicated Policy-0B replay covering PHP and near-threshold random 3-SAT, and no obvious PHP C025 fixture appeared in the direct experiment listing.

**Status:** `NOT_VERIFIED / LIKELY_COVERAGE_GAP`, not “family absent from repository”.

**Repair target.** One `validate-c025-adversarial-families.yml` with explicit Policy-0B fixtures and frozen expected claim ceilings.

### G07 — external theorem package audit needs one immutable source ledger

Verified in this pass:

- Sokolov CCC 2022 metadata, DOI, Theorem 14/15 and Lemma 12/self-reduction text;
- Prcovic ICTAI 2012 metadata/DOI and the explicit ER3 p-simulates ER theorem statement.

Still desirable: one repository document freezing exact theorem numbers/pages, hypotheses, translation objects, parameter variables, and the exact internal lemma that consumes each source theorem.

### G08 — full p-simulation should have an executable translator or independent second derivation

B2↔ER and ER→ER3 are currently mathematical translation arguments plus external theorem use. A full executable translation on finite certificates would improve object-identity assurance, without pretending finite replay proves p-simulation asymptotics.

### G09 — analytical F2/F3 are not machine-checked proofs

Provider CI validates finite mechanics and recurrence sanity. The asymptotic theorems remain prose mathematics. This is normal, but for a high-stakes proof-complexity line we should add an independent derivation/audit, and eventually Lean/Coq/Isabelle or a small custom proof checker for the combinatorial lemmas if practical.

### G10 — semantic axiom inclusion in the NW transfer deserves a frozen source-line receipt

L1E’s key transfer says direct root clauses and legal local extension clauses are semantic axioms of the source functional encoding. This has an analytical derivation + finite probe. Freeze the exact source Definition/Lemma ranges and a second independent object-level derivation.

### G11 — parameter regimes are split and easy to conflate

L1E uses approximately `Delta=log^(2-delta)n`; L1F uses a fixed-constant multiple of `log n` to make the direct encoding polynomial. Later F2/F3 write the lower bound as `exp(N^eta)` after absorbing losses.

**Repair target.** A `C025_E2R_PARAMETER_LEDGER.md` with one row per theorem and explicit maps among `n,m,Delta,r,epsilon,N,K,S,L,eta,alpha`.

### G12 — explicit derivation of `eta` should be frozen

F2/F3 use a shorthand `L(N) >= exp(N^eta)` for some fixed `eta>0` in the polynomial-input regime. Freeze the exact inequality and dependence of `eta` on source parameters instead of leaving “absorb polylog losses” as prose.

### G13 — F3 recurrence needs an independent overlap/DAG-sharing audit

F3 inherited pure context lifting from F2 and passed finite recurrence fixtures. A second derivation should explicitly audit overlapping dependency cones, repeated semantic functions, aliasing, and DAG sharing against the `S^(7(b+2)^(d+1))` accounting.

---

## P2 — project authority/provenance drift

### G14 — `PROJECT_STATUS.json` is stale

At the time of this audit it stops around L1C and still lists the full NW transfer/heavy-width step as open. It does not record L1E, L1F, L1G, F2 or F3.

### G15 — mathematical README is stale

Navigation/current-front text does not yet expose the full `#217 -> #218 -> #219 -> #220 -> #221` chain and the current F3-D endpoint.

### G16 — PR #214 body is stale

The draft PR body stops around the ER3 extension-count reduction and old active-front list. The branch itself contains later work, but the PR summary does not.

### G17 — Issue #221 body is pre-provider-pass

It still labels F3 proof-level cut elimination as a candidate/open gate although provider run `32754807213` has already passed and the receipt promotes F3 in stated scope.

### G18 — PR #210 lifecycle ambiguity

C024 #211 is conclusively refuted and successor work moved to C025, but draft PR #210 remains open. This is not mathematically wrong, but an open historical draft can look like a competing active authority.

**Repair options:** close/archive as completed negative-result line, or prominently mark it frozen/historical and point to C025.

### G19 — #212 scope drift

Original issue: Policy-0A residual-size theorem. Later references: all C025 active representation. This should be split or renamed to prevent a future false inference that resolving the old residual-only statement settles all new representation classes.

---

# VIII. Repair queue

Recommended order:

```text
R1  Sync authority surfaces:
    PROJECT_STATUS + math README + PR214 + Issue221

R2  Freeze parameter/source ledger:
    exact Sokolov/ER3 theorem mapping + eta/alpha derivations

R3  Finish F3-D:
    semantic residual-function simplification
    surviving crossing skeleton
    b_rho, d_rho under the exact NW self-reduction

R4  Restore C025-F adversarial regression:
    GT + padded GT + Policy0B Tseitin + PHP + random 3-SAT + synthetic padding

R5  Freeze complete Policy0B.1 deterministic machine:
    retention/deletion/extension proposal/search order

R6  Split/repair active-representation issue:
    exact byte model for clauses/reasons/extensions/indexes/proofs

R7  Only then resume C2 deterministic proof discovery.
```

The ordering matters. C2 before R5 would analyze an underspecified algorithm. A state-size proof before defining all retained structures would count the wrong object. F3-D before source/parameter normalization risks theorem-transfer drift.

---

# IX. Current dependency graph

```text
C024 CONDITIONAL BRIDGE                     PROVED
        |
        +-- #211 residual count              REFUTED for Policy0A
        |       |
        |       -> Policy0B fair scheduler   PASS
        |
        +-- #212 state/representation        OPEN / scope needs repair

Policy0B
  A scheduler                               PROVED in current size
  B plain portable reason                   PROVED in scope
  C1 cached reason query                    PROVED in explicit M
  E1 plain root proof-size                  REFUTED as universal language
  B2 extension-aware reason                 PROVED in scope
       |
       -> E2 global proof-size = ER frontier OPEN
             |
             -> ER3 extension count #217     OPEN
                    |
                    -> class-count route     REFUTED
                    -> kappa->NW transfer    REFUTED
                    -> NW-local L1E           SUPERPOLY K, restricted
                           |
                           -> crossing L1F    t >= N^alpha, restricted
                                  |
                                  -> L1G monotone crossing impossible
                                         |
                                         -> F2 q >= logN/loglogN
                                                |
                                                -> F3 width-depth tradeoff
                                                       |
                                                       -> F3-D semantic restriction survival OPEN

Orthogonal blockers:
  complete Policy0B machine                 NOT FROZEN
  active representation in N               OPEN
  deterministic proof discovery C2          OPEN/DEFERRED
  adversarial family regression C025-F      NOT VERIFIED COMPLETE

P_VS_NP                                     OPEN
```

---

# X. Source audit snapshot

## Sokolov — verified in this forensic pass

Dmitry Sokolov, **Pseudorandom Generators, Resolution and Heavy Width**, CCC 2022, LIPIcs 234, Article 15, DOI `10.4230/LIPIcs.CCC.2022.15`.

Verified relevant objects from the published paper:

- functional encoding permits local variables depending on one NW neighborhood;
- Lemma 12: functional form remains a functional form after partial x-assignment;
- Definition 20 / Algorithm 1: structured self-reduction by partial x-assignments;
- Theorem 14: formal heavy-width Resolution size lower bound;
- Theorem 15: high-probability random-graph regime with size `exp(n^Omega(delta))` for `m=n^(2-delta)`, `Delta=log^(2-delta)n`.

## Prcovic — theorem statement/metadata verified

Nicolas Prcovic, **Narrowing Extended Resolution**, ICTAI 2012, pp. 556–563, DOI `10.1109/ICTAI.2012.81`.

Verified statement: Narrow Extended Resolution / ER3 p-simulates unrestricted Extended Resolution; Theorem 1 in the available text is `ER3 p-simulates ER`.

**Open source-packaging action:** preserve an immutable local theorem-transfer receipt with exact source text/page and the internal translation contract.

---

# XI. Final forensic verdict

The project did not discover one hidden fatal flaw. It discovered a **sequence of moved exponentials**, and each successful move made the next location more explicit:

```text
residual count
 -> scheduler starvation
 -> state retention
 -> reason portability
 -> certificate bytes
 -> proof-system proof size
 -> extension count
 -> locality
 -> cross-neighborhood mixing
 -> polarity inversion count
 -> inversion frontier width/depth
 -> semantic survival under restrictions
```

That is scientific progress even though `P vs NP` is still open: each stage removes a vague escape hatch and replaces it with a named, falsifiable resource.

The most dangerous remaining holes are not the famous global #217 by itself. They are the **interfaces** where a hidden exponential can still be smuggled into an algorithmic claim:

```text
UNFROZEN POLICY0B MACHINE
ACTIVE REPRESENTATION SIZE
SEMANTIC RESTRICTION SURVIVAL
DETERMINISTIC PROOF DISCOVERY
```

Those four must remain red until separately closed.
