#!/usr/bin/env python3
"""TOPA v25.4 geographic mirror null replay.

Retrospective falsification only. The historical pair was known before this
operator was formalized, so this script MUST NOT be described as prospective
discovery evidence.
"""
from __future__ import annotations

import json
import math
import numpy as np

R_KM = 6371.0088
A = (38.7500, -104.7667)  # Colorado_NORAD
B = (61.7833, 34.3500)    # Petrozavodsk_RU
N = 2_000_000


def wrap_lon(lon_deg: float) -> float:
    return ((lon_deg + 180.0) % 360.0) - 180.0


def great_circle_km(a, b) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = math.radians(wrap_lon(math.degrees(lon2 - lon1)))
    h = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )
    return 2.0 * R_KM * math.asin(min(1.0, math.sqrt(h)))


def m58(point):
    lat, lon = point
    return (2.0 * 58.0 - lat, lon)


def mantipode(point):
    lat, lon = point
    return (-lat, wrap_lon(lon + 180.0))


def null_once(center, observed_radius_km, seed: int, northern: bool):
    rng = np.random.default_rng(seed)
    # IMPORTANT: draw all latitude variates first, then all longitude variates.
    # This sampling order is frozen so the exact Monte Carlo receipt replays.
    u = rng.uniform(0.0, 1.0, N) if northern else rng.uniform(-1.0, 1.0, N)
    lat = np.arcsin(u)
    lon = rng.uniform(-math.pi, math.pi, N)

    clat = math.radians(center[0])
    clon = math.radians(center[1])
    cosd = (
        math.sin(clat) * np.sin(lat)
        + math.cos(clat) * np.cos(lat) * np.cos(lon - clon)
    )
    d = R_KM * np.arccos(np.clip(cosd, -1.0, 1.0))
    count = int(np.sum(d <= observed_radius_km))
    p = count / N
    se = math.sqrt(p * (1.0 - p) / N)
    return {"N": N, "seed": seed, "count_le_observed": count, "empirical_p": p, "mc_se": se}


def analytic_global_cap_p(radius_km: float) -> float:
    theta = radius_km / R_KM
    return (1.0 - math.cos(theta)) / 2.0


def main():
    p58 = m58(A)
    d58 = great_circle_km(p58, B)
    pant = mantipode(A)
    dant = great_circle_km(pant, B)

    out = {
        "registration_class": "RETROSPECTIVE_FORMALIZATION_FOR_FALSIFICATION__NOT_PROSPECTIVE_DISCOVERY",
        "earth_radius_km": R_KM,
        "historical_pair": {"A": A, "B": B},
        "literal_58_reflection": {
            "mirrored_A": p58,
            "residual_km": d58,
            "global_uniform_sphere": null_once(p58, d58, 20260826, False),
            "northern_hemisphere": null_once(p58, d58, 20260827, True),
            "analytic_global_cap_p_check": analytic_global_cap_p(d58),
        },
        "antipodal_negative_control": {
            "mirrored_A": pant,
            "residual_km": dant,
            "global_uniform_sphere": null_once(pant, dant, 20260828, False),
            "northern_hemisphere": null_once(pant, dant, 20260829, True),
            "analytic_global_cap_p_check": analytic_global_cap_p(dant),
        },
        "decision": {
            "alpha": 0.05,
            "literal_58": "FAIL",
            "antipodal_control": "FAIL",
            "operator_shopping_after_result": "FORBIDDEN",
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
