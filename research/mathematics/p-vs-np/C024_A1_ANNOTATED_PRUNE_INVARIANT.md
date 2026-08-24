# C024 A1 — Annotated-Prune Invariant Under Local Resolution

**Status:** partial invariant proved; orientation recovery remains open for the unpadded source-GT route. A stronger resolution-sink counterfamily is now the primary #211 attack, but this result is preserved because it constrains future calculi.

## Setting

Use the theorem-matched directed `GT_n` encoding with variables `x_(i,j)` for `i != j`, totality clauses

```text
x_(i,j) OR x_(j,i)
```

and antisymmetry clauses

```text
~x_(i,j) OR ~x_(j,i).
```

A Policy-0A cache key is taken after exhaustive unit propagation and before the local one-layer Resolution pass. Local Resolution adds clauses but introduces no variables and does not delete an unsatisfied original clause.

## Lemma A1.1 — incomparability signature survives

At every nonterminal pre-resolution key `K` reached from source `GT_n`, after including all inherited local resolvents, an unordered vertex pair `{i,j}` is still incomparable in the transitively closed cumulative core restriction iff the original totality clause

```text
(x_(i,j) OR x_(j,i))
```

is present in `K`.

### Proof

Fix `{i,j}`.

If neither orientation variable has been assigned, the original totality clause is not satisfied and no literal is deleted from it. Local Resolution only adds clauses, so the totality clause remains in the residual and survives canonical deduplication.

If one orientation is assigned false, totality becomes a unit forcing the opposite orientation true. If one orientation is assigned true, antisymmetry becomes a unit forcing the opposite orientation false. Exhaustive unit propagation therefore eliminates both directed variables from the residual whenever the pair becomes oriented.

Transitivity is also represented by GT clauses; whenever existing assignments force a transitive orientation, the corresponding transitivity clause becomes unit and exhaustive unit propagation installs that orientation. Hence after the fixpoint, a pair whose directed variables remain unassigned is precisely a pair not ordered by the current transitive closure.

Therefore presence of the source totality clause is an exact marker of current incomparability. □

## Corollary A1.1a — exact cache equality preserves the incomparability graph

If two Policy-0A pre-resolution keys are byte-for-byte equal, their sets of source totality clauses are equal. By Lemma A1.1, the induced undirected incomparability graphs are equal.

Thus inherited local resolvents cannot make two exact cache keys collide while changing which unordered pairs are comparable.

## Why this does not yet recover `prune(sigma)`

The Beame–Impagliazzo–Pitassi–Segerlind `prune` invariant is oriented: two partial orders may have the same undirected comparability/incomparability graph while disagreeing about the direction of comparable pairs.

The historical Lemma 4.27 recovers orientation from restricted nonminimality and transitivity clauses under Weakening/Subsumption. In JANUS-FC_local, inherited derived clauses can in principle add clauses with the same syntactic shapes and therefore may obscure a direct source-clause argument.

The missing positive subgate was therefore:

```text
A1.2 ORIENTATION_RECOVERY
```

Prove that equality of two augmented keys `GT_n|sigma AND D_sigma` and `GT_n|tau AND D_tau` forces

```text
prune(sigma) = prune(tau),
```

or exhibit a concrete collision where orientation information is erased by the derived ledgers.

## Current research consequence

The separate resolution-sink padding construction avoids needing A1.2 to attack Issue #211: it forces the local pass never to touch the GT core, reducing the projected execution to ordinary exact Formula Caching. Therefore A1.2 is no longer the shortest route to falsifying the current Policy-0A residual-count premise.

Still, A1.1 is retained as a design constraint for future variants:

```text
LOCAL_INFERENCE_MAY_ADD_INFORMATION,
BUT EXACT_KEYS_CANNOT_HIDE_WHICH_GT_PAIRS_REMAIN_UNORDERED.
```

## Claim boundary

This note proves only the incomparability-signature statement. It does not prove the full historical prune invariant under arbitrary inherited Resolution clauses and does not resolve P versus NP.
