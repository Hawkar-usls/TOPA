# C025 — Policy-0B Fair Proof-Carrying Reason Calculus

**Status:** design / first scheduler lemma proved / global polynomiality open.

**Motivation:** C024 Issue #211 is refuted for Policy-0A by a polynomial-size padding family that starves its single global local-Resolution budget at an irrelevant smallest-id pivot. C025 converts that counterexample into a machine design constraint rather than hiding it.

**Claim ceiling:** nothing in C025 currently proves polynomial-time SAT or `P=NP`.

## 1. Laws inherited from the counterexample

A successor calculus must satisfy all of:

```text
NO_EARLY_PIVOT_CAN_STARVE_LATER_PIVOTS
IRRELEVANT_PADDING_MUST_NOT_BLOCK_CORE_INFERENCE
PROOF_EXISTENCE != DETERMINISTIC_PROOF_SEARCH
REASON_REUSE_REQUIRES_CHECKABLE_CONTEXT_INDEPENDENCE
STATE_SIZE_MUST_BE_CHARGED_IN_ORIGINAL_INPUT_LENGTH
CERTIFICATE_GENERATION_AND_REPLAY_ARE_NOT_FREE
```

The first two repair the exact C024-A failure. The remaining four prevent the repair from merely moving the hidden exponential cost elsewhere.

## 2. Policy-0B scheduler candidate

For a pre-resolution CNF key `K`, let

```text
L = literal_occurrences(K).
```

For each variable/pivot `x`, let `p_x` and `q_x` be the numbers of clauses in the frozen start-of-pass clause set containing `x` and `~x` respectively.

Policy-0B-Fair scans **every** complementary parent pair from that frozen set exactly once in canonical order. Newly derived clauses are not used as parents during the same layer.

### Lemma 2.1 — a complete fair one-layer scan is polynomial in current representation size

The number of complementary parent-pair attempts is

```text
A(K) = sum_x p_x q_x.
```

Since

```text
sum_x p_x + sum_x q_x = L,
```

we have

```text
A(K)
  <= (sum_x p_x)(sum_x q_x)
  <= L^2 / 4.
```

Therefore every pivot can be given a complete one-layer scan without a global early-pivot cutoff and with at most `L^2/4` pair attempts. □

### Consequence

The C024 resolution-sink attack no longer starves the GT core: its `d` pivot may contribute many tautological attempts, but after those attempts Policy-0B-Fair continues to every later pivot. An adversary cannot block a core pivot merely by inserting more earlier tautological pairs.

This repairs **scheduler starvation only**. It does not prove that the clauses obtained from core pivots are sufficient for polynomial SAT.

## 3. Do not retain the old addition-budget bug under a new name

A complete one-layer scan can yield `O(L^2)` distinct resolvents. Blindly retaining all of them is polynomial per pass but can compound over polynomial branch depth. Therefore C025 must not infer

```text
FAIR_SCAN => POLYNOMIAL_STATE_SIZE.
```

Issue #212 remains active as a design gate.

Any active-clause retention policy must come with one of:

1. a universal polynomial-size canonical basis theorem;
2. an amortized global potential theorem;
3. a proof-carrying deletion/subsumption theorem preserving all information needed by the solver;
4. an explicit counterfamily showing the proposed retention rule fails.

## 4. Proof-carrying returned reasons

Policy-0B should separate two resources that Policy-0A conflates:

```text
RESIDUAL_BOOLEAN_CACHE
CONTEXT_INDEPENDENT_REASON
```

When an UNSAT child returns, the producer may return a reason object `R` only if a verifier can establish that `R` is derivable from the child's clauses and that its reuse condition is independent of the accidental decision context being discarded.

Candidate initial language: clauses with an explicit Resolution/weakening derivation ledger.

At a branch variable `x`, if the two children return reusable reasons whose derivations support a sound parent reason, the parent may cache that reason rather than only the entire exact residual Boolean judgement.

This is motivated by the known Formula-Caching-with-reasons line, which can simulate regular Resolution. However:

```text
SHORT_PROOF_EXISTS != DETERMINISTIC_POLICY_FINDS_SHORT_PROOF.
```

C025 therefore contains a separate search-complexity gate.

## 5. New killer gates

### C025-A — fair scheduler parity

Implement the complete frozen-layer scan and prove/verify:

```text
attempts <= L^2/4
all pivots with both polarities are visited
resolution-sink padding cannot starve a later GT pivot
```

### C025-B — reason soundness

Specify the exact reason object and prove a standalone verifier sound.

### C025-C — reason extraction cost

Give a deterministic extraction algorithm and charge its total work. Existence of a short reason/proof is insufficient.

### C025-D — deterministic proof-search gap

For every imported proof-system simulation theorem, distinguish:

```text
EXISTENCE_OF_POLYNOMIAL_PROOF
```

from

```text
DETERMINISTIC_POLYNOMIAL_TIME_DISCOVERY_OF_THAT_PROOF.
```

No P-vs-NP promotion is allowed from the first statement alone.

### C025-E — polynomial active representation

Re-use Issue #212 as a hard gate: all retained clauses, reasons, indexes and certificates must have a universal polynomial bound in original input length, or the proposed calculus fails the bridge.

### C025-F — adversarial family suite

At minimum replay:

- theorem-matched directed `GT_n`;
- C024 resolution-sink padded `GT_n`;
- masked/lifted Tseitin;
- pigeonhole principle;
- random/near-threshold 3-SAT finite controls;
- synthetic padding attacks designed to manipulate pivot/order/frequency/index structures.

Finite PASS only validates mechanics; asymptotic promotion still requires theorem.

## 6. Current exact frontier

```text
C024_CONDITIONAL_BRIDGE_THEOREM        = PROVED
C024_POLICY0A_POLY_RESIDUAL_COUNT      = REFUTED
C024_ISSUE_212_STATE_SIZE              = OPEN

C025_FAIR_SCAN_ATTEMPT_BOUND           = PROVED_IN_CURRENT_STATE_SIZE
C025_FAIR_SCHEDULER_IMPLEMENTATION     = NEXT
C025_REASON_SOUNDNESS                  = OPEN
C025_REASON_EXTRACTION_COST            = OPEN
C025_DETERMINISTIC_PROOF_SEARCH        = OPEN
C025_POLY_ACTIVE_REPRESENTATION        = OPEN

P_VS_NP                                = OPEN
```

## 7. TOPA role

TOPA should now actively search for adversarial padding against every proposed C025 scheduler/retention/reason rule **before** it is promoted into Fundamentum. A failed design remains a useful receipt and becomes the next constraint.
