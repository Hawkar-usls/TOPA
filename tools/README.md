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

## TOPA Artifact Classifier

This is TOPA's independent POSS-I image-forensics lane. It borrows useful ideas from public astronomical/ML work but does **not** import a closed VASCO model, closed 107,875-row catalogue, nuclear labels, or substantive UAP interpretations.

The score has deliberately narrow semantics:

```text
candidate_quality_score_raw
    = how point-source-like the image evidence looks
      under the frozen TOPA label contract
```

It is **not** a calibrated physical probability, not proof that the source is a real astrophysical transient, and not a UAP/NHI/nuclear-response score.

### 1. Acquire the pinned public POSS-I cohort

`topa_poss1_open_intake.py` pins a specific `jannefi/poss1-plate-slice` commit and verifies transfer/content hashes before writing anything downstream.

```bash
python tools/topa_poss1_open_intake.py self-test

python tools/topa_poss1_open_intake.py fetch-release \
  --out-dir work/topa-poss1 \
  --receipt work/topa-poss1/intake.receipt.json

python tools/topa_poss1_open_intake.py fetch-plate-metadata \
  --out-dir work/topa-poss1 \
  --receipt work/topa-poss1/plate-metadata.receipt.json

python tools/topa_poss1_open_intake.py write-feature-config \
  --out-dir work/topa-poss1
```

The network-heavy plate-metadata step reads only FITS primary-header bytes needed for `DATE-OBS`/`EXPOSURE` and provenance rather than retaining full plate arrays.

### 2. Build the feature rail

`topa_artifact_features.py` merges the base candidate catalogue with registered sidecars into one JSONL/NDJSON stream. Public astronomy CSV/CSV.GZ/CSV.BZ2 files are accepted as adapters; the canonical TOPA output stays on JSON rails.

```bash
python tools/topa_artifact_features.py self-test
python tools/topa_artifact_features.py build work/topa-poss1/topa_artifact_feature_build_config.json
```

Feature families registered in [`TOPA-ARTIFACT-FEATURE-REGISTRY-v1.0.json`](../research/uap-nuclear/TOPA-ARTIFACT-FEATURE-REGISTRY-v1.0.json) include:

```text
morphology / local PSF
pixel-level shape
plate-centre + physical-edge geometry
SuperCOSMOS R1 cross-scan consistency
PTF coverage/persistence
repeat POSS-I plate/epoch persistence
duplicate geometry
WCS/exposure/acquisition provenance
local field context
future public red/blue cross-band evidence
```

`plate_id`, observation date, coordinates and `group_id` are provenance/split fields, not predictors. Nuclear-window, harmonization, UAP/NHI and effect-statistic fields are rejected from the predictor namespace.

Missing measurements are preserved; this builder does not silently impute or convert “not observed” into negative evidence.

### 3. Freeze a label rail

Training labels live in a **separate** JSONL/NDJSON stream. Minimal contract:

```json
{"candidate_id":"...","label":1,"label_tier":"A","label_source":"...","witness_families":[]}
```

`label=1` means `POINT_SOURCE_LIKE`; `label=0` means `PLATE_OR_SCAN_ARTIFACT_LIKE`.

Tier A is direct preserved pixel/forensic review; Tier B is a strong independent witness; Tier C is a weak proxy/heuristic and cannot be the sole primary training truth.

Critical anti-circularity rule: **if a feature family contributes to a label, that family is forbidden from predictors in that training arm.** For example, SuperCOSMOS may be used as a witness or as a predictor, but not both in the same primary experiment.

### 4. Group-OOF training

Install the small ML dependency set:

```bash
python -m pip install -r tools/requirements-artifact-classifier.txt
```

Then run:

```bash
python tools/topa_artifact_classifier.py self-test
python tools/topa_artifact_classifier.py train training-config.json
```

The reference ensemble contains four deliberately different families:

```text
L2 logistic regression
Random Forest
Extra Trees
Histogram Gradient Boosting
```

The primary ensemble is their unweighted mean raw class-1 score. Candidate rows from the same plate/date group can never be split between train and test. Fold assignment is deterministic from a SHA-256 group hash; random row CV is forbidden.

The training receipt records OOF ROC-AUC, average precision, balanced accuracy, raw-score Brier diagnostic, reliability table, per-fold metrics, label-source/tier census, missingness, exact software versions, model hashes and raw-score distribution diagnostics.

### 5. Score the full open population

```bash
python tools/topa_artifact_classifier.py score scoring-config.json
```

For rows used in training, the analysis stream reuses their preserved group-OOF score when supplied. Rows outside the labelled set use the model fitted to the full labelled training set. Every row records `score_origin` so these cases are never mixed invisibly.

Raw member-model scores and the raw ensemble score are preserved. Calibration is not performed by the v1 primary stream. Any future calibrator must write a separate sidecar and can never overwrite `candidate_quality_score_raw`; a collapsed calibrated distribution is rejected for primary use rather than allowed to destroy the ranking stream.

Canonical scientific contract: [`TOPA_ARTIFACT_CLASSIFIER_PROTOCOL-v1.0.json`](../protocols/TOPA_ARTIFACT_CLASSIFIER_PROTOCOL-v1.0.json).
Bootstrap ledger: [`TOPA-ARTIFACT-CLASSIFIER-BOOTSTRAP-2026-08-27-v1.0.json`](../research/uap-nuclear/TOPA-ARTIFACT-CLASSIFIER-BOOTSTRAP-2026-08-27-v1.0.json).

## POSS-I Closed/Open Harmonization

`topa_poss1_harmonization.py` implements the frozen `TOPA_POSS1_CLOSED_OPEN_HARMONIZATION_01` statistic:

```text
raw candidate-quality/artifact score per candidate
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

- raw artifact/candidate-quality scores are immutable;
- uncalibrated scores are **not** renamed probabilities;
- calibration, when later added, must be a sidecar view rather than a replacement distribution;
- all compared cohorts must use the same frozen calendar/window/statistic before results are compared;
- the classifier must be frozen **before** it is allowed to see any harmonization result;
- a positive result can strengthen a temporal association only, not nuclear causation or UAP/NHI origin.

Self-test:

```bash
python tools/topa_poss1_harmonization.py self-test
```

The exact original closed `107,875` VASCO score-stream comparison remains blocked until authorized row-level scores/opportunity are released. That no longer blocks TOPA itself: the independent public `poss1-plate-slice` reconstruction is the active open cohort and can be scored end-to-end on its own provenance.

See [`TOPA-POSS1-CLOSED-OPEN-HARMONIZATION-01-PREREG-v1.0.json`](../research/uap-nuclear/TOPA-POSS1-CLOSED-OPEN-HARMONIZATION-01-PREREG-v1.0.json).

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
