# C025-E2R-L1G-F2 — Negative-edge budget to macro cut-elimination cost

**Status:** `PROVED_IN_STATED_SCOPE__PROVIDER_PASS`.

**Authoritative provider replay:** run `32753914462`, job `97516954725`, head `6dd18e95c663451b5bf9cff5abba691bb9b29156`, conclusion `SUCCESS`.

**Scope firewall:** this theorem converts a bounded polarity-inversion budget into a pure-Resolution simulation bound for frozen B2/ER3 on the stated NW hard-family transfer. It does **not** prove a superpolynomial lower bound on total extension count, does not resolve unrestricted ER/EF p-boundedness, and does not resolve P vs NP.

## Theorem chain

Let `q` be the total number of distinct negative crossing dependency edges and `S>=2` the explicit B2/ER3 proof volume.

F1 gives per-crossing-literal structural CNF expansion

```text
|CNFEXP(ell)| <= S^((q+2)!).
```

The authoritative replay does not materialize this astronomical bound; it compares logarithms. `BOUND != OBJECT_TO_MATERIALIZE`.

Because source lines are ER3, a safe per-line expansion ceiling is

```text
B_q = S^((q+3)!).
```

### Pure restriction/context lift

Resolution is closed under partial restrictions without proof-size increase: a restricted inference either remains a Resolution step or one restricted parent already subsumes the restricted resolvent.

For a context clause `C`, restrict by the assignment falsifying all literals of `C`, refute the restricted premises, and lift the proof back. This derives in pure Resolution a clause `C' subseteq C`. The provider replay includes an overlap fixture where the context shares a variable with the proof.

### Complement refutation

Using the F1 positive-closure normal form

```text
F = L AND (~F_1) AND ... AND (~F_k),
```

resolve away the local complement literals and eliminate frontier children one at a time with the pure context-lifting lemma. No disjointness of child cones is assumed.

With `H(q)=(q+2)!`, the recurrence

```text
R_q <= S^(H(q)+1) + q*S^H(q)*R_(q-1)
```

is safely dominated by

```text
R_q <= S^((q+4)!).
```

### Macro pivot and whole proof

Every ER3 macro pivot can therefore be expanded and simulated in local Resolution. Across the full proof,

```text
S_local <= S^((q+5)!).
```

After the already-audited NW-local literal substitution, the result is a Resolution proof of the functional encoding used by the established heavy-width lower bound.

## Quantitative consequence

For the existential polynomial-input NW-parity hard family there is a fixed `eta>0` such that sufficiently large members satisfy a local-functional Resolution lower bound

```text
L(N) >= exp(N^eta)
```

(after absorbing the fixed polylogarithmic source losses).

If a B2/ER3 escape had polynomial explicit size `S<=N^d`, then

```text
(N^d)^((q+5)!) >= exp(N^eta).
```

Hence

```text
(q+5)! * O(log N) >= N^eta,
```

and Stirling-scale growth `log(r!)=Theta(r log r)` yields

```text
q = Omega(log N / log log N).
```

Therefore every polynomial-size unrestricted B2/ER3 escape on this stated existential family needs a growing polarity-inversion DAG with at least `Omega(log N/log log N)` negative crossing edges.

## Provider replay gates

```text
F1_NEGATIVE_EDGE_ACCOUNTING                 = PASS
F1_FACTORIAL_EXPANSION_BOUND_FINITE         = PASS
F1_BOUND_MATERIALIZATION_AVOIDED             = PASS
F1_PARITY_NEGATIVE_EDGE_GROWTH              = PASS
F2_NESTED_COMPLEMENT_REFUTATION_FIXTURES    = PASS
F2_FACTORIAL_RECURRENCE_CEILING             = PASS
F2_PURE_RESTRICTION_CONTEXT_OVERLAP         = PASS
F2_PURE_CONTEXT_SUBCLAUSE_DERIVATION        = PASS
```

The earlier weakening-based route remains only a regression artifact; v1.1 promotion rests on pure `restrict -> refute -> lift`.

## Claim ceiling

```text
Q = Omega(log N/loglog N) != SUPERPOLYNOMIAL Q
Q LOWER BOUND != SUPERPOLYNOMIAL TOTAL EXTENSION COUNT
F2 != FULL ER/EF LOWER BOUND
SHORT PROOF EXISTENCE != DETERMINISTIC PROOF SEARCH
P_VS_NP = OPEN
```

Canonical provider receipt:

`data/TOPA-C025-E2R-L1G-F2-MACRO-CUT-PROVIDER-PASS-2026-08-24-v1.0.json`

## Next exact front

`C025-E2R-L1G-F3`: quantify **placement/depth of negative crossing edges under NW restrictions**. The aim is to distinguish many shallow/redundant inversions from a small number of strategically global inversions and to prove or refute a restriction-survival tradeoff.
