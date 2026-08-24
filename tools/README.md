# TOPA tools

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
