#!/usr/bin/env python3
"""TOPA Artifact Classifier v1.

A leakage-resistant image-forensics classifier harness for POSS-I candidates.
It consumes TOPA feature rails and a separate label rail, performs deterministic
plate/date-group out-of-fold evaluation, preserves all raw model score streams,
and can score a larger unlabelled population after OOF evaluation.

This classifier does NOT receive nuclear-event data and does NOT classify UAP,
NHI, causation or astrophysical transience. Its positive class means only
POINT_SOURCE_LIKE_IMAGE_EVIDENCE under the supplied label contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from topa_json_rails import JsonlWriter, iter_records, raw_sha256, write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "research/uap-nuclear/TOPA-ARTIFACT-FEATURE-REGISTRY-v1.0.json"
DEFAULT_MODELS = ["logistic_l2", "random_forest", "extra_trees", "hist_gradient_boosting"]

FORBIDDEN_EXACT = {
    "plate_id", "date_obs", "obs_date", "group_id", "nuclear_window",
    "nuclear_test", "nuclear_event", "harmonization_outcome", "effect_p_value",
    "uap", "nhi", "label", "target", "ground_truth",
}
FORBIDDEN_FRAGMENTS = (
    "nuclear_", "atomic_test", "bomb_test", "detonation_", "harmonization_",
    "uap_", "nhi_", "outcome_",
)


def _resolve(base_dir: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base_dir / p).resolve()


def _load_registry(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    return {f["name"]: f for f in obj.get("features", [])}, hashlib.sha256(raw).hexdigest()


def _guard_predictor(name: str) -> None:
    low = name.lower()
    if low in FORBIDDEN_EXACT or any(fragment in low for fragment in FORBIDDEN_FRAGMENTS):
        raise ValueError(f"forbidden classifier predictor {name!r}")


def _load_unique_records(path: Path, id_field: str = "candidate_id") -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    ordered = []
    by_id = {}
    for row in iter_records(path):
        if not isinstance(row, dict):
            raise ValueError(f"{path}: expected JSON object records")
        cid = str(row.get(id_field, "")).strip()
        if not cid:
            raise ValueError(f"{path}: record missing {id_field}")
        if cid in by_id:
            raise ValueError(f"{path}: duplicate {id_field}={cid}")
        by_id[cid] = row
        ordered.append(row)
    return ordered, by_id


def _fold_for_group(group_id: str, folds: int, seed: int) -> int:
    digest = hashlib.sha256(f"TOPA|{seed}|{group_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % folds


def _feature_matrix(rows: list[dict[str, Any]], feature_names: list[str]) -> tuple[np.ndarray, dict[str, float]]:
    X = np.full((len(rows), len(feature_names)), np.nan, dtype=np.float64)
    missing = Counter()
    for i, row in enumerate(rows):
        feats = row.get("features") or {}
        if not isinstance(feats, dict):
            raise ValueError(f"candidate {row.get('candidate_id')}: features must be an object")
        for j, name in enumerate(feature_names):
            value = feats.get(name)
            if value is None or value == "":
                missing[name] += 1
                continue
            if isinstance(value, bool):
                X[i, j] = float(value)
                continue
            try:
                x = float(value)
            except Exception as exc:
                raise ValueError(f"candidate {row.get('candidate_id')}: nonnumeric feature {name}={value!r}") from exc
            if not math.isfinite(x):
                raise ValueError(f"candidate {row.get('candidate_id')}: non-finite feature {name}")
            X[i, j] = x
    return X, {name: missing[name] / max(1, len(rows)) for name in feature_names}


def _make_model(name: str, random_state: int, quick: bool = False):
    trees = 60 if quick else 400
    if name == "logistic_l2":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(
                penalty="l2", C=1.0, class_weight="balanced", max_iter=2000,
                solver="lbfgs", random_state=random_state,
            )),
        ])
    if name == "random_forest":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("model", RandomForestClassifier(
                n_estimators=trees, min_samples_leaf=2, max_features="sqrt",
                class_weight="balanced_subsample", n_jobs=-1, random_state=random_state,
            )),
        ])
    if name == "extra_trees":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("model", ExtraTreesClassifier(
                n_estimators=trees, min_samples_leaf=2, max_features="sqrt",
                class_weight="balanced", n_jobs=-1, random_state=random_state,
            )),
        ])
    if name == "hist_gradient_boosting":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("model", HistGradientBoostingClassifier(
                learning_rate=0.05, max_iter=100 if quick else 300,
                max_leaf_nodes=31, l2_regularization=1.0,
                class_weight="balanced", random_state=random_state,
            )),
        ])
    raise ValueError(f"unknown model {name!r}")


def _score_distribution(values: np.ndarray) -> dict[str, Any]:
    x = np.asarray(values, dtype=float)
    if x.size == 0:
        return {"n": 0}
    rounded = np.round(x, 6)
    counts = Counter(float(v) for v in rounded)
    quantiles = {str(q): float(np.quantile(x, q)) for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)}
    unique = len(counts)
    max_bucket = max(counts.values()) / len(x)
    sd = float(np.std(x))
    collapse_warning = bool(
        sd < 1e-6 or unique < max(10, int(math.ceil(0.02 * len(x)))) or max_bucket > 0.50
    )
    return {
        "n": int(len(x)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "mean": float(np.mean(x)),
        "population_sd": sd,
        "quantiles": quantiles,
        "unique_rounded_1e-6": unique,
        "largest_rounded_bucket_fraction": max_bucket,
        "distribution_collapse_warning": collapse_warning,
        "semantic_note": "RAW_ENSEMBLE_RANKING_SCORE__NOT_CALIBRATED_PROBABILITY",
    }


def _reliability_table(y: np.ndarray, score: np.ndarray, bins: int = 10) -> list[dict[str, Any]]:
    out = []
    edges = np.linspace(0.0, 1.0, bins + 1)
    for i in range(bins):
        lo, hi = float(edges[i]), float(edges[i + 1])
        if i == bins - 1:
            mask = (score >= lo) & (score <= hi)
        else:
            mask = (score >= lo) & (score < hi)
        n = int(mask.sum())
        out.append({
            "lo": lo, "hi": hi, "n": n,
            "mean_raw_score": float(np.mean(score[mask])) if n else None,
            "positive_label_fraction": float(np.mean(y[mask])) if n else None,
        })
    return out


def _metrics(y: np.ndarray, score: np.ndarray) -> dict[str, Any]:
    if len(set(int(v) for v in y)) < 2:
        return {"status": "UNDEFINED_SINGLE_CLASS"}
    pred = (score >= 0.5).astype(int)
    return {
        "status": "OK",
        "roc_auc": float(roc_auc_score(y, score)),
        "average_precision": float(average_precision_score(y, score)),
        "balanced_accuracy_at_0p5": float(balanced_accuracy_score(y, pred)),
        "brier_raw_score_diagnostic": float(brier_score_loss(y, score)),
        "brier_note": "Diagnostic only; raw scores are not asserted to be calibrated probabilities.",
        "reliability_table_raw_score": _reliability_table(y, score),
    }


def _input_label_census(labels: list[dict[str, Any]]) -> dict[str, Any]:
    tiers = Counter(str(x.get("label_tier", "MISSING")) for x in labels)
    sources = Counter(str(x.get("label_source", "MISSING")) for x in labels)
    classes = Counter(int(x["label"]) for x in labels)
    witness = Counter()
    for x in labels:
        for fam in x.get("witness_families", []) or []:
            witness[str(fam)] += 1
    return {
        "classes": {str(k): int(v) for k, v in sorted(classes.items())},
        "tiers": dict(sorted(tiers.items())),
        "sources": dict(sorted(sources.items())),
        "witness_families": dict(sorted(witness.items())),
    }


def train(config: dict[str, Any], *, base_dir: Path = Path.cwd()) -> dict[str, Any]:
    feature_path = _resolve(base_dir, config["feature_path"])
    label_path = _resolve(base_dir, config["label_path"])
    registry_path = _resolve(base_dir, config.get("feature_registry_path", DEFAULT_REGISTRY))
    registry, registry_sha = _load_registry(registry_path)

    feature_rows_all, feature_by_id = _load_unique_records(feature_path)
    label_rows, label_by_id = _load_unique_records(label_path)
    if not label_rows:
        raise ValueError("no labels supplied")

    selected = list(config.get("feature_names", []))
    if not selected:
        observed = set()
        for row in feature_rows_all:
            observed.update((row.get("features") or {}).keys())
        selected = [name for name, meta in registry.items() if meta.get("default_predictor", False) and name in observed]
    if not selected:
        raise ValueError("no predictor features selected")
    if len(selected) != len(set(selected)):
        raise ValueError("duplicate feature names in model config")
    for name in selected:
        _guard_predictor(name)
        if name not in registry:
            raise ValueError(f"unregistered feature {name!r}")

    selected_families = {registry[name]["family"] for name in selected}
    witness_families = set()
    for lr in label_rows:
        for fam in lr.get("witness_families", []) or []:
            witness_families.add(str(fam))
    overlap = sorted(selected_families & witness_families)
    if overlap and not config.get("allow_witness_family_overlap", False):
        raise ValueError(
            "target-leakage guard: predictor families also created labels: " + ", ".join(overlap)
        )

    tiers = {str(x.get("label_tier", "")) for x in label_rows}
    if tiers and tiers <= {"C"} and not config.get("allow_tier_c_only", False):
        raise ValueError("primary training cannot use only Tier-C heuristic labels")

    training_rows = []
    training_labels = []
    label_meta = []
    missing_label_features = 0
    for lr in label_rows:
        cid = str(lr["candidate_id"])
        fr = feature_by_id.get(cid)
        if fr is None:
            missing_label_features += 1
            continue
        label = int(lr["label"])
        if label not in (0, 1):
            raise ValueError(f"candidate {cid}: label must be 0 or 1")
        group = str(fr.get("group_id", "")).strip()
        if not group:
            raise ValueError(f"candidate {cid}: group_id missing from feature rail")
        training_rows.append(fr)
        training_labels.append(label)
        label_meta.append(lr)
    if missing_label_features and config.get("require_all_labels_in_feature_rail", True):
        raise ValueError(f"{missing_label_features} label rows have no matching feature row")
    if len(training_rows) < 20:
        raise ValueError("too few labelled rows; need at least 20 for v1 harness")
    y = np.asarray(training_labels, dtype=np.int64)
    if set(y.tolist()) != {0, 1}:
        raise ValueError("both label classes are required")

    X, missing_rates = _feature_matrix(training_rows, selected)
    folds = int(config.get("folds", 5))
    seed = int(config.get("seed", 20260827))
    if folds < 2:
        raise ValueError("folds must be >=2")
    groups = [str(r["group_id"]) for r in training_rows]
    unique_groups = set(groups)
    if len(unique_groups) < folds * 2:
        raise ValueError(f"too few independent groups ({len(unique_groups)}) for {folds} folds")
    fold_idx = np.asarray([_fold_for_group(g, folds, seed) for g in groups], dtype=np.int64)
    model_names = list(config.get("models", DEFAULT_MODELS))
    if not model_names:
        raise ValueError("no models configured")
    quick = bool(config.get("quick_mode", False))

    model_oof = {name: np.full(len(y), np.nan, dtype=float) for name in model_names}
    fold_receipts = []
    for fold in range(folds):
        test = np.flatnonzero(fold_idx == fold)
        train_idx = np.flatnonzero(fold_idx != fold)
        if len(test) == 0:
            raise ValueError(f"deterministic group fold {fold} is empty")
        if len(set(y[train_idx].tolist())) < 2 or len(set(y[test].tolist())) < 2:
            raise ValueError(f"fold {fold} lacks both classes in train/test; adjust labels or fold count before proceeding")
        fold_model_metrics = {}
        for mi, name in enumerate(model_names):
            model = _make_model(name, seed + fold * 100 + mi, quick=quick)
            model.fit(X[train_idx], y[train_idx])
            score = model.predict_proba(X[test])[:, 1]
            if np.any(~np.isfinite(score)) or np.any((score < 0) | (score > 1)):
                raise ValueError(f"model {name} fold {fold} emitted invalid scores")
            model_oof[name][test] = score
            fold_model_metrics[name] = _metrics(y[test], score)
        fold_receipts.append({
            "fold": fold,
            "test_rows": int(len(test)),
            "train_rows": int(len(train_idx)),
            "test_groups": int(len({groups[i] for i in test})),
            "train_groups": int(len({groups[i] for i in train_idx})),
            "test_class_census": {str(k): int(v) for k, v in sorted(Counter(y[test].tolist()).items())},
            "models": fold_model_metrics,
        })

    for name, scores in model_oof.items():
        if np.any(~np.isfinite(scores)):
            raise ValueError(f"model {name}: not every labelled row received exactly one OOF score")
    ensemble = np.mean(np.column_stack([model_oof[n] for n in model_names]), axis=1)
    if np.any(~np.isfinite(ensemble)):
        raise ValueError("ensemble contains non-finite values")

    model_metrics = {name: _metrics(y, model_oof[name]) for name in model_names}
    ensemble_metrics = _metrics(y, ensemble)
    distribution = _score_distribution(ensemble)

    oof_path = _resolve(base_dir, config["oof_scores_path"])
    oof_path.parent.mkdir(parents=True, exist_ok=True)
    with JsonlWriter(oof_path) as writer:
        for i, fr in enumerate(training_rows):
            writer.write({
                "schema": "hawkar.topa.artifact_score_row.v1",
                "candidate_id": fr["candidate_id"],
                "plate_id": fr.get("plate_id"),
                "date_obs": fr.get("date_obs"),
                "group_id": fr.get("group_id"),
                "fold": int(fold_idx[i]),
                "label": int(y[i]),
                "label_tier": label_meta[i].get("label_tier"),
                "label_source": label_meta[i].get("label_source"),
                "candidate_quality_score_raw": float(ensemble[i]),
                "artifact_likelihood_raw": float(1.0 - ensemble[i]),
                "model_scores_raw": {name: float(model_oof[name][i]) for name in model_names},
                "score_origin": "DETERMINISTIC_GROUP_OOF",
                "score_semantics": "UNCALIBRATED_ENSEMBLE_RANKING_SCORE__NOT_A_PHYSICAL_PROBABILITY",
            })

    model_dir = _resolve(base_dir, config["model_dir"])
    model_dir.mkdir(parents=True, exist_ok=True)
    model_files = {}
    for mi, name in enumerate(model_names):
        model = _make_model(name, seed + 9000 + mi, quick=quick)
        model.fit(X, y)
        path = model_dir / f"{name}.joblib"
        joblib.dump(model, path)
        model_files[name] = {"path": path.name, "raw_sha256": raw_sha256(path)}

    manifest = {
        "schema": "hawkar.topa.artifact_model_bundle.v1",
        "status": "TRAINED_AFTER_GROUP_OOF_EVALUATION",
        "feature_names": selected,
        "feature_families": sorted(selected_families),
        "model_names": model_names,
        "model_files": model_files,
        "seed": seed,
        "folds": folds,
        "quick_mode": quick,
        "feature_registry_raw_sha256": registry_sha,
        "training_feature_file_raw_sha256": raw_sha256(feature_path),
        "training_label_file_raw_sha256": raw_sha256(label_path),
        "score_semantics": "UNCALIBRATED_CLASS1_RANKING_SCORE",
        "calibration": "NOT_PERFORMED",
    }
    manifest_path = model_dir / "model_manifest.json"
    write_json_atomic(manifest_path, manifest)

    receipt = {
        "schema": "hawkar.topa.artifact_classifier_training_receipt.v1",
        "status": "PASS",
        "claim_ceiling": "IMAGE_FORENSICS_CLASSIFICATION_PERFORMANCE_ON_SUPPLIED_LABEL_CONTRACT_ONLY",
        "training_rows": int(len(y)),
        "independent_groups": int(len(unique_groups)),
        "folds": folds,
        "deterministic_group_hash_split": True,
        "same_group_train_test_allowed": False,
        "feature_names": selected,
        "feature_families": sorted(selected_families),
        "feature_missing_fraction": missing_rates,
        "label_census": _input_label_census(label_meta),
        "label_rows_without_feature_row": missing_label_features,
        "witness_feature_family_overlap": overlap,
        "witness_overlap_allowed": bool(config.get("allow_witness_family_overlap", False)),
        "models": model_metrics,
        "ensemble_group_oof": ensemble_metrics,
        "fold_receipts": fold_receipts,
        "raw_score_distribution": distribution,
        "oof_scores_path": str(oof_path),
        "oof_scores_raw_sha256": raw_sha256(oof_path),
        "model_dir": str(model_dir),
        "model_manifest_raw_sha256": raw_sha256(manifest_path),
        "feature_registry_path": str(registry_path),
        "feature_registry_raw_sha256": registry_sha,
        "input_hashes": {
            "features": raw_sha256(feature_path),
            "labels": raw_sha256(label_path),
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "calibration": {
            "performed": False,
            "raw_score_overwritten": False,
            "note": "Any future calibration must be a sidecar view and cannot replace these OOF raw scores.",
        },
        "nuclear_calendar_loaded": False,
        "uap_or_nhi_target_used": False,
    }
    receipt_path = config.get("training_receipt_path")
    if receipt_path:
        write_json_atomic(_resolve(base_dir, receipt_path), receipt)
    return receipt


def score_population(config: dict[str, Any], *, base_dir: Path = Path.cwd()) -> dict[str, Any]:
    feature_path = _resolve(base_dir, config["feature_path"])
    model_dir = _resolve(base_dir, config["model_dir"])
    manifest_path = model_dir / "model_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    feature_names = list(manifest["feature_names"])
    model_names = list(manifest["model_names"])
    rows, _ = _load_unique_records(feature_path)
    X, missing_rates = _feature_matrix(rows, feature_names)

    model_scores = {}
    for name in model_names:
        spec = manifest["model_files"][name]
        path = model_dir / spec["path"]
        got = raw_sha256(path)
        if got != spec["raw_sha256"]:
            raise ValueError(f"model file hash mismatch for {name}: {got} != {spec['raw_sha256']}")
        model = joblib.load(path)
        score = model.predict_proba(X)[:, 1]
        if np.any(~np.isfinite(score)) or np.any((score < 0) | (score > 1)):
            raise ValueError(f"model {name} emitted invalid full-population scores")
        model_scores[name] = score
    ensemble = np.mean(np.column_stack([model_scores[n] for n in model_names]), axis=1)

    oof_map = {}
    oof_path_value = config.get("oof_scores_path")
    if oof_path_value:
        oof_path = _resolve(base_dir, oof_path_value)
        for row in iter_records(oof_path):
            cid = str(row["candidate_id"])
            if cid in oof_map:
                raise ValueError(f"duplicate OOF score candidate {cid}")
            oof_map[cid] = row

    out_path = _resolve(base_dir, config["output_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final_scores = np.empty(len(rows), dtype=float)
    replaced = 0
    with JsonlWriter(out_path) as writer:
        for i, fr in enumerate(rows):
            cid = str(fr["candidate_id"])
            if cid in oof_map:
                oo = oof_map[cid]
                quality = float(oo["candidate_quality_score_raw"])
                member = {k: float(v) for k, v in (oo.get("model_scores_raw") or {}).items()}
                origin = "GROUP_OOF_REUSED_FOR_TRAINING_ROW"
                replaced += 1
            else:
                quality = float(ensemble[i])
                member = {name: float(model_scores[name][i]) for name in model_names}
                origin = "FULL_TRAINING_SET_MODEL_INFERENCE"
            final_scores[i] = quality
            writer.write({
                "schema": "hawkar.topa.artifact_score_row.v1",
                "candidate_id": cid,
                "plate_id": fr.get("plate_id"),
                "date_obs": fr.get("date_obs"),
                "group_id": fr.get("group_id"),
                "candidate_quality_score_raw": quality,
                "artifact_likelihood_raw": float(1.0 - quality),
                "model_scores_raw": member,
                "score_origin": origin,
                "score_semantics": "UNCALIBRATED_ENSEMBLE_RANKING_SCORE__NOT_A_PHYSICAL_PROBABILITY",
            })

    receipt = {
        "schema": "hawkar.topa.artifact_population_scoring_receipt.v1",
        "status": "PASS",
        "population_rows": len(rows),
        "training_rows_replaced_with_group_oof_scores": replaced,
        "full_model_inference_rows": len(rows) - replaced,
        "feature_names": feature_names,
        "feature_missing_fraction": missing_rates,
        "raw_score_distribution": _score_distribution(final_scores),
        "output_path": str(out_path),
        "output_raw_sha256": raw_sha256(out_path),
        "model_manifest_raw_sha256": raw_sha256(manifest_path),
        "feature_file_raw_sha256": raw_sha256(feature_path),
        "calibration_performed": False,
        "raw_score_overwritten": False,
        "harmonization_ready": True,
        "harmonization_score_field": "candidate_quality_score_raw",
        "harmonization_date_field": "date_obs",
        "claim_ceiling": "IMAGE_FORENSICS_SCORE_STREAM_ONLY",
    }
    receipt_path = config.get("scoring_receipt_path")
    if receipt_path:
        write_json_atomic(_resolve(base_dir, receipt_path), receipt)
    return receipt


def self_test() -> dict[str, Any]:
    from topa_poss1_harmonization import run_config as harmonize

    with tempfile.TemporaryDirectory(prefix="topa-artifact-classifier-") as td:
        root = Path(td)
        features = root / "features.jsonl.gz"
        labels = root / "labels.ndjson.bz2"
        rng = np.random.default_rng(20260827)
        n_groups = 60
        per_group = 10
        with JsonlWriter(features) as fw, JsonlWriter(labels) as lw:
            for g in range(n_groups):
                plate = f"P{g:03d}"
                date_obs = f"1950-01-{(g % 28)+1:02d}"
                gid = hashlib.sha256(f"{plate}|{date_obs}".encode()).hexdigest()[:24]
                group_bias = rng.normal(0, 0.25)
                for j in range(per_group):
                    cid = f"{plate}-{j:02d}"
                    fwhm = float(rng.normal(1.05, 0.22))
                    spread = float(rng.normal(1.2, 2.0))
                    edge = float(rng.uniform(0.5, 120.0))
                    wcs = float(abs(rng.normal(0.4, 0.25)))
                    logit = 2.0 - 2.7*(fwhm-1.0) - 0.35*spread + 0.006*edge - 0.8*wcs + group_bias
                    prob = 1/(1+math.exp(-logit))
                    label = int(rng.random() < prob)
                    fw.write({
                        "schema":"hawkar.topa.artifact_feature_row.v1",
                        "candidate_id":cid,"tile_id":f"T{g:03d}","plate_id":plate,
                        "date_obs":date_obs,"group_id":gid,"ra_deg":10+g/10,"dec_deg":20+j/10,
                        "features":{
                            "morph_fwhm_ratio":fwhm,
                            "morph_spread_snr":spread,
                            "geo_edge_dist_arcmin":edge,
                            "acq_wcs_offset_arcsec":wcs,
                        },
                        "source_presence":{"synthetic":True},
                        "feature_families_present":["morphology_psf","plate_geometry","acquisition_provenance"],
                    })
                    lw.write({
                        "candidate_id":cid,"label":label,"label_tier":"A",
                        "label_source":"SYNTHETIC_SELF_TEST","witness_families":[]
                    })
        model_dir = root / "models"
        oof = root / "oof.jsonl.gz"
        train_receipt = train({
            "feature_path":str(features),"label_path":str(labels),
            "feature_registry_path":str(DEFAULT_REGISTRY),
            "feature_names":["morph_fwhm_ratio","morph_spread_snr","geo_edge_dist_arcmin","acq_wcs_offset_arcsec"],
            "folds":3,"seed":20260827,"quick_mode":True,
            "models":DEFAULT_MODELS,
            "oof_scores_path":str(oof),"model_dir":str(model_dir),
        }, base_dir=root)
        auc = float(train_receipt["ensemble_group_oof"]["roc_auc"])
        if auc < 0.65:
            raise AssertionError(f"synthetic self-test OOF AUC unexpectedly low: {auc}")
        scored = root / "scored.jsonl.gz"
        score_receipt = score_population({
            "feature_path":str(features),"model_dir":str(model_dir),
            "oof_scores_path":str(oof),"output_path":str(scored),
        }, base_dir=root)
        assert score_receipt["population_rows"] == n_groups * per_group
        assert score_receipt["training_rows_replaced_with_group_oof_scores"] == n_groups * per_group

        nuclear = root / "nuclear.jsonl.gz"
        opportunity = root / "opportunity.jsonl.gz"
        with JsonlWriter(nuclear) as w:
            w.write({"date":"1950-01-10"})
        with JsonlWriter(opportunity) as w:
            for d in range(1, 29):
                w.write({"date_obs":f"1950-01-{d:02d}","opportunity":100.0})
        harm = harmonize({
            "experiment_id":"TOPA_ARTIFACT_CLASSIFIER_SELF_TEST_HANDOFF",
            "study_start":"1950-01-01","study_end":"1950-01-28","nuclear_window_days":1,
            "nuclear_manifest_path":str(nuclear),"nuclear_date_field":"date",
            "cohorts":[{
                "id":"SYNTHETIC","candidates_path":str(scored),"opportunity_path":str(opportunity),
                "candidate_date_field":"date_obs","raw_score_field":"candidate_quality_score_raw",
                "opportunity_date_field":"date_obs","opportunity_field":"opportunity",
            }]
        })
        assert harm["status"] == "EXECUTED_ON_SUPPLIED_COHORTS"
        return {
            "schema":"hawkar.topa.artifact_classifier.self_test.v1",
            "status":"PASS",
            "synthetic_rows":n_groups*per_group,
            "independent_groups":n_groups,
            "group_oof_auc":auc,
            "models":DEFAULT_MODELS,
            "raw_distribution_preserved":True,
            "oof_replacement_path_tested":True,
            "harmonization_handoff_tested":True,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="TOPA Artifact Classifier")
    sp = ap.add_subparsers(dest="cmd", required=True)
    tr = sp.add_parser("train"); tr.add_argument("config")
    sc = sp.add_parser("score"); sc.add_argument("config")
    sp.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        result = self_test()
    else:
        cfg_path = Path(args.config).resolve()
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
        result = train(config, base_dir=cfg_path.parent) if args.cmd == "train" else score_population(config, base_dir=cfg_path.parent)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
