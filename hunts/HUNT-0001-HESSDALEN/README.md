# HUNT-0001 — Hessdalen Lights

**TOPA first native empirical hunt**  
**State:** `UNRESOLVED_EVENT_FAMILY__REPLICATION_WORTHY`  
**Promotion:** blocked pending raw replay and stronger cross-sensor independence.

> **ANOMALY IS A QUESTION, NOT A CONCLUSION.**

## Why Hessdalen

Hessdalen is an unusually good first test of TOPA because it combines decades of reports, historical instrument work, a modern continuously operating camera system and a public-data route. It is also exactly the kind of subject where weak method can turn “unexplained” into “extraordinary” by accident.

TOPA therefore starts one level earlier:

**Is there a reproducible event family here at all, after known-light, sensor, processing, source-dependence and selection-bias attacks?**

## Frozen question

See [`PREREGISTRATION.json`](PREREGISTRATION.json).

The first hunt asks whether the public record establishes a recurring, source-bound event family strongly enough to justify independent raw-data replication. It does **not** preregister an alien, paranormal, wormhole, plasma or other favored answer.

## PASS-001 result

The first archival/adversarial pass found that the historical corpus is real and research-worthy, while the common-cause claim remains too strong.

Key points from the 1984 technical report:

- event reports, photographs, radar, spectral, magnetic, RF, IR, radiation and seismic channels were documented;
- the report's `F`/`G` anomaly-quality scoring was explicitly subjective;
- only a small subset combined high anomaly score with high report quality;
- 36 radar recordings were listed, but only three were also visually observed as lights;
- the report itself acknowledges incomplete continuous monitoring;
- the reported magnetic coincidence was explicitly recognized as potentially accidental;
- several channels produced null or low-power results.

The current Blue Box workflow improves the situation by recording continuously and exposing public stacked images, with raw video available for selected events and at least one full day. Crucially, the project also documents its own mundane and processing confounders: aircraft, satellites, stars, meteors, birds/insects, lens reflections, H.264 artifacts and stack behavior.

Therefore:

```text
DOCUMENTED RECURRENT CORPUS       = YES
SOME MULTI-CHANNEL OVERLAP        = YES, LIMITED
ONE COMMON PHYSICAL PHENOMENON    = NOT ESTABLISHED
EXTRAORDINARY CAUSE               = NOT ESTABLISHED
REPLICATION VALUE                 = HIGH
```

## Next killer gates

1. **K1 — Modern raw-day replay:** choose a full public day before reading anomaly labels; freeze known-object and artifact rules; classify every track.
2. **K2 — Two-camera parallax:** require geometry and clock bounds before assigning distance or speed.
3. **K3 — Cross-sensor clock:** require synchronized optical + independent non-optical raw channels with timing/error metadata.
4. **K4 — 1984-01-27 reconstruction:** replay the famous radar/visual speed claim against radar sweep cadence, geometry, propagation and timing uncertainty.
5. **K5 — Holdout classifier:** train mundane exclusion rules on one period, freeze them, and score a separate date range.

## Files

- [`PREREGISTRATION.json`](PREREGISTRATION.json) — frozen question, hypotheses and gates.
- [`SOURCE_LEDGER.json`](SOURCE_LEDGER.json) — source classes and authority boundaries.
- [`PASS-001-ARCHIVAL-ADVERSARIAL.json`](PASS-001-ARCHIVAL-ADVERSARIAL.json) — first full TOPA pass.
- [`STATUS.json`](STATUS.json) — current machine-readable state.

## Current law learned

```text
RECURRENT REPORTS != ONE PHENOMENON
MULTI_CHANNEL != INDEPENDENT COMMON CAUSE
RADAR RETURN != OBJECT IDENTITY
STACKED IMAGE != RAW VIDEO
UNEXPLAINED != EXTRAORDINARY
```

The hunt remains open by design. A future raw replay is allowed to strengthen the anomaly case, weaken it, split it into multiple ordinary families, or close it entirely.
