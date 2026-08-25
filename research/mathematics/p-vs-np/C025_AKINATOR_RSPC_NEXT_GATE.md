# C025 — Akinator RSPC next gate

Current fork after the bounded-cover theorem:

## Route BC1 — attack fixed-C

Try to extend the existing NW-local transfer from `C=1` to `C`-neighborhood-covered functions for arbitrary universal fixed `C`.

Target statement:

> For every fixed constant `C`, polynomial-size ER3 refutations restricted to macros with verified cover size at most `C` remain impossible on a suitable frozen NW hard family.

This statement is **OPEN**. Sokolov's published local-function theorem is a one-neighborhood statement; it must not be silently promoted to fixed unions of neighborhoods.

A successful BC1 transfer for every fixed `C` would imply that any polynomial escape requires cover count `c(N)->infinity`. Combined with the exact truth-table route, the visible no-oracle cost becomes `N^O(c(N))`.

It would still not prove that no different semantic-survival algorithm beats truth-table enumeration.

## Route BC2 — construct fixed-C progress

Search for a concrete fixed `C>1` with all of:

1. polynomial candidate enumeration;
2. exact deterministic survival discovery;
3. source-matched transfer validity;
4. universal next-step availability;
5. globally sound polynomially bounded progress potential;
6. polynomial state/trace/witness bytes in original `N`.

If all hold, the resulting selector is a true polynomial Akinator layer and gives the conditional bridge to `P=NP`.

## Priority

Run BC1 first because it is falsification-first: attempt to kill the entire fixed-C escape class before engineering BC2.

### First micro-gate BC1-A

Define `C-local` precisely as an explicit union of at most `C` frozen NW neighborhoods. Check whether the source functional-encoding substitution and restriction-stability lemmas remain valid under this enlarged locality notion.

Do not invoke the heavy-width lower bound until the source theorem's locality assumptions are re-proved for the enlarged encoding.

`BC1_A_C_LOCAL_SUBSTITUTION = NEXT`  
`BC1_B_RESTRICTION_STABILITY = OPEN`  
`BC1_C_HEAVY_WIDTH_TRANSFER = OPEN`  
`P_VS_NP = OPEN`
