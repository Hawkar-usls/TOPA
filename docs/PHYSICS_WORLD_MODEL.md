# TOPA Physics World Model

`tools/topa_world_model.py` is TOPA's safe, uncertainty-aware predictive physics layer for benign robotics, navigation, environmental dynamics, latency compensation and scientific simulation.

It is intentionally **not** a weapons or fire-control module. Ballistic targeting, weapon aiming, projectile-impact optimization and weaponized interception are rejected by the runtime safety gate.

## What it does

The primary v1 kernel models a planar mobile platform and generates a deterministic Latin-hypercube cloud of futures under uncertain drag, rolling loss, environmental drift and control scale.

```text
estimated state
    + controls
    + environment
    + uncertainty ranges
          |
          v
TOPA physics baseline
          |
          v
N scenario rollouts
          |
          +--> immutable scenario parameters
          +--> trajectory / endpoint per scenario
          +--> endpoint quantiles
          +--> result SHA-256
```

A prediction is always labelled as model-conditioned output, never as observation.

## Example

```json
{
  "purpose": "warehouse mobile robot navigation",
  "initial_state": {
    "x_m": 0.0,
    "y_m": 0.0,
    "yaw_rad": 0.0,
    "speed_mps": 1.0,
    "yaw_rate_rps": 0.0
  },
  "control": {
    "linear_accel_mps2": 0.1,
    "yaw_accel_rps2": 0.02
  },
  "environment": {
    "drag_per_s": 0.02,
    "rolling_loss_mps2": 0.01,
    "drift_x_mps": 0.0,
    "drift_y_mps": 0.0
  },
  "uncertainty": {
    "drag_per_s": {"min": 0.01, "max": 0.03},
    "rolling_loss_mps2": {"min": 0.0, "max": 0.02},
    "drift_x_mps": {"min": -0.02, "max": 0.02},
    "drift_y_mps": {"min": -0.02, "max": 0.02},
    "control_scale": {"min": 0.98, "max": 1.02}
  },
  "dt_s": 0.05,
  "horizon_s": 2.0,
  "scenario_count": 512,
  "seed": 42
}
```

Run:

```bash
python tools/topa_world_model.py rollout config.json --out future-cloud.json
```

Latency compensation:

```bash
python tools/topa_world_model.py latency-compensate latency-config.json --out compensated-state.json
```

## Backends

The canonical baseline is intentionally small and portable: NumPy plus a deterministic TOPA kernel. The locked development environment also includes official MuJoCo Python bindings for higher-fidelity benign rigid-body/contact research. MuJoCo is optional for the v1 baseline and may not overwrite baseline provenance.

## Learned residuals / PINN / MBRL

A learned residual can be added later, but TOPA requires it to be a sidecar:

```text
physics_baseline(t)
       +
learned_residual(t | training-data hash, model hash)
       =
augmented_prediction(t)
```

The baseline must remain reconstructable. A neural model is not allowed to silently rewrite raw physics output.

## Scientific boundary

- prediction != observation
- simulation != validation
- rank/confidence != truth
- every run records seed, parameters and SHA-256
- uncertainty is preserved rather than collapsed to one future
- failed predictions remain useful calibration data
- sim-to-real error must be measured against later observation

Canonical contract: `protocols/TOPA_PHYSICS_WORLD_MODEL_PROTOCOL-v1.0.json`.
