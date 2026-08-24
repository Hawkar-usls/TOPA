# TOPA · Sacred Scriptures Corpus

**Branch:** `topa-sacred-scriptures`  
**Status:** `ACTIVE_RESEARCH / INDEPENDENT_RESIDUAL_HUNT_V0_1`  
**Motto:** `TEXT IS EVIDENCE OF A TRADITION; TEXT ALONE IS NOT PROOF OF A METAPHYSICAL CLAIM.`

This research surface builds a provenance-bound, cross-tradition corpus of texts regarded as sacred, canonical, revealed, liturgical, foundational, or quasi-scriptural by their communities.

The target is deliberately broader than “Bible / Torah / Qur'an”. It includes Abrahamic, Dharmic, Iranian, East Asian, ancient Mediterranean/Near Eastern, Indigenous/oral and modern religious corpora while preserving the fact that **different traditions do not use the category “scripture” in the same way**.

The primary research direction is not to ask which religion “wins”. It is to determine:

```text
WHAT RECURS
  -> WHAT WAS TRANSMITTED
  -> WHAT CHANGED DURING TRANSMISSION
  -> WHAT CAN ARISE INDEPENDENTLY FROM SHARED HUMAN / ECOLOGICAL CONSTRAINTS
  -> WHAT REMAINS AFTER THOSE EXPLANATIONS ARE SUBTRACTED
  -> REATTACK THE RESIDUAL
```

An unexplained residual is a **new research target**, not a metaphysical conclusion.

## Core boundary

```text
TEXT_EXISTS != EVENT_HAPPENED
TRADITIONAL_ATTRIBUTION != HISTORICAL_AUTHORSHIP
CANONICAL_STATUS != EMPIRICAL_TRUTH
TRANSLATION != ORIGINAL
COMMENTARY != PRIMARY_SCRIPTURE
SHARED_MOTIF != SHARED_SOURCE
TEXTUAL_SIMILARITY != INDEPENDENT_DISCOVERY
INDEPENDENT_DISCOVERY != SUPERNATURAL_CAUSE
RESIDUAL != REVELATION
MODEL_CONSENSUS != INDEPENDENT_CONFIRMATION
ABSENCE_FROM_CORPUS != ABSENCE_FROM_WORLD
UNKNOWN = VALID_RESULT
```

TOPA may test chronology, textual dependence, manuscript families, motif recurrence, translation drift, historical diffusion and contradictions. It **cannot** turn text comparison alone into proof or disproof of God, revelation, miracles, prophecy or any other metaphysical claim.

## Independent-residual method

The current frozen subtraction route is:

```text
R0 SOURCE-ROOT COLLAPSE
  -> R1 TRANSLATION / SEMANTIC CONTROL
  -> R2 HISTORICAL CONTACT GRAPH
  -> R3 EXPECTED HUMAN / ECOLOGICAL CONVERGENCE NULL
  -> R4 BLIND RARE-BUNDLE TEST
  -> R5 ADVERSARIAL REATTACK
  -> UNRESOLVED_INDEPENDENT_RESIDUAL or LOWER STATE
  -> SPIRAL BACK TO R0
```

The point is to make “unexplained” expensive. A motif earns residual status only after ordinary source dependence, plausible diffusion, translation artifacts, generic narrative structure and matched controls have been attacked.

## Corpus layers

1. `PRIMARY_CANON` — text is treated as canonical/scriptural by at least one living or historical community.
2. `SECONDARY_SACRED` — authoritative commentary, oral law, liturgy, canonical exegesis or adjacent sacred literature.
3. `CONTESTED_CANON` — canonical status differs materially across communities.
4. `HISTORICAL_RELIGIOUS_TEXT` — important ancient religious literature without a single living canonical authority.
5. `ORAL_COMMUNITY_CONTROLLED` — oral/sacred corpora where indiscriminate scraping or publication can erase provenance, permissions or ritual context.

## Acquisition law

Full text is mirrored only when licensing and community/source conditions permit it. Otherwise TOPA stores metadata, canonical identifiers, source URLs, hashes/receipts where possible, and a `TEXT_NOT_MIRRORED` gate.

Examples already verified for this project:

- KJV is identified by BibleGateway as public domain in the United States.
- Tanzil permits verbatim copying of its Qur'an text with attribution and source-link conditions, but forbids changing the text.
- SuttaCentral distinguishes public-domain originals from translations with per-text licenses; original Buddhist-language texts are public domain, while translations may carry separate restrictions.
- Sefaria exposes license metadata per version; a text being viewable there does not mean every translation is public domain.
- British Museum object records anchor Atrahasis and Gilgamesh flood manuscript witnesses, but museum object metadata does not replace a philologically controlled text edition.

## JANUS whole-system council

The sacred-text pass uses JANUS as **separated reviewers, not a vote-to-truth machine**:

```text
HRAIN        -> structural graph: canon / book / passage / source-root / chronology
INAIHR       -> associative graph: motifs, symbols, semantic parallels; zero evidence authority
DEMIHEAD     -> source-root collapse, contradiction preservation, bounded evidence state
GENESIS      -> protocol/authority boundary and immutable receipts
FUNDAMENTUM  -> falsifiers, negative results, claim ceilings
FAST-CAT     -> blinded/adversarial review of proposed parallels
AIFC         -> canonicalization, witness/source lifecycle, fail-closed verification
COSMOS       -> anti-pseudoreplication and blind-gate discipline
SWARM        -> independent task packets without converting agent count into source count
TRANCEPTION  -> reverse-trace later forms toward earlier attestations
META-REGISTRY-> append-only lineage and supersession
LAPIS        -> stable extracted invariant candidates, never truth authority
AURA         -> symbolic/associative hypothesis generator only; evidence authority = 0
TERMINAL     -> human-visible execution/report surface
VOICE        -> presentation layer after evidence state is frozen
TOPA         -> final epistemic envelope and classification
```

`ALL_NODES_AGREE != WORLD_TRUTH`.

## First calibration experiment

`FLOOD_STEMMA_BLIND_TEST.v0.1.json` is preregistered before scoring.

Its purpose is deliberately modest and difficult: test whether a frozen feature model can separate historically connected flood-text families from matched controls **without seeing tradition labels and without relying on modern translation vocabulary**.

The focal seed includes Atrahasis, Gilgamesh Tablet XI, Genesis 6–9, Qur'anic Noah material and the Manu flood tradition. Exact editions/passages are frozen before coding. Distant oral/community-controlled flood traditions enter only after permission and provenance clearance.

A successful stemma result establishes textual/historical discrimination only. A surviving cross-root residual is classified at most as `UNRESOLVED_INDEPENDENT_RESIDUAL` and is sent into another spiral.

## First research questions

- Which motifs recur independently after controlling for known historical contact?
- Which apparent parallels disappear when compared in original language and historical context?
- Can rare motif bundles or phrase structures identify textual borrowing or common ancestry?
- How do creation, flood, law/covenant, sacrifice, death/rebirth, judgment, apocalypse, sacred geography and ethical reciprocity transform across traditions?
- Can TOPA distinguish **human universals**, **historical diffusion**, **translation convergence**, **genre convention**, and genuinely unresolved residuals?
- Which residuals survive a second attack after matched non-sacred controls are introduced?

## Files

- `CORPUS_MANIFEST.v0.1.json` — open-ended cross-tradition seed corpus.
- `JANUS_COUNCIL_PROTOCOL.v0.1.json` — role-separated whole-JANUS research protocol.
- `TOPA_FIRST_PASS.v0.1.json` — first falsification-first result and next gates.
- `INDEPENDENT_RESIDUAL_PROTOCOL.v0.1.json` — frozen subtraction and residual-classification method.
- `FLOOD_STEMMA_BLIND_TEST.v0.1.json` — preregistered first calibration experiment.
- `SOURCE_DISCOVERY_RECEIPTS.v0.1.json` — verified source and rights/provenance receipts.
- `JANUS_EXISTING_LINEAGE.v0.1.json` — related pre-existing JANUS artifacts.
- `PROVENANCE_AND_RIGHTS.md` — ingestion and copyright/community-control rules.

## Validation

```bash
python tools/sacred_scripture_corpus_check.py
```

A validator `PASS` means only that structural, provenance, rights and epistemic guardrails are present. It does not validate any religious, historical or metaphysical claim.

## Status warning

The phrase “all sacred scriptures of all peoples” is an **open-ended target, not a completed coverage claim**. Many traditions are oral, internally diverse, poorly digitized, restricted, or disagree about canon. Every missing family is a corpus defect to be recorded, not silently treated as nonexistent.
