# TOPA Retina Video Bridge

**Status:** `IMPLEMENTED / LIVE_DATASET_REPLAY_NOT_YET_EXECUTED`

TOPA needs to inspect video without making a web UI, a curated clip, or a model response the authority for the underlying evidence. The Retina Video Bridge therefore separates **transport**, **media decoding**, **visual interpretation**, and **scientific classification**.

## JANUS lineage

The bridge reuses two established JANUS design ideas without importing their live transports or secrets:

1. **Retina** — an image is encoded and passed to a vision model as a source-bound visual observation.
2. **Telegram Bot Hub vision path** — perception is normalized separately from Telegram transport so that a media source does not become evidence merely because a bot received it.

TOPA deliberately does **not** copy Telegram tokens, chat IDs, runtime configuration, live databases, or polling logic. It also changes one behavior of the old Retina design: TOPA does **not delete evidence or derived frames after analysis**. Reproducibility takes priority over cache cleanup inside a hunt.

## Pipeline

```text
LOCAL FILE / HTTP FILE / PUBLIC GOOGLE DRIVE FILE OR FOLDER
        ↓
ACQUIRE WITHOUT MUTATING SOURCE
        ↓
SHA-256 EVERY ACQUIRED FILE
        ↓
FFPROBE CONTAINER + STREAM METADATA
        ↓
DETERMINISTIC TIMESTAMPED FRAME SAMPLING
        ↓
SHA-256 EACH DERIVED FRAME
        ↓
CONTACT SHEETS FOR HUMAN VISUAL ACCESS
        ↓
OPTIONAL RETINA FRAME ANALYSIS
        ↓
RUN.json + video_manifest.json + frame_manifest.json
```

The implementation is [`tools/topa_retina_video.py`](../tools/topa_retina_video.py).

## Google Drive fix

A Google Drive browser page is not a reproducible scientific listing. The bridge therefore supports **public Drive file/folder acquisition through `gdown`** and immediately freezes the resulting local file list and SHA-256 hashes.

This creates an auditable acquisition snapshot even if the Drive UI changes later.

Install optional Drive support:

```bash
python -m pip install gdown
```

The Drive folder remains a discovery/transport surface. The actual evidence boundary is:

```text
SOURCE URL
+ acquired filename
+ byte size
+ SHA-256
+ media metadata
```

For HUNT-0001 we still ask Project Hessdalen for the exact full raw-day location and a segment manifest, because a public camera folder may contain stacks, selected clips, partial days or later-added files. `ABLE_TO_DOWNLOAD_A_FOLDER != COMPLETE_RAW_DAY_PROVEN`.

## Video viewing

Requirements:

- Python 3.10+
- `ffmpeg`
- `ffprobe`
- optional `gdown` for public Google Drive
- optional `TOPA_RETINA_API_KEY` for Retina analysis

Local video:

```bash
python tools/topa_retina_video.py sample.mp4 --out runs/sample
```

Public HTTP video:

```bash
python tools/topa_retina_video.py 'https://example.org/video.mp4' --out runs/http
```

Public Google Drive folder:

```bash
python tools/topa_retina_video.py 'https://drive.google.com/drive/folders/FOLDER_ID' --out runs/drive
```

With Retina inspection of sampled frames:

```bash
export TOPA_RETINA_API_KEY='...'
python tools/topa_retina_video.py sample.mp4 --retina --retina-max 64 --out runs/retina
```

For a frozen source manifest:

```json
{
  "sources": [
    {"url": "https://example.org/camera-A-segment-0001.mp4"},
    {"path": "/data/camera-A-segment-0002.mp4"}
  ]
}
```

Run:

```bash
python tools/topa_retina_video.py sources.json --manifest --out runs/frozen-day
```

## What Retina is allowed to say

The optional vision stage is a **visual observer**, not a cause detector. The prompt is bounded to visible objects, lights, tracks/streaks, artifact candidates, sky/weather context and uncertainty.

```text
RETINA RECOGNITION != PHYSICAL IDENTIFICATION
MODEL DESCRIPTION != TRACK CLASSIFICATION
UNRECOGNIZED != EXTRAORDINARY
```

Every Retina row is tied to a frame hash and source timestamp when available.

## Sampling boundary

The default deterministic interval sampling exists so a human or vision model can efficiently inspect long video and verify that decoding works.

It is **not** the K1 anomaly detector. A sub-second event can fall between sampled frames. Therefore:

```text
CONTACT SHEET / RETINA SAMPLE
!=
FULL-RATE EVENT SEARCH
```

K1 still requires the frozen full-rate/track-level conventional-classification pipeline over the complete selected day. Once a candidate interval exists, the bridge can be rerun on that exact source segment at much denser sampling for visual review.

## HUNT-0001 connection

For Hessdalen the bridge removes the previous tooling limitation: TOPA can now ingest public video files/folders into a reproducible local evidence surface instead of depending on the browser listing.

The remaining acquisition question is scientific rather than perceptual:

- Which exact public files constitute one **complete raw day**?
- Are any 20-minute segments missing or corrupt?
- Which camera and timestamp standard produced each segment?

Those questions were sent to Project Hessdalen separately. Until answered or independently resolved, K1 remains `ACQUISITION_OPEN`, not `REPLAY_COMPLETE`.

## K2 boundary

The Retina bridge can show simultaneous media but cannot manufacture parallax. K2 remains gated by surveyed station separation, overlapping field of view, clock synchronization and intrinsic/extrinsic calibration.

```text
TWO VIDEOS != STEREO BASELINE
VISUAL MATCH != TRIANGULATION
```

## Self-test

The dependency-free internal test is:

```bash
python tools/topa_retina_video.py --self-test
```

Expected marker:

```text
TOPA_RETINA_VIDEO_SELF_TEST=PASS
```

This only tests the internal deterministic fixture. It does not test `ffmpeg`, Google Drive access, a vision API, or any Hessdalen claim.
