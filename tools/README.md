# TOPA tools

## JSON Rails

`topa_json_rails.py` is TOPA's native machine-readable transport layer for evidence dumps and receipts.

Supported inputs/outputs:

```text
.json
.json.gz
.json.bz2
.jsonl / .ndjson
.jsonl.gz / .ndjson.gz
.jsonl.bz2 / .ndjson.bz2
```

Large JSONL/NDJSON dumps are processed record-by-record instead of being loaded into RAM as one giant object. Monolithic `.json` remains supported, but a huge top-level array is intentionally treated as a non-streaming format; use JSONL/NDJSON for large-scale work.

Examples:

```bash
# deterministic capability test
python tools/topa_json_rails.py self-test

# inspect + hash a dump
python tools/topa_json_rails.py inspect evidence.jsonl.gz

# stream-search a nested field and write matching records compressed
python tools/topa_json_rails.py search evidence.ndjson.bz2 \
  --field source.title \
  --contains palomar \
  --contains nuclear \
  --all \
  --out matches.jsonl.gz \
  --receipt search-receipt.json

# convert while preserving a machine-readable receipt
python tools/topa_json_rails.py convert input.json output.jsonl.bz2 \
  --receipt convert-receipt.json
```

The rails record both raw-file SHA-256 and a canonical logical-record-stream SHA-256 where applicable. JSON validity, hashes and search hits are provenance tools, **not evidence that a represented claim is true**.

Canonical rules live in [`protocols/TOPA_JSON_RAILS_PROTOCOL-v1.0.json`](../protocols/TOPA_JSON_RAILS_PROTOCOL-v1.0.json).

## POSS-I Closed/Open Harmonization

`topa_poss1_harmonization.py` implements the frozen `TOPA_POSS1_CLOSED_OPEN_HARMONIZATION_01` statistic:

```text
raw artifact score per candidate
        ↓ sum by observed date
artifact-score-weighted nightly outcome
        ÷
actual observing opportunity
        ↓
exposed vs non-exposed rate ratio
        ↓
exhaustive circular-shift nuclear-calendar null
```

Important boundaries:

- raw artifact scores are immutable;
- uncalibrated scores are **not** renamed probabilities;
- calibration, when later added, must be a sidecar view rather than a replacement distribution;
- closed and open cohorts must use the same frozen calendar/window/statistic before results are compared;
- a positive result can strengthen a temporal association only, not nuclear causation or UAP/NHI origin.

Self-test:

```bash
python tools/topa_poss1_harmonization.py self-test
```

The real experiment remains blocked until the exact closed `107,875` candidate rows/scores and a compatible observing-opportunity manifest are available or independently reconstructed. See [`TOPA-POSS1-CLOSED-OPEN-HARMONIZATION-01-PREREG-v1.0.json`](../research/uap-nuclear/TOPA-POSS1-CLOSED-OPEN-HARMONIZATION-01-PREREG-v1.0.json).

## Retina Video Bridge

`topa_retina_video.py` turns local files, HTTP(S) video, or public Google Drive media into an evidence-bound visual inspection surface:

```text
source -> acquire -> SHA-256 -> ffprobe -> timestamped frame samples
       -> frame hashes -> contact sheets -> optional Retina analysis
```

Quick check:

```bash
python tools/topa_retina_video.py --self-test
```

Public Google Drive support requires `gdown`; media decoding requires `ffmpeg` / `ffprobe`.

See [`docs/RETINA_VIDEO_BRIDGE.md`](../docs/RETINA_VIDEO_BRIDGE.md) for the full method and claim boundaries.
