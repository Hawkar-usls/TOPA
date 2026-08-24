# HUNT-0001 — K1 Modern Raw-Day Replay

**State:** preregistered; acquisition not yet executed.

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

## Holdout discipline

Any thresholds or classifiers tuned on part of the day must be frozen before a separate holdout interval is scored. `No counterexample found` is not a positive extraordinary result.

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

## Current blocker

The public Project Hessdalen page confirms that a full raw day is available, but the current retrieval path does not expose the Google Drive directory listing needed to enumerate and download it reproducibly. The correct state is therefore `ACQUISITION_OPEN`, not `REPLAY_COMPLETE`.

That failure is useful: the experiment is frozen before data inspection.
