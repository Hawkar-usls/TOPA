# C025-E2R-L1E — NW-neighborhood-local ER3 extension-count lower bound

**Status:** `RESTRICTED_EXISTENTIAL_SUPERPOLY_EXTENSION_COUNT_PROVED_FROM_SOURCE_THEOREM`; deterministic explicit family remains `OPEN`.

**Scope firewall:** this theorem concerns a deliberately restricted proof system in which every B2 extension stays inside one fixed Nisan-Wigderson neighborhood. It is **not** a lower bound for unrestricted ER3 / Extended Resolution / Extended Frege and does not resolve Issue #217 globally.

## 1. Source theorem used

Sokolov (CCC 2022), building on the functional Nisan-Wigderson encoding, proves the following asymptotic lower-bound regime.

For sufficiently large `n`, fix a constant `delta` with `0<delta<1`, let

```text
m = n^(2-delta)
Delta = log^(2-delta) n,
```

choose an appropriate random left-Delta-regular NW dependency graph `G`, and take balanced base functions. With high probability over `G`, for any `b` outside the image of the generator, every Resolution refutation of the **full functional encoding** has size

```text
L_n = exp(n^Omega(delta)).
```

Parity is an admissible base function for the balancedness condition: parity on `Delta` variables is `(1/2, Delta-1)`-balanced, stronger than the theorem's required balance in the stated asymptotic regime.

The proof below uses this theorem as an external provider theorem; it does not re-prove heavy width.

## 2. Direct root-only CNF family

Let every NW output function be parity on its `Delta` neighbours.

Because `m>n`, the map

```text
F_G : {0,1}^n -> {0,1}^m
```

cannot be surjective. Choose any `b_n` outside its image.

Define `DIRPARITY(G,b_n)` over the original right-side variables `x_1,...,x_n` only. For each output `i`, include one width-`Delta` clause for every assignment

```text
a in {0,1}^Delta
```

whose parity is not `b_i`; the clause simply forbids that assignment on `Vars_i=N(v_i)`.

Each output contributes exactly

```text
2^(Delta-1)
```

clauses. Therefore, under a standard explicit signed-literal-list encoding,

```text
N_n = O(m * 2^Delta * Delta * log n).
```

The formula is UNSAT exactly because `b_n` is outside the image of the NW generator.

## 3. Real input-length map

For

```text
m = n^(2-delta)
Delta = log^(2-delta) n,
```

we have

```text
log N_n = O(log^(2-delta) n).
```

Thus for every fixed constant `c`,

```text
log(N_n^c) = O(c * log^(2-delta) n)
           = o(n^alpha)
```

for every fixed `alpha>0`.

Since the source lower bound is

```text
L_n = exp(n^Omega(delta)),
```

it follows that

```text
L_n / N_n^c -> infinity
```

for every fixed `c`.

So the heavy-width lower bound is superpolynomial in the **actual encoded length of the direct root CNF**, even though the truth-table encoding of each parity constraint is itself superpolynomial in `Delta`.

## 4. Frozen NW-neighborhood-local B2/ER3 restriction

For each extension variable `e`, compute transitive support in the original root variables.

A B2 definition

```text
e <-> (a AND b)
```

is admitted only when there exists a single NW output neighborhood `Vars_i` such that

```text
support(e) = support(a) union support(b) subseteq Vars_i.
```

Equivalently, the complete dependency cone of the extension lies inside one NW neighborhood.

For the ER3 subregime, every Resolution-derived non-axiom clause has width at most 3. Root clauses of `DIRPARITY` may have width `Delta`; extension axioms have width at most 3.

## 5. Functional semantics of every B2 variable

Recursively associate a Boolean function with every proof variable:

```text
g_(x_j)(x) = x_j

g_e(x) = value(a) AND value(b)
```

where literal polarity is interpreted semantically.

By the NW-local admission rule, every `g_e` depends only on one `Vars_i`, hence it is a local function in the sense of the functional encoding.

Semantic duplicates are allowed: two syntactically different B2 variables may compute the same Boolean function.

## 6. Variable substitution into the full functional encoding

Let `Phi_full(G,f,b)` be the full functional encoding containing variables `y_g` for all local Boolean functions and all source semantic consequence clauses.

Define the literal substitution

```text
mu(x_j) = y_(projection x_j)
mu(e)   = y_(g_e).
```

This substitution need not be injective.

Ordinary Resolution is polynomially closed under literal substitutions, so a B2/Resolution refutation can be transformed with polynomial overhead after applying `mu`; tautological substituted clauses may be discarded in the standard way.

## 7. Root-axiom inclusion lemma

Take a clause `C` of `DIRPARITY` belonging to output `i`.

- all variables/literals of `mu(C)` are projection functions supported inside `Vars_i`;
- by construction `C` forbids one assignment that violates `f_i(x)=b_i`;
- therefore every assignment satisfying `f_i(x)=b_i` satisfies at least one literal of `mu(C)`.

This is exactly the semantic-clause admission condition in the functional encoding.

Hence every non-tautological substituted direct root clause is an axiom of `Phi_full`.

## 8. Extension-axiom inclusion lemma

Consider a legal NW-local B2 definition

```text
e <-> (a AND b).
```

Its three CNF clauses are Boolean identities relating the local functions `g_e`, `g_a`, `g_b`, with literal polarities included.

Because the complete support union lies inside one `Vars_i`, every such clause is a semantic consequence valid for every assignment to that neighborhood, hence in particular for every assignment satisfying `f_i(x)=b_i`.

Therefore every non-tautological substituted B2 extension axiom is an axiom of the full functional encoding.

This argument uses the **general semantic-clause definition**, not merely the special positive-literal conjunction example printed in the source.

## 9. Proof-transfer theorem

Let `pi` be any NW-neighborhood-local B2 refutation of `DIRPARITY(G,b_n)`.

Treat the legal extension clauses introduced by `pi` as extension axioms and apply substitution `mu` to all proof lines.

By polynomial closure of Resolution under literal substitutions, obtain a Resolution refutation `mu(pi)` with polynomial overhead whose initial clauses are substituted root clauses or substituted extension axioms.

By Sections 7 and 8, every non-tautological initial clause of `mu(pi)` belongs to `Phi_full(G,f,b_n)`.

Hence `mu(pi)` is a valid Resolution refutation of the full functional encoding.

The Sokolov lower bound therefore implies

```text
size(pi) >= exp(n^Omega(delta))
```

up to a fixed polynomial-root loss if one uses only the general p-closure statement rather than a linear substitution implementation. Either form remains `exp(n^Omega(delta))` after changing the hidden constant.

Combining with Section 3:

```text
size(pi) is superpolynomial in N_n.
```

### Theorem L1E.1

There exists an infinite family of polynomially described UNSAT direct NW-parity CNFs (with explicit encoded length `N_n` as above) for which every NW-neighborhood-local B2 refutation has superpolynomial size in `N_n`.

The graph family is obtained by the high-probability existence statement in the source theorem; deterministic explicit graph selection is not established here.

## 10. From proof length to extension count in ER3

Now additionally require the proof to be ER3.

Let `K` be its number of extension variables and let `V=n+K`.

The already-proved ER3 clause-universe / duplicate-elimination lemma gives a refutation with the same extension definitions and at most

```text
O(N_n + K + V^3)
```

proof nodes/axioms, up to ordinary encoding factors.

Suppose, for contradiction, that there is a fixed `c` such that infinitely many formulas in the family have an NW-local ER3 refutation with

```text
K <= N_n^c.
```

Then

```text
O(N_n + K + (n+K)^3)
```

is polynomial in `N_n` (and `n <= N_n`). This contradicts Theorem L1E.1.

### Theorem L1E.2 — restricted extension-count lower bound

For the family above, for every fixed `c`, all sufficiently large members satisfy:

```text
EVERY NW-neighborhood-local ER3 refutation has K > N_n^c.
```

Equivalently, the required extension count is superpolynomial in the actual input length.

This is the first genuine extension-count lower bound produced by the C025-E2R route — **inside the frozen NW-neighborhood-local restriction only**.

## 11. Why this does not solve global Issue #217

Unrestricted ER3 may introduce an extension whose transitive support crosses many NW neighborhoods. The heavy-width source theorem does not permit such a variable inside the functional encoding.

Therefore the escape hatch is exact and visible:

```text
NW_LOCAL K = SUPERPOLYNOMIAL
        does not imply
FULL_ER3 K = SUPERPOLYNOMIAL.
```

The next question is no longer whether locality yields a lower bound — it does. The next question is how much **cross-neighborhood mixing** is required to escape it.

## 12. Remaining gates

```text
L1E_SOURCE_HEAVY_WIDTH_THEOREM                    = EXTERNAL_THEOREM
L1E_DIRECT_PARITY_INPUT_LENGTH_MAP                 = PROVED
L1E_ROOT_AXIOM_INCLUSION                           = PROVED
L1E_EXTENSION_AXIOM_INCLUSION                      = PROVED
L1E_RESOLUTION_SUBSTITUTION_TRANSFER               = PROVED_USING_STANDARD_P_CLOSURE
L1E_NW_LOCAL_B2_PROOF_SIZE_LOWER_BOUND             = PROVED_FROM_SOURCE_THEOREM
L1E_NW_LOCAL_ER3_SUPERPOLY_EXTENSION_COUNT         = PROVED_FROM_SOURCE_THEOREM
L1E_DETERMINISTIC_EXPLICIT_HARD_GRAPH_FAMILY       = OPEN
L1F_CROSS_NEIGHBORHOOD_MIXING_ESCAPE_MEASURE       = NEXT
GLOBAL_ISSUE_217                                   = OPEN
P_VS_NP                                            = OPEN
```

## 13. New hard boundary

```text
LOCALITY_LOWER_BOUND_PROVED != FULL_ER_LOWER_BOUND
THE_ESCAPE_RESOURCE_IS_NOW_CROSS_NEIGHBORHOOD_MIXING
```
