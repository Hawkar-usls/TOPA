#!/usr/bin/env python3
"""TOPA SPIDER — Keymaster pivot calibration relation microscope.

Reads frozen exact pivot feature rows produced by JANUS and searches for
relationships that may help Keymaster/Pivot-Slime order future exact checks.

Scientific firewall:
- correlations are diagnostic, not causal proof;
- two frozen formula families are not a universal law;
- local pivot numbers are provenance only and are NEVER transfer features;
- exact JANUS replay remains proof-state authority;
- P_VS_NP remains OPEN.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "TOPA/SPIDER/KEYMASTER-PIVOT-RELATIONS/v1.0.0"
P_VS_NP = "OPEN"

FEATURES = [
    "pos_mean_width",
    "neg_mean_width",
    "conflict_mass_per_pair",
    "same_sign_mass_per_pair",
    "support_overlap_mass_per_pair",
    "tautology_rate",
    "collision_rate_non_taut",
    "unique_resolvents",
    "unique_added",
    "subsumed_raw_clauses",
]
CHEAP_FEATURES = {
    "pos_mean_width",
    "neg_mean_width",
    "conflict_mass_per_pair",
    "same_sign_mass_per_pair",
    "support_overlap_mass_per_pair",
}
EXACT_INTERMEDIATE_FEATURES = set(FEATURES) - CHEAP_FEATURES


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tied_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = avg
        i = j
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    vx = sum(x*x for x in dx)
    vy = sum(y*y for y in dy)
    if vx <= 0 or vy <= 0:
        return None
    return sum(x*y for x, y in zip(dx, dy)) / math.sqrt(vx * vy)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    return pearson(tied_ranks(xs), tied_ranks(ys))


def correlations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    ys = [float(r["raw_units"]) for r in rows]
    for f in FEATURES:
        xs = [float(r[f]) for r in rows]
        rho = spearman(xs, ys)
        out[f] = {
            "spearman_vs_raw": rho,
            "feature_class": "CHEAP_PRE_PIVOT" if f in CHEAP_FEATURES else "EXACT_INTERMEDIATE",
            "constant_within_case": len(set(xs)) == 1,
        }
    return out


def mean(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(r[key]) for r in rows) / max(1, len(rows))


def threshold_contrast(rows: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    safe = [r for r in rows if int(r["raw_units"]) <= cap]
    over = [r for r in rows if int(r["raw_units"]) > cap]
    keys = [*FEATURES, "raw_units", "canonical_units"]
    deltas = {}
    if safe and over:
        for k in keys:
            ms = mean(safe, k)
            mo = mean(over, k)
            deltas[k] = {
                "safe_mean": ms,
                "overflow_mean": mo,
                "overflow_minus_safe": mo - ms,
            }
    return {
        "cap": cap,
        "safe_count": len(safe),
        "overflow_count": len(over),
        "safe_local_pivots": [r["pivot_id_local"] for r in safe],
        "overflow_local_pivots": [r["pivot_id_local"] for r in over],
        "local_ids_are_provenance_only": True,
        "feature_contrasts": deltas,
    }


def sign(x: float | None, eps: float = 1e-12) -> int | None:
    if x is None:
        return None
    return 1 if x > eps else (-1 if x < -eps else 0)


def build(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_case[str(r["case_id"])].append(r)

    cases = {}
    for case_id, case_rows in sorted(by_case.items()):
        cases[case_id] = {
            "rows": len(case_rows),
            "raw_range": [min(r["raw_units"] for r in case_rows), max(r["raw_units"] for r in case_rows)],
            "correlations": correlations(case_rows),
        }
        if case_id == "250x250-n8":
            cases[case_id]["stress_contrast_104_squared"] = threshold_contrast(case_rows, 104*104)
            cases[case_id]["stress_contrast_105_squared"] = threshold_contrast(case_rows, 105*105)

    cross = {}
    for f in FEATURES:
        per = {cid: cases[cid]["correlations"][f]["spearman_vs_raw"] for cid in cases}
        signs = [sign(v) for v in per.values() if v is not None and sign(v) != 0]
        cross[f] = {
            "per_case_spearman": per,
            "nonzero_sign_consistent": bool(signs) and len(set(signs)) == 1,
            "feature_class": "CHEAP_PRE_PIVOT" if f in CHEAP_FEATURES else "EXACT_INTERMEDIATE",
        }

    hypotheses = []

    # Exact intermediate: unique surviving resolvent diversity is closest to the
    # raw-cap mechanism itself.  Useful as a teacher target even though it is not
    # cheap enough to be the final pre-pivot feature.
    if cross["unique_added"]["nonzero_sign_consistent"]:
        hypotheses.append({
            "id": "H-UNIQUE-SURVIVING-RESOLVENT-MASS",
            "status": "TWO-WITNESS-REPLICATED-CANDIDATE__NOT_THEOREM",
            "relation": "More unique added resolvents tracks higher raw C025 cost in both frozen witness families.",
            "role": "Teacher/intermediate target: learn a cheap predictor for unique surviving resolver mass.",
            "proof_authority": False,
        })
    if cross["collision_rate_non_taut"]["nonzero_sign_consistent"]:
        hypotheses.append({
            "id": "H-COLLISION-PROTECTS-RAW-CAP",
            "status": "TWO-WITNESS-REPLICATED-CANDIDATE__NOT_THEOREM",
            "relation": "Higher non-tautological collision rate tracks lower raw cost in both frozen witness families.",
            "role": "Search for cheap pre-pivot proxies for resolvent collision probability.",
            "proof_authority": False,
        })

    # Explicitly record sign-instability rather than averaging it away.
    unstable = [f for f in FEATURES if not cross[f]["nonzero_sign_consistent"] and any(v is not None for v in cross[f]["per_case_spearman"].values())]
    hypotheses.append({
        "id": "NEG-SINGLE-FEATURE-MONOCULTURE",
        "status": "NEGATIVE-CALIBRATION-CERTIFICATE",
        "relation": "Some intuitive features change correlation sign between witness families; one-feature Keymaster rules are unsafe to generalize.",
        "sign_unstable_features": unstable,
        "proof_authority": False,
    })

    c250 = cases.get("250x250-n8", {})
    contrast = c250.get("stress_contrast_104_squared", {})
    if contrast.get("overflow_count"):
        hypotheses.append({
            "id": "H-RAW-BEFORE-CANONICAL-COMPRESSION",
            "status": "EXACT-LOCAL-MECHANISM",
            "relation": "At cap 104^2 the overflow pivots have larger raw cost even though their final canonical residual would be smaller. Therefore final canonical size cannot substitute for the monotone pre-subsumption raw-cap check.",
            "contrast": {
                "raw_units": contrast["feature_contrasts"].get("raw_units"),
                "canonical_units": contrast["feature_contrasts"].get("canonical_units"),
                "unique_added": contrast["feature_contrasts"].get("unique_added"),
                "collision_rate_non_taut": contrast["feature_contrasts"].get("collision_rate_non_taut"),
                "tautology_rate": contrast["feature_contrasts"].get("tautology_rate"),
            },
            "scope": "FROZEN_250x250_N8_WITNESS_AT_CAP_104_SQUARED",
            "proof_authority": False,
        })

    payload = {
        "schema": SCHEMA,
        "status": "PASS",
        "P_VS_NP": P_VS_NP,
        "rows": len(rows),
        "formula_families": len(cases),
        "cases": cases,
        "cross_witness_relations": cross,
        "hypotheses": hypotheses,
        "next_experiments": [
            "Generate multiple independently constructed canonical formulas per polarity scale; split holdout by formula fingerprint.",
            "Test whether cheap sign/support co-occurrence features can predict unique-added-resolvent mass before exact pair enumeration.",
            "Run ablations: Keymaster calibration only vs +M2R-PM vs +Pivot-Slime vs +TOPA-derived features.",
            "Preserve overflow examples near cap; they are more informative for route navigation than easy all-safe cases.",
            "Search counterexamples where high predicted collision still produces high raw cost because surviving resolvents are wider.",
        ],
        "laws": [
            "LOCAL_PIVOT_NUMBER_IS_NOT_A_TRANSFER_FEATURE",
            "CORRELATION_IS_NOT_CAUSATION",
            "TWO_WITNESSES_ARE_NOT_A_UNIVERSAL_LAW",
            "MODEL_RANKING_CANNOT_CHANGE_EXACT_VERDICT",
            "TOPA_RELATION_REQUIRES_HOLDOUT_OR_EXACT_COUNTEREXAMPLE_TEST",
            "P_VS_NP_IS_OPEN",
        ],
    }
    return payload


def self_test() -> None:
    rows = [
        {"case_id":"a","pivot_id_local":1,"raw_units":10,"canonical_units":5,
         "pos_mean_width":3,"neg_mean_width":3,"conflict_mass_per_pair":1,"same_sign_mass_per_pair":1,"support_overlap_mass_per_pair":2,
         "tautology_rate":.5,"collision_rate_non_taut":.8,"unique_resolvents":2,"unique_added":2,"subsumed_raw_clauses":1},
        {"case_id":"a","pivot_id_local":2,"raw_units":20,"canonical_units":6,
         "pos_mean_width":3,"neg_mean_width":3,"conflict_mass_per_pair":2,"same_sign_mass_per_pair":1,"support_overlap_mass_per_pair":3,
         "tautology_rate":.4,"collision_rate_non_taut":.4,"unique_resolvents":4,"unique_added":4,"subsumed_raw_clauses":2},
    ]
    p = build(rows)
    assert p["status"] == "PASS" and p["P_VS_NP"] == "OPEN"
    assert p["rows"] == 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["analyze", "self-test"])
    ap.add_argument("--input", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        print(json.dumps({"status":"PASS","P_VS_NP":P_VS_NP}))
        return 0
    if not args.input or not args.out:
        ap.error("analyze requires --input and --out")
    rows = load_jsonl(args.input)
    payload = build(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "rows": payload["rows"],
        "formula_families": payload["formula_families"],
        "hypotheses": [h["id"] for h in payload["hypotheses"]],
        "P_VS_NP": payload["P_VS_NP"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
