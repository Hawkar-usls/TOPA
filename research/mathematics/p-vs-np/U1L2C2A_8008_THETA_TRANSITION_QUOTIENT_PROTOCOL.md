# U1-L2C2A — 8008 transition-state + Ramanujan-theta exact donor audit

Status: **FROZEN_PROTOCOL_BEFORE_PROVIDER**
Claim ceiling: **P_VS_NP = OPEN**

## Purpose

Attack the active nonliteral-factor projection debt without heuristics.

Two donors are admitted only in exact form:

1. **Intel-8008 transition-state principle** — a state representation may be chosen for cheap exact transitions rather than human/numeric presentation order.
2. **Ramanujan general theta exact algebra donor** — exact sum/product identities and exact recurrences may justify a representation switch when a proof-carrying morphism exists.

Neither donor is admitted as evidence for P=NP by itself.

## A. 8008 anti-fake-compression theorem gate

For a finite transition system with `S` semantically distinct states, any bijective relabeling/permutation of those states preserves `S` exactly. A de-Bruijn-like/nonlinear state ordering may simplify transition realization, but it does not reduce the information-theoretic state count.

The frozen 3-bit cycle checked here is:

`000 -> 001 -> 010 -> 101 -> 011 -> 111 -> 110 -> 100 -> 000`.

Required assertions:

- all eight 3-bit words appear exactly once;
- transition map is deterministic and cyclic;
- source semantic-state count = target semantic-state count = 8;
- minimum fixed-width state label remains `ceil(log2 8)=3` bits;
- therefore **RELABELLING_ONLY_IS_NOT_ASYMPTOTIC_COMPRESSION**.

This is a guardrail for JANUS: future transition encodings must reduce/quotient the semantic state space or macro-represent it, not merely rename it.

## B. Ramanujan theta exact donor

Use the exact specialization of the general theta function

`f(a,b) = sum_{n in Z} a^{n(n+1)/2} b^{n(n-1)/2}`

at `a=q`, `b=q^2`:

`Theta(q) = sum_{n in Z} q^{n(3n-1)/2}`

with product side

`(-q;q^3)_inf (-q^2;q^3)_inf (q^3;q^3)_inf`.

Frozen finite audit degree: `D=128`.

Provider must independently construct coefficient vectors through:

1. the bilateral sum exponents `E(n)=n(3n-1)/2` for all `E(n)<=D`;
2. the truncated exact product, including every factor whose smallest exponent is `<=D`, with integer polynomial arithmetic truncated only above degree `D`.

Required equality: every coefficient `0..D` must agree exactly.

No floating point, sampling, numerical tolerance, CAS oracle or web lookup is allowed in the provider.

## C. 8008 + theta recurrence state

For the same exact theta specialization define

`E(n)=n(3n-1)/2`.

Frozen exact transitions:

- forward: `(n,E) -> (n+1, E + 3n + 1)`;
- backward: `(n,E) -> (n-1, E - 3n + 2)`.

Provider must replay both transitions on every integer `n` whose source and target exponents lie within the audited finite window.

This demonstrates an exact low-dimensional **transition representation** for this theta family: the next spectral exponent is generated from the current transition state instead of materializing the whole series.

It does **not** establish a SAT encoding.

## D. SAT-side admission contract

A theta/transition macro may enter the P=NP proof path for a nonliteral Boolean factor `g(x,Y)` only after all of the following are proved:

1. `PHI`: deterministic polynomial-time construction of a macro-state `phi(g)` from the explicit proof-carrying factor;
2. `EXACT`: semantic interpretation of `phi(g)` is exactly `g` (or exactly the projection-relevant relation required by the proof);
3. `UPDATE`: `exists x g` is computed directly on the macro-state without decompression;
4. `CLOSURE`: the updated state remains in the admitted language;
5. `SIZE`: state + certificate bytes are polynomial in original source size;
6. `WORK`: construction + failed discovery + update + verify + witness are globally polynomial;
7. `WITNESS`: satisfying assignments lift in polynomial time.

Until then:

`ARBITRARY_B2_TO_THETA_MORPHISM = OPEN`.

## E. Frozen output interpretation

Allowed positive result:

- exact 8008-style transition encoding is useful as a design rule;
- relabeling alone provably does not shrink semantic-state cardinality;
- theta sum/product and recurrence are exact representation/transition donors;
- SAT-side morphism remains open.

Forbidden inference:

- theta identity implies SAT in P;
- de-Bruijn/nonlinear state numbering reduces arbitrary Boolean cofactor diversity;
- finite coefficient agreement proves a new theta theorem;
- donor success implies P=NP.

## Next gate

If this audit passes, the active proof obligation becomes:

`U1-L2C2B_PROOF_CARRYING_NONLITERAL_TRANSITION_MACRO_MORPHISM`

The target is not a prettier encoding. It is an exact polynomial-size quotient/macro of a real nonliteral SAT factor that supports the next existential update and remains closed.
