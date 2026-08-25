# PF5 benchmark admission protocol

Status: **FROZEN SCIENTIFIC PROTOCOL**  
Claim ceiling: **P_VS_NP = OPEN**

## 1. Purpose

A family may enter the PF5 **red / adversarial** benchmark lane only after an explicit proof-complexity upper-bound audit.

The GT12 episode demonstrated why this is mandatory: generic residual/quotient policies hit large caps, yet the exact JANUS graph-tautology encoding has a deterministic cubic Resolution refutation schema with 506 inferences at n=12.

Therefore generic search difficulty cannot be interpreted as proof-system hardness until known family-specific upper bounds have been checked.

---

## 2. Admission questions

For every proposed red family record, before execution:

1. exact generator/encoding and immutable seed or deterministic construction;
2. actual input-size measure `N`;
3. expected SAT/UNSAT regime, if any, separately from exact finite classification;
4. known polynomial algorithms for the language/encoding;
5. known polynomial proof schemas in Resolution, ER/EF/Frege or a stronger admitted system;
6. known lower bounds and the exact proof-system scope of each;
7. whether lower bounds are deterministic-family theorems, random high-probability statements, or finite observations;
8. all experimental caps and operator order;
9. exact reference classification method and its full charged cost;
10. a rule forbidding post-hoc seed, density, cap or operator-order changes after result inspection.

If a polynomial same-system or stronger-system proof schema is found, reclassify the family as a **positive schema control** rather than treating generic cap hits as hardness evidence.

---

## 3. Random sparse 3-CNF candidate lane

### External proof-complexity basis

Classical Chvatal–Szemeredi and later random-CSP proof-complexity results establish exponential Resolution complexity with high probability for appropriate random 3-SAT / random CSP regimes with a linear number of constraints.

This supports using random sparse 3-CNF as a **Resolution-search stress distribution**.

It does NOT establish an Extended Resolution or Frege lower bound.

Modern proof-complexity literature still treats superpolynomial lower bounds for general Frege as a major open problem; recent work obtains lower bounds only for restricted systems/settings.

Therefore the candidate status is:

`RANDOM_3CNF = RED_DISCOVERY_STRESS_WITH_RESOLUTION_SOURCE_LOWER_BOUND_CONTEXT__NOT_A_CLAIMED_ER_HARD_FAMILY`.

### Important density caution

Very dense random formulas can admit short proofs in stronger systems in regimes studied in the literature. The PF5 experiment therefore must not select an arbitrarily huge density merely to force UNSAT.

The frozen first suite uses near-threshold-style constant density `m/n = 4.30` only as an experimental stress choice. Exact SAT/UNSAT status of each finite instance is determined independently; no theorem about the precise 3-SAT threshold at 4.30 is assumed.

---

## 4. Frozen deterministic suite v1

Generator:

- variables: `n in {32,40,48,56,64}`;
- clauses: `m = floor(4.30*n)`;
- each clause has three distinct variables;
- literal signs are independent pseudorandom bits;
- duplicate canonical clauses are rejected;
- RNG: Python `random.Random(seed)` only for finite reproducibility, not cryptographic randomness;
- seed for size `n` is first 64 bits (big-endian) of
  `SHA256("PF5-RANDOM3SAT-RED-V1|n=<n>")`;
- formula accepted exactly as generated; no seed skipping based on SAT status or solver difficulty.

Frozen seeds:

- `n=32`: `6320781990444464615`
- `n=40`: `11525392518347774442`
- `n=48`: `241980694331674918`
- `n=56`: `15760637885256236406`
- `n=64`: `7505710842836848748`

These seeds were derived from the public tag rule before the suite was executed.

---

## 5. Exact reference classification

The first finite pass uses a deterministic complete DPLL reference with:

- exhaustive branching when necessary;
- exact unit propagation;
- deterministic variable selection by maximum current literal occurrence, ties by smallest variable ID;
- false-first branch;
- no learned clauses;
- no semantic oracle;
- node cap `2,000,000` per instance;
- every visited DPLL state charged;
- SAT requires an independently checked full witness;
- UNSAT is accepted only if the complete recursive tree closes under the frozen cap;
- cap hit yields `OPEN_REFERENCE_CAP`, not a guessed answer.

This reference solver is **not** a PF5 progress operator and its cost is not hidden. It exists only to establish finite ground truth when it terminates.

---

## 6. PF5 first-pass operator audit

Before any new family-specific schema is invented, each frozen formula is tested against the already-admitted cheap/exact domains:

1. Horn recognizer/solver;
2. Krom/2-CNF recognizer/solver;
3. explicit affine/XOR recognizer/solver;
4. exact GT-family recognizer;
5. exact PHP/known family-schema recognizers already in the portfolio;
6. incidence component decomposition;
7. PF1 one-step / deterministic repeated factor accounting under a separately frozen state cap;
8. low-width exact lanes only under their already-declared caps;
9. general B2/ER discovery remains `OPEN`, not simulated by a semantic oracle.

A formula escaping all cheap domains becomes a **portfolio coverage witness**, not a proof of hardness.

---

## 7. Interpretation rules

Allowed:

- “the current PF5 portfolio returned UNKNOWN/open on this frozen instance under these caps”;
- “plain Resolution has a source lower-bound context for the random distribution”;
- “a family-specific polynomial schema was found and therefore the benchmark was reclassified.”

Forbidden:

- finite cap hit -> `P!=NP`;
- random Resolution lower bound -> ER/Frege lower bound;
- solver wall-clock -> asymptotic proof complexity;
- seed shopping after inspection;
- raising caps and calling the new run the same preregistered test;
- absence of a found schema -> proof that no polynomial schema exists.

---

## 8. Global closure relation

If a deterministic PF5 controller can, for every CNF of length `N`, choose exact operators and terminate with correct SAT/UNSAT while its full charged

`Q_total = Q_state + Q_proof + Q_discovery + Q_witness`

is bounded by `N^c` for one fixed universal `c`, then SAT is in P and therefore `P=NP`.

The benchmark suite is a falsification/search instrument for that theorem. It is not the theorem itself.

---

## 9. Laws

- `RED_BENCHMARK_REQUIRES_UPPER_BOUND_AUDIT`
- `NO_FOUND_SCHEMA != NO_POLYNOMIAL_SCHEMA`
- `RANDOM_RESOLUTION_HARDNESS != ER_HARDNESS`
- `SEED_SHOPPING_IS_FORBIDDEN_AFTER_FREEZE`
- `REFERENCE_SOLVER_COST_IS_CHARGED_AND_HAS_ZERO_SELECTOR_AUTHORITY`
- `FINITE_PORTFOLIO_ESCAPE != P_NOT_EQUAL_NP`
