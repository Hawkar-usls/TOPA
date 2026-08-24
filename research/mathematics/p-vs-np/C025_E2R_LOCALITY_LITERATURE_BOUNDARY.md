# C025-E2R-L1 — Literature transfer boundary

Relevant external results are **templates, not transferred theorems** for B2/ER3.

- Sokolov (CCC 2022) develops heavy-width lower bounds for Resolution on functional Nisan-Wigderson encodings containing local extension variables.
- Impagliazzo–Mouli–Pitassi (CCC 2023) and follow-up work prove lower bounds for Polynomial Calculus with locality/arity-restricted extension variables.
- Guarded-extension separations concern weaker systems and cannot be promoted to unrestricted ER lower bounds.

Before importing any result into `ER3[kappa-local]`, TOPA requires:

```text
SOURCE_FORMULA_OBJECT_IDENTITY_OR_EXPLICIT_REDUCTION
SOURCE_EXTENSION_SEMANTICS_MATCH_OR_SIMULATION
SOURCE_PROOF_RULE_SIMULATION
SOURCE_LOCALITY_PARAMETER_MAP
SOURCE_SIZE_PARAMETER_MAP
RESTRICTION_STABILITY
```

Until those are established, status is `INSPIRATION_ONLY`.

The immediate research task is to test whether a heavy-width-style measure can be defined directly for the frozen transitive-support-local B2 grammar and remain stable under Resolution and partial assignments.
