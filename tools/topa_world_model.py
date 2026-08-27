#!/usr/bin/env python3
"""TOPA Physics World Model v1.

Safe general-purpose predictive physics for benign robotics/navigation/scientific
simulation. This module intentionally excludes weapon targeting, ballistic fire
control, projectile impact optimization, and weaponized interception.

The primary kernel is a deterministic planar mobile-platform model with
uncertainty-preserving multi-scenario rollouts. A learned residual may be added
later only as a separate sidecar; it may never overwrite the physics baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    raise SystemExit("numpy is required: pip install numpy") from exc

SCHEMA = "hawkar.topa.physics_world_model.v1"

FORBIDDEN_PURPOSE_TOKENS = {
    "weapon", "weapons", "firearm", "rifle", "gun", "ballistic", "ballistics",
    "projectile", "aim", "aiming", "targeting", "impact optimization", "missile",
    "weaponized intercept", "weaponised intercept", "fire control",
}


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_obj(obj: Any) -> str:
    return hashlib.sha256(_canonical_json(obj)).hexdigest()


def _check_safe_purpose(cfg: Dict[str, Any]) -> None:
    text = " ".join(
        str(cfg.get(k, "")) for k in ("purpose", "task", "description", "mode")
    ).lower()
    hits = sorted(t for t in FORBIDDEN_PURPOSE_TOKENS if t in text)
    if hits:
        raise ValueError("TOPA_WORLD_MODEL_SAFETY_REJECT:" + ",".join(hits))


@dataclass(frozen=True)
class State:
    x_m: float
    y_m: float
    yaw_rad: float
    speed_mps: float
    yaw_rate_rps: float


@dataclass(frozen=True)
class Control:
    linear_accel_mps2: float
    yaw_accel_rps2: float


@dataclass(frozen=True)
class Environment:
    drag_per_s: float
    rolling_loss_mps2: float
    drift_x_mps: float
    drift_y_mps: float


@dataclass(frozen=True)
class Scenario:
    scenario_id: int
    drag_per_s: float
    rolling_loss_mps2: float
    drift_x_mps: float
    drift_y_mps: float
    control_scale: float


def _finite(name: str, value: Any) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"NONFINITE:{name}")
    return x


def parse_state(d: Dict[str, Any]) -> State:
    return State(*[_finite(k, d[k]) for k in ("x_m", "y_m", "yaw_rad", "speed_mps", "yaw_rate_rps")])


def parse_control(d: Dict[str, Any]) -> Control:
    return Control(_finite("linear_accel_mps2", d.get("linear_accel_mps2", 0.0)),
                   _finite("yaw_accel_rps2", d.get("yaw_accel_rps2", 0.0)))


def parse_environment(d: Dict[str, Any]) -> Environment:
    return Environment(
        max(0.0, _finite("drag_per_s", d.get("drag_per_s", 0.0))),
        max(0.0, _finite("rolling_loss_mps2", d.get("rolling_loss_mps2", 0.0))),
        _finite("drift_x_mps", d.get("drift_x_mps", 0.0)),
        _finite("drift_y_mps", d.get("drift_y_mps", 0.0)),
    )


def _wrap_angle(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def step(state: State, control: Control, env: Environment, dt_s: float, control_scale: float = 1.0) -> State:
    """One semi-implicit Euler step for a planar mobile platform."""
    dt = _finite("dt_s", dt_s)
    if not (0.0 < dt <= 1.0):
        raise ValueError("dt_s must be in (0, 1]")

    a_cmd = control.linear_accel_mps2 * control_scale
    yaw_a = control.yaw_accel_rps2 * control_scale

    # Passive speed losses oppose current motion; no hidden sign flip at rest.
    loss = env.drag_per_s * abs(state.speed_mps) + env.rolling_loss_mps2
    if abs(state.speed_mps) < 1e-12 and abs(a_cmd) <= loss:
        new_speed = 0.0
    else:
        signed_loss = math.copysign(loss, state.speed_mps if abs(state.speed_mps) > 1e-12 else a_cmd)
        new_speed = state.speed_mps + (a_cmd - signed_loss) * dt
        if state.speed_mps > 0.0 and new_speed < 0.0 and a_cmd <= 0.0:
            new_speed = 0.0
        if state.speed_mps < 0.0 and new_speed > 0.0 and a_cmd >= 0.0:
            new_speed = 0.0

    new_yaw_rate = state.yaw_rate_rps + yaw_a * dt
    new_yaw = _wrap_angle(state.yaw_rad + new_yaw_rate * dt)

    vx = new_speed * math.cos(new_yaw) + env.drift_x_mps
    vy = new_speed * math.sin(new_yaw) + env.drift_y_mps

    return State(
        x_m=state.x_m + vx * dt,
        y_m=state.y_m + vy * dt,
        yaw_rad=new_yaw,
        speed_mps=new_speed,
        yaw_rate_rps=new_yaw_rate,
    )


def _latin_hypercube(n: int, dims: int, seed: int) -> np.ndarray:
    if n < 1 or dims < 1:
        raise ValueError("Latin hypercube dimensions must be positive")
    rng = np.random.default_rng(seed)
    out = np.empty((n, dims), dtype=float)
    for j in range(dims):
        perm = rng.permutation(n)
        out[:, j] = (perm + rng.random(n)) / n
    return out


def _interval(spec: Any, default: float) -> Tuple[float, float]:
    if spec is None:
        return default, default
    if isinstance(spec, (int, float)):
        x = float(spec)
        return x, x
    if isinstance(spec, dict):
        lo = float(spec.get("min", default))
        hi = float(spec.get("max", default))
        if hi < lo:
            raise ValueError("UNCERTAINTY_INTERVAL_REVERSED")
        return lo, hi
    raise TypeError("Uncertainty entries must be numbers or {min,max}")


def make_scenarios(base: Environment, uncertainty: Dict[str, Any], count: int, seed: int) -> List[Scenario]:
    count = int(count)
    if not (1 <= count <= 100_000):
        raise ValueError("scenario_count must be between 1 and 100000")
    u = _latin_hypercube(count, 5, seed)
    specs = [
        _interval(uncertainty.get("drag_per_s"), base.drag_per_s),
        _interval(uncertainty.get("rolling_loss_mps2"), base.rolling_loss_mps2),
        _interval(uncertainty.get("drift_x_mps"), base.drift_x_mps),
        _interval(uncertainty.get("drift_y_mps"), base.drift_y_mps),
        _interval(uncertainty.get("control_scale"), 1.0),
    ]
    rows: List[Scenario] = []
    for i in range(count):
        vals = [lo + (hi - lo) * u[i, j] for j, (lo, hi) in enumerate(specs)]
        rows.append(Scenario(i, max(0.0, vals[0]), max(0.0, vals[1]), vals[2], vals[3], vals[4]))
    return rows


def rollout_one(initial: State, control: Control, scenario: Scenario, dt_s: float, horizon_s: float) -> List[State]:
    steps = int(round(horizon_s / dt_s))
    if steps < 1:
        raise ValueError("horizon_s must cover at least one step")
    if abs(steps * dt_s - horizon_s) > 1e-9:
        raise ValueError("horizon_s must be an integer multiple of dt_s")
    env = Environment(scenario.drag_per_s, scenario.rolling_loss_mps2, scenario.drift_x_mps, scenario.drift_y_mps)
    s = initial
    out = [s]
    for _ in range(steps):
        s = step(s, control, env, dt_s, scenario.control_scale)
        out.append(s)
    return out


def _quantiles(values: Sequence[float]) -> Dict[str, float]:
    a = np.asarray(values, dtype=float)
    qs = np.quantile(a, [0.05, 0.25, 0.5, 0.75, 0.95])
    return {k: float(v) for k, v in zip(("q05", "q25", "q50", "q75", "q95"), qs)}


def rollout_cloud(cfg: Dict[str, Any]) -> Dict[str, Any]:
    _check_safe_purpose(cfg)
    initial = parse_state(cfg["initial_state"])
    control = parse_control(cfg.get("control", {}))
    env = parse_environment(cfg.get("environment", {}))
    dt_s = _finite("dt_s", cfg.get("dt_s", 0.02))
    horizon_s = _finite("horizon_s", cfg.get("horizon_s", 1.0))
    if horizon_s <= 0.0 or horizon_s > 300.0:
        raise ValueError("horizon_s must be in (0,300]")
    seed = int(cfg.get("seed", 0))
    count = int(cfg.get("scenario_count", 256))
    scenarios = make_scenarios(env, cfg.get("uncertainty", {}), count, seed)

    trajectories: List[Dict[str, Any]] = []
    endpoints: List[State] = []
    preserve_trajectories = bool(cfg.get("preserve_trajectories", True))

    for sc in scenarios:
        states = rollout_one(initial, control, sc, dt_s, horizon_s)
        endpoints.append(states[-1])
        rec: Dict[str, Any] = {
            "scenario": asdict(sc),
            "endpoint": asdict(states[-1]),
        }
        if preserve_trajectories:
            rec["trajectory"] = [asdict(s) for s in states]
        trajectories.append(rec)

    summary = {
        "x_m": _quantiles([s.x_m for s in endpoints]),
        "y_m": _quantiles([s.y_m for s in endpoints]),
        "yaw_rad": _quantiles([s.yaw_rad for s in endpoints]),
        "speed_mps": _quantiles([s.speed_mps for s in endpoints]),
        "yaw_rate_rps": _quantiles([s.yaw_rate_rps for s in endpoints]),
    }
    payload = {
        "schema": SCHEMA,
        "status": "MODEL_CONDITIONED_PREDICTION",
        "purpose": cfg.get("purpose", "benign physics rollout"),
        "input_sha256": _sha256_obj(cfg),
        "scenario_count": count,
        "seed": seed,
        "dt_s": dt_s,
        "horizon_s": horizon_s,
        "physics_baseline": "TOPA_PLANAR_MOBILE_KERNEL_V1",
        "learned_residual_applied": False,
        "prediction_is_observation": False,
        "endpoint_quantiles": summary,
        "scenarios": trajectories,
        "claim_ceiling": "MODEL_OUTPUT_IS_NOT_WORLD_TRUTH__VALIDATE_AGAINST_OBSERVATION",
    }
    payload["result_sha256"] = _sha256_obj(payload)
    return payload


def latency_compensate(cfg: Dict[str, Any]) -> Dict[str, Any]:
    _check_safe_purpose(cfg)
    latency = _finite("sensor_latency_s", cfg.get("sensor_latency_s", 0.0))
    if not (0.0 <= latency <= 10.0):
        raise ValueError("sensor_latency_s must be in [0,10]")
    if latency == 0.0:
        out = parse_state(cfg["initial_state"])
    else:
        local_cfg = dict(cfg)
        dt = min(_finite("dt_s", cfg.get("dt_s", 0.02)), latency)
        # choose a dt that exactly divides latency
        n = max(1, int(math.ceil(latency / dt)))
        dt = latency / n
        initial = parse_state(cfg["initial_state"])
        control = parse_control(cfg.get("control", {}))
        env = parse_environment(cfg.get("environment", {}))
        s = initial
        for _ in range(n):
            s = step(s, control, env, dt)
        out = s
    result = {
        "schema": SCHEMA,
        "status": "LATENCY_COMPENSATED_STATE_ESTIMATE",
        "sensor_latency_s": latency,
        "predicted_state": asdict(out),
        "prediction_is_observation": False,
        "input_sha256": _sha256_obj(cfg),
        "claim_ceiling": "LATENCY_COMPENSATION_IS_A_MODEL_ESTIMATE_NOT_A_SENSOR_MEASUREMENT",
    }
    result["result_sha256"] = _sha256_obj(result)
    return result


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise TypeError("config must be a JSON object")
    return obj


def _write_json(path: str | None, obj: Dict[str, Any]) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
    if path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def self_test() -> Dict[str, Any]:
    cfg = {
        "purpose": "warehouse mobile robot navigation latency simulation",
        "initial_state": {"x_m": 0, "y_m": 0, "yaw_rad": 0, "speed_mps": 1, "yaw_rate_rps": 0},
        "control": {"linear_accel_mps2": 0.1, "yaw_accel_rps2": 0.05},
        "environment": {"drag_per_s": 0.02, "rolling_loss_mps2": 0.01, "drift_x_mps": 0.0, "drift_y_mps": 0.0},
        "uncertainty": {
            "drag_per_s": {"min": 0.01, "max": 0.03},
            "rolling_loss_mps2": {"min": 0.0, "max": 0.02},
            "drift_x_mps": {"min": -0.02, "max": 0.02},
            "drift_y_mps": {"min": -0.02, "max": 0.02},
            "control_scale": {"min": 0.98, "max": 1.02}
        },
        "dt_s": 0.05,
        "horizon_s": 1.0,
        "scenario_count": 32,
        "seed": 42,
        "preserve_trajectories": False
    }
    a = rollout_cloud(cfg)
    b = rollout_cloud(cfg)
    assert a["result_sha256"] == b["result_sha256"]
    assert a["scenario_count"] == 32
    assert a["prediction_is_observation"] is False
    assert a["endpoint_quantiles"]["x_m"]["q95"] >= a["endpoint_quantiles"]["x_m"]["q05"]

    lat_cfg = dict(cfg)
    lat_cfg["sensor_latency_s"] = 0.2
    c = latency_compensate(lat_cfg)
    assert c["predicted_state"]["x_m"] > 0.0

    rejected = False
    try:
        bad = dict(cfg)
        bad["purpose"] = "ballistic targeting"
        rollout_cloud(bad)
    except ValueError as e:
        rejected = str(e).startswith("TOPA_WORLD_MODEL_SAFETY_REJECT")
    assert rejected

    return {
        "schema": "hawkar.topa.physics_world_model.self_test.v1",
        "status": "PASS",
        "deterministic_rollout": True,
        "uncertainty_cloud": True,
        "latency_compensation": True,
        "raw_physics_preserved": True,
        "weaponization_firewall": True,
        "scenario_count": 32,
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="TOPA safe physics world model")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")

    p_roll = sub.add_parser("rollout")
    p_roll.add_argument("config")
    p_roll.add_argument("--out")

    p_lat = sub.add_parser("latency-compensate")
    p_lat.add_argument("config")
    p_lat.add_argument("--out")

    args = ap.parse_args(argv)
    if args.cmd == "self-test":
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0
    cfg = _load_json(args.config)
    if args.cmd == "rollout":
        _write_json(args.out, rollout_cloud(cfg))
        return 0
    if args.cmd == "latency-compensate":
        _write_json(args.out, latency_compensate(cfg))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
