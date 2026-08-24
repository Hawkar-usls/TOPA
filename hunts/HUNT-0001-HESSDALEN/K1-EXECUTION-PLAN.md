# HUNT-0001 — K1 Modern Raw-Day Replay

**State:** preregistered; video acquisition/viewing bridge implemented; complete raw-day dataset not yet frozen.

The first executable modern test is a blind full-day replay. The day is selected before inspecting anomaly labels or curated event commentary.

## Frozen selection rule

Use the lexicographically earliest complete raw day publicly accessible from the Project Hessdalen data surface at execution time. A complete day must contain the expected 20-minute segments for at least one operational camera with no unexplained gaps. If no complete day can be enumerated, stop as `ACQUISITION_BLOCKED`; do not substitute attractive clips.

## Data volume

Project Hessdalen documents two operational 4K cameras at 25 fps, approximately 45 GB per camera per day, or roughly 90 GB/day for the pair. Raw videos date back to November 2024 and a full public day is stated to be available for testing.

## Replay order

```text
COMPLETE RAW DAY
→ hash + continuity check
→ raw-frame decode
→ camera calibration
→ stars / planets
→ satellites / spacecraft
→ aircraft
→ meteors
→ birds / insects
→ lens / internal reflections
→ H.264 / codec artifacts
→ stacking artifacts
→ other conventional / uncertain
→ RESIDUAL_UNCLASSIFIED
```

A stack-only feature can never become a TOPA residual. The corresponding raw video must exist and preserve the feature.

## Retina video bridge

TOPA now has a native evidence-preserving media bridge at:

```text
tools/topa_retina_video.py
```

It accepts local media, ordinary HTTP(S) media and public Google Drive file/folder URLs. Public Drive support uses optional `gdown`; every acquired file is frozen by filename, byte count and SHA-256 before analysis.

The bridge produces `ffprobe` metadata, deterministic timestamped frame samples, frame hashes, contact sheets and optional source-bound Retina analysis. It does not delete source data or derived frames.

Example public Drive acquisition:

```bash
python -m pip install gdown
python tools/topa_retina_video.py 'https://drive.google.com/drive/folders/FOLDER_ID' --out runs/hessdalen-drive
```

This fixes the **tooling/viewing** problem, not the **dataset-membership** problem:

```text
ABLE_TO_ENUMERATE_OR_DOWNLOAD_PUBLIC_DRIVE
!=
ONE_COMPLETE_RAW_DAY_PROVEN
```

The selected K1 day must still be frozen from a reproducible segment manifest or an independently verified complete-day listing.

## Holdout discipline

Any thresholds or classifiers tuned on part of the day must be frozen before a separate holdout interval is scored. `No counterexample found` is not a positive extraordinary result.

The Retina bridge's interval sampling/contact sheets are for visual access and QC only. A sub-second event can fall between samples, so K1's scientific event search must still operate on the full-rate source stream or an equivalently loss-bounded track detector.

## K2 correction

The two currently operational 4K cameras are documented as being on the same Blue Box mast, looking west and south. They are **not automatically a useful parallax pair**.

`K2_TWO_CAMERA_PARALLAX` is replaced by `K2_STEREO_BASELINE_GATE`:

```text
surveyed separated positions
+ overlapping FOV
+ synchronized clocks
+ calibrated intrinsics/extrinsics
+ same raw event in both stations
→ only then triangulate distance / altitude / speed
```

Without that gate, TOPA may report angular motion only.

## Current acquisition state

The earlier blocker — inability of the browser retrieval channel to expose a reproducible Google Drive folder listing — is no longer treated as a general inability to inspect video. TOPA can now acquire public Drive media through the Retina bridge and freeze hashes locally.

The remaining blocker is narrower and scientific: TOPA does not yet know which exact public files constitute one complete raw day, their segment continuity, authoritative timestamp basis, camera geometry/calibration, or whether the third remote/test camera provides a surveyed usable stereo baseline.

A source-bound request for those fields was sent to Project Hessdalen on 2026-08-24 and is recorded in `CONTACT-001-HESSDALEN-RAW-DATA-REQUEST.json`.

Until that dataset boundary is resolved, state remains:

```text
VIDEO_INGEST = IMPLEMENTED
RAW_DAY_MEMBERSHIP = OPEN
K1_REPLAY = NOT_YET_EXECUTED
K2_TRIANGULATION = BLOCKED_PENDING_BASELINE_AND_CALIBRATION
```
