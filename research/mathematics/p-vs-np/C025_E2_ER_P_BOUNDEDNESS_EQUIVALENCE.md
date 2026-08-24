# C025-E2 — B2 / Extended-Resolution p-boundedness equivalence

**Status:** `EQUIVALENCE_PROVED_FOR_CNF_REFUTATIONS`; global polynomial-size question remains `OPEN_MAJOR_EXTERNAL_FRONTIER`.

**Claim ceiling:** this note does not prove a polynomial upper bound or a superpolynomial lower bound for Extended Resolution / Extended Frege. It identifies the exact external proof-complexity problem reached by the frozen B2 language.

## 1. Frozen B2 refutation language

For an UNSAT root CNF `F0`, B2 permits:

1. root clauses as axioms;
2. fresh extension definitions

```text
EXTEND(e,a,b):  e <-> (a AND b)
```

with exact clauses

```text
(~e OR a)
(~e OR b)
(e OR ~a OR ~b)
```

where `a,b` are literals over root variables or earlier extension variables;
3. exact Resolution steps;
4. a final advertised clause over root variables only.

For a root refutation, the advertised clause is the empty clause `[]`, so the original-variable export restriction is vacuous.

## 2. Standard Extended Resolution -> B2

Use the standard literal-AND presentation of Extended Resolution: introduce a fresh variable `e` abbreviating `a AND b`, where `a,b` are literals already available, add the three exact definitional clauses, then continue with Resolution.

This is exactly the B2 extension rule.

The additional B2 normalization conditions do not change proof power polynomially:

- rename extension variables by introduction order to strictly increasing fresh integer ids above all root variables;
- because operands may mention only already available literals, the renamed definitions remain topologically ordered;
- delete proof nodes not reachable from the empty clause;
- delete extension definitions outside the transitive definition closure of reachable extension axioms and remap indices.

All operations are polynomial-time and do not increase proof size by more than a polynomial factor (indeed the direct AND-form translation is linear up to encoding/renaming overhead).

### OR-form presentations

If an ER source is presented with

```text
z <-> (l1 OR l2),
```

introduce in B2

```text
e <-> ((~l1) AND (~l2))
```

and represent source literal `z` by B2 literal `~e`, and source literal `~z` by `e` throughout the remaining derivation. This is De Morgan plus a polarity renaming. Resolution on pivot `z` becomes Resolution on pivot `e`; proof size changes only linearly.

Therefore common AND- and OR-literal presentations of ER normalize into B2 with polynomial overhead.

## 3. B2 -> Standard Extended Resolution

Every B2 extension definition is an ordinary Extended-Resolution extension step, and every B2 proof inference is ordinary Resolution. Dropping B2's serialization/portability metadata therefore gives an ER refutation directly.

Thus B2 is polynomially simulated by ER.

## 4. Equivalence theorem

For UNSAT CNF refutations:

```text
B2  <=p  ER
ER  <=p  B2
```

so

```text
B2 ~=p ER.
```

The frozen B2 language is therefore not merely inspired by Extended Resolution; at the refutation level it is a normalized portable presentation of the same proof-complexity strength.

## 5. Consequence for E2

Define E2 as:

> Does there exist a fixed polynomial `p` such that every UNSAT CNF `F` of encoded length `N` has a verifier-accepted B2 refutation of encoded size at most `p(N)`?

By the p-equivalence above:

```text
E2_POSITIVE  <=>  ER_IS_P_BOUNDED_ON_CNF_REFUTATIONS
```

up to the standard polynomial encoding translations.

Extended Resolution is polynomially equivalent to Extended Frege, so E2 lands on the classical strong-proof-system frontier rather than a local JANUS-specific lemma.

## 6. Complexity consequences

### If E2 is positive

B2 verification is polynomial in certificate size. If every UNSAT CNF has a polynomial-size B2 certificate, then `UNSAT in NP`. Since UNSAT is coNP-complete,

```text
NP = coNP.
```

This is already a major complexity consequence. It does **not** by itself give `P=NP`; deterministic polynomial certificate discovery is a separate C025-C2 gate.

### If E2 is negative

A superpolynomial lower bound for B2 yields a superpolynomial lower bound for Extended Resolution / Extended Frege up to p-equivalence. Such a result would be a major proof-complexity breakthrough.

Importantly, `ER is not p-bounded` is not currently known by itself to imply `NP != coNP`, because ER is not known to be an optimal propositional proof system.

## 7. Literature boundary

Primary/standard facts used for frontier identification:

- standard Extended Resolution adds fresh variables for binary functions of earlier literals and Resolution;
- Extended Resolution and Extended Frege polynomially simulate one another;
- proving strong lower bounds for Extended Frege / Extended Resolution remains a major open problem.

Representative sources checked in this pass include Sam Buss's Proof Complexity I slides, the Beame–Pitassi proof-complexity survey, and Jan Krajicek's recent chapter on ER.

## 8. New split

The old single label `C025-E2` is now split:

```text
C025_E2A_B2_ER_P_EQUIVALENCE             = PROVED
C025_E2B_GLOBAL_ER_P_BOUNDEDNESS         = OPEN_MAJOR_EXTERNAL_FRONTIER
C025_E2R_POLICY0B_RESTRICTED_PROOF_SIZE   = NEXT_TRACTABLE_ATTACK
```

`E2R` asks for bounds only on certificates generated by a fully frozen Policy-0B resource discipline (extension generation, retention, proof-DAG sharing and deletion rules explicitly fixed). This does not solve global ER p-boundedness, but it can still falsify or validate the specific JANUS route.

## 9. Hard non-equivalences preserved

```text
B2_SOUNDNESS != B2_P_BOUNDEDNESS
B2_P_BOUNDEDNESS != DETERMINISTIC_PROOF_SEARCH
ER_P_BOUNDEDNESS != P_EQUALS_NP
ER_LOWER_BOUND != KNOWN_NP_NOT_EQUAL_CONP
SHORT_ER_PROOF_EXISTS != POLICY0B_FINDS_IT_IN_POLYTIME
```

## 10. Current status

```text
C025_B2_SOUNDNESS                         = PROVED_IN_SCOPE
C025_E2A_B2_ER_P_EQUIVALENCE             = PROVED
C025_E2B_GLOBAL_ER_P_BOUNDEDNESS         = OPEN
C025_E2R_POLICY0B_RESTRICTED_PROOF_SIZE  = NEXT
C025_C2_DETERMINISTIC_PROOF_SEARCH       = DEFERRED_UNTIL_E2R
ISSUE_212_ACTIVE_REPRESENTATION          = OPEN
P_VS_NP                                  = OPEN
```
