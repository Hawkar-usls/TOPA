# C025 — Akinator RSPC witness-frontier protocol

Status: **FROZEN NEXT-GATE PROTOCOL**  
Claim ceiling: **P_VS_NP = OPEN**

## Objective

Test whether the semantic-survival search barrier can be bypassed by a constructive proof-carrying macro language with a polynomial witness frontier and no backtracking.

## Frozen state object

Every represented Boolean function/macro `g` carries:

- exact B2-DAG definition;
- exact transitive root support `supp(g)`;
- a retained positive witness set `W1(g)`;
- a retained negative witness set `W0(g)`;
- provenance for how each witness was inherited or introduced;
- serialized byte count charged to original input length `N`.

No witness may be inserted by an unrestricted SAT/model-counting call.

## Frozen candidate language WF-1

Candidate NOT:

`e := NOT a`

with witness sets swapped.

Candidate AND:

`e := a AND b`

is admissible only when the current retained positive witness sets contain at least one compatible pair:

`alpha in W1(a), beta in W1(b)`

such that `alpha` and `beta` agree on `supp(a) intersect supp(b)`.

The parent positive witness is `alpha union beta`.

A negative witness may be inherited from either zero-child witness and canonically completed on roots outside that child's support.

## Deterministic selector rule WF-1-LEX

At each state:

1. enumerate all available ordered literal pairs `(a,b)` in canonical ID order;
2. for each pair, enumerate witness pairs `(alpha,beta)` in canonical serialized order;
3. accept the first pair whose positive witnesses are compatible;
4. if no admissible AND exists, try canonical NOT candidates not already represented;
5. if none exists, return `WF_STUCK`.

No heuristic score, model vote, semantic oracle, or backtracking is allowed.

## Complexity ledger

Let

- `V(S)` = number of available literals/macros in state `S`;
- `Omega(S)` = maximum retained witness count per value/function;
- `B_w(S)` = total serialized witness bytes;
- `J(S)` = total compatibility pairs checked in one selector step.

For the naive frozen selector:

`J(S) <= O(V(S)^2 * Omega(S)^2)`.

A polynomial-time claim in original input length requires fixed universal constants `c1,c2,c3` such that on every target run:

- `V(S) <= N^c1`,
- `Omega(S) <= N^c2`,
- `B_w(S) <= N^c3`,

plus polynomial bit complexity of compatibility and serialization.

`POLYNOMIAL_IN_V_OR_OMEGA != POLYNOMIAL_IN_ORIGINAL_N`.

## Required universal theorem

WF-1 is not promoted beyond a finite constructive language unless all of the following are proved:

1. **Availability:** every nonterminal target state has an admissible next candidate.
2. **No-backtracking completeness:** canonical first-choice witness retention never destroys future availability, or a polynomial repair mechanism is proved.
3. **Witness frontier bound:** `Omega(S)` and total witness bytes remain polynomial in original `N` with universal exponents.
4. **Source-matched survival:** retained witnesses certify the exact residual property required by the frozen Sokolov transfer/restriction model.
5. **Global progress:** every accepted step decreases a sound polynomially bounded potential leading to a correct SAT terminal state.

Failure modes must be classified separately:

- `WF_STUCK_BY_WITNESS_CONFLICT`
- `WF_FRONTIER_SUPERPOLY`
- `WF_JOIN_SUPERPOLY`
- `WF_SOURCE_SURVIVAL_FAIL`
- `WF_GLOBAL_PROGRESS_FAIL`

## Immediate adversarial target

Construct the smallest family in which:

- every macro has a short positive witness;
- pairwise witness compatibility is locally easy;
- a globally successful composition exists;
- WF-1-LEX gets stuck unless multiple alternative witnesses are retained.

Then measure the minimum witness frontier required to avoid the trap.

The first finite two-function trap is already known:

`a=x OR y`, `b=x OR NOT y`.

The next goal is an `r`-stage family where canonical witness retention forces frontier growth with `r`. No asymptotic lower bound is assumed in advance.

## Claim ceiling

`WF1_LOCAL_ACCEPTED_STEP_DISCOVERY = POLYNOMIAL_IN_EXPLICIT_STATE_AND_RETAINED_FRONTIER`  
`WF1_UNIVERSAL_AVAILABILITY = OPEN`  
`WF1_POLYNOMIAL_FRONTIER_IN_ORIGINAL_N = OPEN`  
`WF1_SOURCE_MATCHED_SURVIVAL = OPEN`  
`WF1_GLOBAL_PROGRESS = OPEN`  
`POLYNOMIAL_AKINATOR = OPEN`  
`P_VS_NP = OPEN`
