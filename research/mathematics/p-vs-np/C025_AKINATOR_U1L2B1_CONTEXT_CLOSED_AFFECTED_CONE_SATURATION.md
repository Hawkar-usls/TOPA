# C025 — Akinator U1-L2B1: context-closed affected-cone monotonicity and polynomial local saturation

Status: **GLOBAL_MONOTONICITY_FOR_CLOSED_LOCAL_REWRITES_PROVED / UNIVERSAL_USEFULNESS_OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

U1-L2B0 exhaustively synthesized the complete frozen `k=4, g<=3` local B2 identity catalog and found exact replacements that reduce the syntactic cone affected by a future projection even when gate count is unchanged.

A local cost drop is not enough by itself: a replacement could be unsafe if internal nodes are shared with the surrounding DAG, or could in principle move dependency into the context.

This note isolates a structural condition under which a local exact replacement provably yields a **global** monotone decrease, and then derives a polynomial bound on deterministic saturation by the fixed catalog.

This is a theorem about the admitted local rewrite system. It does **not** prove that every circuit has an applicable rewrite or that saturation yields polynomial existential-projection state.

---

## 1. Explicit DAG and syntactic dependency

Let `C` be a finite acyclic B2 DAG over root variables and signed-input AND gates.

Fix one remaining root variable `x` that is intended for a future existential projection.

For every signal/gate define the frozen syntactic dependency bit recursively:

```text
dep_x(x)       = TRUE
dep_x(y)       = FALSE for every other root y
dep_x(NOT s)   = dep_x(s)
dep_x(a AND b) = dep_x(a) OR dep_x(b).
```

Define

```text
AC_x(C) := number of internal gates v of C with dep_x(v)=TRUE
G(C)    := total number of internal gates of C.
```

No semantic-equivalence query is needed to compute either quantity; both follow from one topological traversal of the explicit DAG.

---

## 2. Context-closed rewrite region

A local region `H` of `C` is **context-closed single-output** when all of the following hold:

1. `H` contains a finite set `I_H` of internal gates and one designated output signal `o_H` computed by `H`;
2. every input edge entering a gate in `I_H` from outside `I_H` is recorded as one of the ordered boundary signals `B_H`;
3. every gate in `I_H` is reachable from `o_H` when traversing internal edges backward;
4. no gate of `I_H` other than the designated output gate has any user outside `I_H`;
5. the surrounding DAG accesses the region only through `o_H` (possibly with sign at the consumer edge);
6. replacing `H` does not duplicate or mutate any boundary signal or any outside gate.

Condition 4 is the critical sharing firewall. A sub-DAG with externally shared internal nodes is not eligible for this theorem unless it is first represented as a separately accounted closed region.

---

## 3. Admitted exact replacement

Let `H'` be another B2 region over the same ordered boundary signals `B_H`, with a single output `o_H'`.

The replacement `H -> H'` is admitted for projected root `x` only if:

### Semantic identity

For every Boolean valuation of the boundary signals,

```text
o_H(B_H) = o_H'(B_H).
```

For the frozen U1-L2B0 catalog this is certified by equality of the complete 16-row formal truth table.

### Nonincrease conditions

```text
G(H')    <= G(H)
AC_x(H') <= AC_x(H).
```

### Strict progress

At least one is strict:

```text
AC_x(H') < AC_x(H)
OR
G(H')    < G(H).
```

Because the U1-L2B0 canonical representative minimizes `(AC_x, G, encoding)` inside an exact truth-table class, its admitted replacements satisfy these local inequalities.

---

## 4. Lemma B1.1 — output dependency cannot increase

For a reachable single-output region,

```text
dep_x(o_H)=FALSE  =>  AC_x(H)=0.
```

Reason: if any reachable internal gate depended syntactically on `x`, every directed path from that gate to the output propagates the dependency bit by OR, so the output would also depend on `x`.

Therefore, from

```text
AC_x(H') <= AC_x(H)
```

we get

```text
dep_x(o_H') <= dep_x(o_H)
```

under Boolean ordering `FALSE < TRUE`.

So an admitted replacement can preserve the region-output dependency or remove it, but cannot introduce a new syntactic dependency at the region interface.

---

## 5. Theorem B1.2 — context-closed global affected-cone monotonicity

Let `C'` be obtained from `C` by one admitted context-closed replacement `H -> H'`.

Then

```text
AC_x(C') <= AC_x(C)
G(C')    <= G(C).
```

Moreover, if the local replacement strictly decreases `AC_x` or `G`, then the global lexicographic potential

```text
Phi_x(C) := (AC_x(C), G(C))
```

strictly decreases:

```text
Phi_x(C') <lex Phi_x(C).
```

### Proof

Partition the gates of `C` into:

1. gates strictly upstream/outside the region;
2. region gates `I_H`;
3. outside descendants/users of the region output.

**Upstream/outside gates.** Their inputs and definitions are unchanged, so their dependency bits are unchanged.

**Region gates.** By admission,

```text
AC_x(H') <= AC_x(H)
```

and

```text
G(H') <= G(H).
```

**Outside descendants.** Because the region is context-closed, no outside node observes an internal gate of `H`; the context observes only the designated output. By Lemma B1.1 the replacement output dependency bit is either unchanged or changes from TRUE to FALSE. Dependency in every outside AND gate is the OR of its input dependency bits. Replacing one input bit by an equal or smaller bit cannot make any descendant dependency change from FALSE to TRUE. Thus outside `AC_x` cannot increase.

Combining the three parts gives

```text
AC_x(C') <= AC_x(C).
```

Gate count outside the region is unchanged and the target has no more internal gates than the source, so

```text
G(C') <= G(C).
```

If local `AC_x` strictly decreases, no outside term can increase, hence global `AC_x` strictly decreases. If local `AC_x` is unchanged but local gate count strictly decreases, global `AC_x` is nonincreasing and global gate count strictly decreases. In either case the lexicographic pair strictly decreases.

QED.

---

## 6. Corollary B1.3 — polynomial number of saturation rewrites

Let the initial DAG have `S_0 = G(C_0)` internal gates.

Run a deterministic saturator that repeatedly applies any admitted context-closed U1-L2B0 replacement and never performs another operation between these rewrites.

From Theorem B1.2 both coordinates of `Phi_x` are nonincreasing nonnegative integers and every accepted rewrite decreases at least one coordinate by at least one.

Initially

```text
0 <= AC_x(C_0) <= S_0
0 <= G(C_0)    =  S_0.
```

Therefore the total number of accepted rewrites is at most

```text
AC_x(C_0) + G(C_0) <= 2 S_0.
```

Thus fixed-catalog saturation cannot take an exponential number of accepted rewrite steps.

---

## 7. Corollary B1.4 — polynomial discovery work for the frozen local kernel

The U1-L2B0 scope has constant

```text
g <= 3
k <= 4.
```

At a DAG state of size at most `S_0`, a brute deterministic structural scan of all candidate internal regions of at most `g` gates is bounded by a fixed polynomial in `S_0`; closure, boundary arity, canonical encoding, and catalog membership are polynomial-time checks, while the catalog itself is a fixed immutable constant-size object with respect to source input length.

Even under a conservative strategy that rescans the entire DAG after every accepted rewrite, there are at most `2S_0` accepted rewrites by Corollary B1.3.

Hence the complete saturation procedure for one fixed projected root `x` has polynomial total discovery and rewrite work in the explicit input DAG size.

A simple conservative implementation may bound the scan by `S_0^{O(g)} * O(S_0)`; with frozen `g=3` this is polynomial.

This result pays for failed local matches as part of the repeated complete scans.

---

## 8. Certificate structure

One accepted rewrite can carry a replayable certificate containing:

1. immutable U1-L2B0 catalog SHA;
2. source region gate IDs and ordered boundary IDs;
3. structural proof that the source region is context-closed;
4. source canonical local encoding;
5. target catalog encoding;
6. formal truth-table identity key;
7. source/target `(AC_x, G)` local costs;
8. before/after Hephaestus state hashes.

A verifier recomputes closure, local encoding, catalog identity, and the global potential change from the explicit DAG. No unrestricted semantic equivalence solver is required.

---

## 9. What is now proved

```text
FIXED_K4_G3_EXACT_LOCAL_IDENTITY_CATALOG              = AVAILABLE
PROJECTION_SPECIFIC_SAME_SIZE_IDENTITIES_EXIST        = PROVED_BY_EXHAUSTIVE_CATALOG
CONTEXT_CLOSED_LOCAL_AC_DROP_IMPLIES_GLOBAL_AC_NOINCREASE = PROVED
CONTEXT_CLOSED_STRICT_LOCAL_PROGRESS_IMPLIES_GLOBAL_PHI_DESCENT = PROVED
MAX_ACCEPTED_LOCAL_SATURATION_STEPS                    <= 2*INITIAL_GATE_COUNT
FIXED_CATALOG_LOCAL_SATURATION_DISCOVERY_WORK          = POLYNOMIAL
```

These statements are independent of benchmark success.

---

## 10. The remaining universal gap

This theorem proves that the local exact kernel is **safe and polynomial to saturate**. It does not prove that the normal form is good enough for existential projection.

A saturated circuit can still have

```text
AC_x(C_sat) = Theta(G(C_sat))
```

and can still generate a large restricted-descendant frontier under repeated projection.

Therefore the next universal obligation is not termination. It is **coverage/progress completeness**:

> before the projection frontier becomes superpolynomial, does every admissible nonterminal state either contain a context-closed exact contraction from a fixed/poly-discoverable proof-carrying grammar, enter a known tractable exact representation, or expose another globally polynomial decreasing rank?

No theorem currently proves this.

---

## 11. Next exact gate

`U1-L2B2 LOCAL-NORMAL-FORM ESCAPE / COMPLETENESS GATE`

Construct adversarial prebirth-projection DAGs and determine whether the frozen exact local kernel reaches a normal form while `AC_x` remains large.

- If such a family exists, preserve it as a falsification receipt for **this local grammar**, not as a P!=NP result.
- If the grammar always contracts a broad family, extract and prove the structural reason before extending the grammar.

Do not enlarge `k` or `g` merely because an escape is observed; first characterize the escape.

```text
P_VS_NP = OPEN
```
