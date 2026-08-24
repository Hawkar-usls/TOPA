# TOPA · Sacred Scriptures Corpus

**Branch:** `topa-sacred-scriptures`  
**Status:** `ACTIVE_RESEARCH / CORPUS_BUILD_V0_1`  
**Motto:** `TEXT IS EVIDENCE OF A TRADITION; TEXT ALONE IS NOT PROOF OF A METAPHYSICAL CLAIM.`

This research surface builds a provenance-bound, cross-tradition corpus of texts regarded as sacred, canonical, revealed, liturgical, foundational, or quasi-scriptural by their communities.

The target is deliberately broader than “Bible / Torah / Qur'an”. It includes Abrahamic, Dharmic, Iranian, East Asian, ancient Mediterranean/Near Eastern, Indigenous/oral and modern religious corpora while preserving the fact that **different traditions do not use the category “scripture” in the same way**.

## Core boundary

```text
TEXT_EXISTS != EVENT_HAPPENED
TRADITIONAL_ATTRIBUTION != HISTORICAL_AUTHORSHIP
CANONICAL_STATUS != EMPIRICAL_TRUTH
TRANSLATION != ORIGINAL
COMMENTARY != PRIMARY_SCRIPTURE
SHARED_MOTIF != SHARED_SOURCE
MODEL_CONSENSUS != INDEPENDENT_CONFIRMATION
ABSENCE_FROM_CORPUS != ABSENCE_FROM_WORLD
```

TOPA may test chronology, textual dependence, manuscript families, motif recurrence, translation drift, historical diffusion and contradictions. It **cannot** turn text comparison alone into proof or disproof of God, revelation, miracles, prophecy or any other metaphysical claim.

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
META-REGISTRY-> append-only lineage and supersession
LAPIS        -> stable extracted invariant candidates, never truth authority
AURA         -> symbolic/associative hypothesis generator only; evidence authority = 0
TERMINAL     -> human-visible execution/report surface
VOICE        -> presentation layer after evidence state is frozen
TOPA         -> final epistemic envelope and classification
```

`ALL_NODES_AGREE != WORLD_TRUTH`.

## First research questions

- Which motifs recur independently after controlling for known historical contact?
- Which apparent parallels disappear when compared in original language and historical context?
- Can rare motif bundles or phrase structures identify textual borrowing or common ancestry?
- How do creation, flood, law/covenant, sacrifice, death/rebirth, judgment, apocalypse, sacred geography and ethical reciprocity transform across traditions?
- Can TOPA distinguish **human universals**, **historical diffusion**, **translation convergence**, **genre convention**, and genuinely unresolved residuals?

## Files

- `CORPUS_MANIFEST.v0.1.json` — open-ended cross-tradition seed corpus.
- `JANUS_COUNCIL_PROTOCOL.v0.1.json` — role-separated whole-JANUS research protocol.
- `TOPA_FIRST_PASS.v0.1.json` — first falsification-first result and next gates.
- `PROVENANCE_AND_RIGHTS.md` — ingestion and copyright/community-control rules.

## Status warning

The phrase “all sacred scriptures of all peoples” is an **open-ended target, not a completed coverage claim**. Many traditions are oral, internally diverse, poorly digitized, restricted, or disagree about canon. Every missing family is a corpus defect to be recorded, not silently treated as nonexistent.
