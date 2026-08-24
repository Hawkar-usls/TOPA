# C025-E2R-L1C — Nisan-Wigderson locality transfer audit

**Status:** `CURRENT_KAPPA_LOCAL_TRANSFER_REFUTED_BY_PARAMETER_MISMATCH`; `NW_NEIGHBORHOOD_LOCAL_EXTENSION_AXIOM_MAP_PROVED_CONDITIONALLY`; full proof transfer `OPEN`.

## 1. Source locality is graph locality, not cardinality locality

In Sokolov's functional encoding of the Nisan-Wigderson generator, a Boolean function `g` is **local** iff there exists an output vertex `v_i` such that `g` depends only on

```text
Vars_i = N(v_i).
```

The encoding introduces a variable `y_g` for each selected local function `g`.

This is materially different from our first restriction

```text
|support(e)| <= kappa.
```

A support can have cardinality at most `kappa` while mixing root variables from several different NW neighborhoods.

### Counterexample

Let

```text
Vars_1={x1,x2}
Vars_2={x3,x4}
kappa=2.
```

An extension depending on `{x1,x3}` is `kappa`-local by cardinality, but is not local in the NW sense because its support is contained in neither `Vars_1` nor `Vars_2`.

Therefore the Sokolov heavy-width theorem does **not** directly apply to `ER3[kappa-local]`.

## 2. Refined restriction: NW-neighborhood-local

Given a fixed NW dependency graph with neighborhoods `Vars_1,...,Vars_m`, call an extension `NW-local` iff

```text
support(e) subseteq Vars_i
```

for at least one `i`.

This restriction implies `|support(e)|<=Delta` when the graph is left-regular of degree `Delta`, but the converse is false.

## 3. Extension-axiom map

Suppose a B2 extension

```text
e <-> (a AND b)
```

is NW-local inside `Vars_i` and the literals `a,b` denote local Boolean functions `g,h` on `Vars_i`.

Then `e` denotes the local function

```text
s = g AND h
```

on the same neighborhood.

Sokolov's functional encoding explicitly contains, for local `s,g,h` with `s=g AND h`, the clauses

```text
(~y_s OR y_g)
(~y_s OR y_h)
(y_s OR ~y_g OR ~y_h).
```

These are exactly the B2 definitional clauses under the literal/function map

```text
e -> y_s
a -> y_g
b -> y_h
```

with polarity handled by literal negation.

### Conditional simulation lemma

If the functional encoding's chosen collection `G` contains every local function computed by the B2 extensions under consideration, then every **B2 extension axiom** of an NW-neighborhood-local proof maps to clauses already present in the functional encoding.

This establishes extension-axiom compatibility only.

## 4. What is still missing for a full theorem transfer

A heavy-width lower bound cannot yet be imported. We still need to prove all of:

1. **root formula map** — the exact CNF refuted by B2 must map to / be contained in the functional encoding with polynomial parameter distortion;
2. **proof literal map** — every root and extension literal used by B2 must have a corresponding `y_g` representation;
3. **collection-size accounting** — the required local-function collection `G` must be represented without hiding superpolynomial input/certificate size;
4. **Resolution preservation** — every B2 Resolution step must map to a legal Resolution step after literal/function substitution;
5. **restriction correspondence** — B2 root restrictions must correspond to the source's normal assignments/restrictions;
6. **ER3 width accounting** — the width-3 normalization must survive the translation or be charged explicitly.

Until these are proved, the literature result remains `INSPIRATION_ONLY` for Issue #217/#218.

## 5. Important source mismatch: semantic functional encoding

The functional encoding is not merely a root CNF plus binary extension definitions. It may contain clauses expressing arbitrary semantic consequences among selected local functions under an output constraint. This can make the source formula strictly richer than a plain B2 extension-axiom set.

Therefore object identity must not be assumed from the presence of matching `s=g AND h` clauses.

## 6. Updated gates

```text
L1-A transitive support mechanics                  = PROVIDER_PASS
L1-B root-restriction locality stability           = PROVED / REPLAY_PENDING
L1-C1 kappa-local -> NW-local direct transfer       = REFUTED
L1-C2 NW-local extension-axiom compatibility        = PROVED_CONDITIONAL_ON_G
L1-C3 full functional-encoding proof transfer       = OPEN
L1-D heavy-width transfer                           = BLOCKED_BY_L1-C3
L1-E restricted counterfamily                       = OPEN
```

## 7. Claim ceiling

```text
NW_LOCAL_EXTENSION_AXIOM_MATCH != HEAVY_WIDTH_THEOREM_TRANSFER
ER3[NW-local] LOWER BOUND != FULL ER3 LOWER BOUND
```
