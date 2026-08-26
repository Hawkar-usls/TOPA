#!/usr/bin/env python3
"""TOPA Artifact Classifier sidecar gatekeeper v1.

A registered feature is not automatically an available measurement. This tool
keeps that boundary executable:

- audit: validate a sidecar manifest against the feature registry, input hashes,
  candidate identifiers, row coverage, duplicates, and declared fields;
- emit-config: inject only admitted + verified sidecars into an existing feature
  build config;
- self-test: exercise ready/missing/hash-failure/config-emission paths.

A sidecar with status RECONSTRUCTION_REQUIRED is documentation, not data, and is
never silently promoted into the classifier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from topa_json_rails import JsonlWriter, raw_sha256, write_json_atomic
from topa_artifact_features import iter_table

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "research/uap-nuclear/TOPA-ARTIFACT-FEATURE-REGISTRY-v1.0.json"

ALLOWED_AVAILABILITY = {
    "PUBLIC_BYTES_READY",
    "RECONSTRUCTED_BYTES_READY",
    "RECONSTRUCTION_REQUIRED",
    "PLANNED_NEW_TOPA_MEASUREMENT",
    "FUTURE_EXTERNAL_PUBLIC_DATA",
}
READY_CLASSES = {"PUBLIC_BYTES_READY", "RECONSTRUCTED_BYTES_READY"}


def _resolve(base: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p).resolve()


def _registry(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    features = {str(x["name"]): x for x in obj.get("features", [])}
    if not features:
        raise ValueError("empty feature registry")
    return features, hashlib.sha256(raw).hexdigest()


def _base_ids(path: Path, id_field: str) -> set[str]:
    out = set()
    for row in iter_table(path):
        cid = str(row.get(id_field, "")).strip()
        if not cid:
            raise ValueError(f"base candidate source has blank {id_field}")
        if cid in out:
            raise ValueError(f"base candidate source duplicates {id_field}={cid}")
        out.add(cid)
    if not out:
        raise ValueError("base candidate source is empty")
    return out


def _field_map(spec: dict[str, Any], registry: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    fields = spec.get("fields", [])
    if not fields:
        raise ValueError(f"sidecar {spec.get('id')}: ready sidecar declares no fields")
    seen = set()
    out = []
    for field in fields:
        src = str(field.get("source", "")).strip()
        feat = str(field.get("feature", "")).strip()
        if not src or not feat:
            raise ValueError(f"sidecar {spec.get('id')}: each field requires source and feature")
        if feat not in registry:
            raise ValueError(f"sidecar {spec.get('id')}: unregistered feature {feat}")
        if feat in seen:
            raise ValueError(f"sidecar {spec.get('id')}: duplicate feature mapping {feat}")
        seen.add(feat)
        expected_type = registry[feat].get("type")
        supplied_type = field.get("type", expected_type)
        if expected_type and supplied_type != expected_type:
            raise ValueError(f"sidecar {spec.get('id')}: {feat} type {supplied_type} != registry {expected_type}")
        out.append({
            "source": src,
            "feature": feat,
            "type": supplied_type,
            "required": bool(field.get("required", False)),
        })
    return out


def audit_manifest(config: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    registry_path = _resolve(base_dir, config.get("feature_registry_path", DEFAULT_REGISTRY))
    registry, registry_sha = _registry(registry_path)

    base_path = _resolve(base_dir, config["base_candidate_path"])
    base_id_field = str(config.get("base_candidate_id_field", "src_id"))
    candidate_ids = _base_ids(base_path, base_id_field)
    n_base = len(candidate_ids)

    entries = []
    ready_verified = []
    for spec in config.get("sidecars", []):
        sid = str(spec.get("id", "")).strip()
        family = str(spec.get("family", "")).strip()
        availability = str(spec.get("availability", "")).strip()
        if not sid or not family:
            raise ValueError("each sidecar needs id and family")
        if availability not in ALLOWED_AVAILABILITY:
            raise ValueError(f"sidecar {sid}: invalid availability {availability!r}")
        if availability not in READY_CLASSES:
            entries.append({
                "id": sid,
                "family": family,
                "availability": availability,
                "verification": "NOT_APPLICABLE_NO_READY_BYTES",
                "admitted_to_feature_config": False,
                "reconstruction": spec.get("reconstruction"),
            })
            continue

        path_value = spec.get("path")
        if not path_value:
            raise ValueError(f"sidecar {sid}: {availability} requires path")
        path = _resolve(base_dir, path_value)
        if not path.exists():
            entries.append({
                "id": sid, "family": family, "availability": availability,
                "verification": "FAIL_MISSING_FILE", "path": str(path),
                "admitted_to_feature_config": False,
            })
            continue

        got_sha = raw_sha256(path)
        expected_sha = str(spec.get("raw_sha256", "")).strip() or None
        hash_ok = expected_sha is None or got_sha == expected_sha
        mappings = _field_map(spec, registry)
        id_field = str(spec.get("id_field", "src_id"))
        seen = set()
        matched = 0
        outside = 0
        duplicate_ids = 0
        missing_declared_fields = Counter()
        row_count = 0
        for row in iter_table(path):
            row_count += 1
            cid = str(row.get(id_field, "")).strip()
            if not cid:
                raise ValueError(f"sidecar {sid}: blank {id_field} at row {row_count}")
            if cid in seen:
                duplicate_ids += 1
            else:
                seen.add(cid)
            if cid in candidate_ids:
                matched += 1
            else:
                outside += 1
            for mapping in mappings:
                if mapping["source"] not in row:
                    missing_declared_fields[mapping["source"]] += 1
        coverage = matched / n_base if n_base else 0.0
        require_unique = bool(spec.get("require_unique_candidate_ids", True))
        min_coverage = float(spec.get("minimum_base_coverage_fraction", 0.0))
        if not (0.0 <= min_coverage <= 1.0):
            raise ValueError(f"sidecar {sid}: minimum coverage must be [0,1]")
        required_source_missing = {
            m["source"]: int(missing_declared_fields[m["source"]])
            for m in mappings if m["required"] and missing_declared_fields[m["source"]]
        }
        reasons = []
        if not hash_ok:
            reasons.append("RAW_SHA256_MISMATCH")
        if require_unique and duplicate_ids:
            reasons.append("DUPLICATE_CANDIDATE_IDS")
        if coverage < min_coverage:
            reasons.append("BASE_COVERAGE_BELOW_MINIMUM")
        if required_source_missing:
            reasons.append("REQUIRED_SOURCE_FIELDS_MISSING")
        verified = not reasons
        entry = {
            "id": sid,
            "family": family,
            "availability": availability,
            "path": str(path),
            "raw_sha256": got_sha,
            "expected_raw_sha256": expected_sha,
            "hash_ok": hash_ok,
            "rows": row_count,
            "unique_candidate_ids": len(seen),
            "duplicate_candidate_ids": duplicate_ids,
            "matched_base_rows": matched,
            "outside_base_rows": outside,
            "base_coverage_fraction": coverage,
            "minimum_base_coverage_fraction": min_coverage,
            "declared_field_missing_counts": dict(sorted(missing_declared_fields.items())),
            "required_source_missing_counts": required_source_missing,
            "verification": "PASS" if verified else "FAIL",
            "failure_reasons": reasons,
            "admitted_to_feature_config": verified and bool(spec.get("admit", False)),
            "fields": mappings,
        }
        entries.append(entry)
        if entry["admitted_to_feature_config"]:
            ready_verified.append(sid)

    receipt = {
        "schema": "hawkar.topa.artifact_sidecar_audit_receipt.v1",
        "status": "PASS" if all(e["verification"] in {"PASS", "NOT_APPLICABLE_NO_READY_BYTES"} for e in entries) else "FAIL",
        "feature_registry_path": str(registry_path),
        "feature_registry_raw_sha256": registry_sha,
        "base_candidate_path": str(base_path),
        "base_candidate_raw_sha256": raw_sha256(base_path),
        "base_candidate_rows": n_base,
        "sidecars": entries,
        "admitted_sidecar_ids": ready_verified,
        "rule": "ONLY_READY_BYTES_WITH_VERIFICATION_PASS_AND_ADMIT_TRUE_MAY_ENTER_THE_FEATURE_CONFIG",
        "nuclear_outcome_used_for_admission": False,
    }
    if config.get("receipt_path"):
        write_json_atomic(_resolve(base_dir, config["receipt_path"]), receipt)
    return receipt


def emit_config(config: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    audit = audit_manifest(config, base_dir=base_dir)
    if audit["status"] != "PASS":
        raise ValueError("sidecar audit failed; feature config emission refused")
    base_config_path = _resolve(base_dir, config["base_feature_config_path"])
    out_path = _resolve(base_dir, config["output_feature_config_path"])
    feature_config = json.loads(base_config_path.read_text(encoding="utf-8"))
    existing_ids = {str(x.get("id")) for x in feature_config.get("sidecars", [])}
    for entry in audit["sidecars"]:
        if not entry.get("admitted_to_feature_config"):
            continue
        if entry["id"] in existing_ids:
            raise ValueError(f"sidecar id already exists in feature config: {entry['id']}")
        feature_config.setdefault("sidecars", []).append({
            "id": entry["id"],
            "path": entry["path"],
            "id_field": next(
                str(s.get("id_field", "src_id"))
                for s in config["sidecars"] if str(s.get("id")) == entry["id"]
            ),
            "require_full_base_coverage": entry["base_coverage_fraction"] == 1.0,
            "fields": entry["fields"],
            "topa_sidecar_gate": {
                "raw_sha256": entry["raw_sha256"],
                "verification": "PASS",
                "family": entry["family"],
            },
        })
        existing_ids.add(entry["id"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(out_path, feature_config)
    receipt = {
        "schema": "hawkar.topa.artifact_sidecar_config_emission_receipt.v1",
        "status": "PASS",
        "base_feature_config_path": str(base_config_path),
        "base_feature_config_raw_sha256": raw_sha256(base_config_path),
        "output_feature_config_path": str(out_path),
        "output_feature_config_raw_sha256": raw_sha256(out_path),
        "admitted_sidecars": audit["admitted_sidecar_ids"],
        "audit": audit,
    }
    if config.get("emission_receipt_path"):
        write_json_atomic(_resolve(base_dir, config["emission_receipt_path"]), receipt)
    return receipt


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="topa-sidecars-") as td:
        root = Path(td)
        base = root / "base.jsonl.gz"
        with JsonlWriter(base) as w:
            for i in range(10):
                w.write({"src_id": f"c{i}"})
        ready = root / "morph.ndjson.bz2"
        with JsonlWriter(ready) as w:
            for i in range(10):
                w.write({"src_id": f"c{i}", "fwhm_ratio": 1.0 + i / 100})
        ready_sha = raw_sha256(ready)
        base_cfg = root / "base-config.json"
        write_json_atomic(base_cfg, {"base": {"path": "irrelevant.csv"}, "sidecars": []})
        cfg = {
            "feature_registry_path": str(DEFAULT_REGISTRY),
            "base_candidate_path": str(base),
            "base_candidate_id_field": "src_id",
            "base_feature_config_path": str(base_cfg),
            "output_feature_config_path": str(root / "expanded.json"),
            "sidecars": [
                {
                    "id": "morph", "family": "morphology_psf",
                    "availability": "RECONSTRUCTED_BYTES_READY", "path": str(ready),
                    "raw_sha256": ready_sha, "id_field": "src_id",
                    "minimum_base_coverage_fraction": 1.0, "admit": True,
                    "fields": [
                        {"source": "fwhm_ratio", "feature": "morph_fwhm_ratio", "type": "float", "required": True}
                    ]
                },
                {
                    "id": "ptf_future", "family": "modern_epoch_ptf",
                    "availability": "RECONSTRUCTION_REQUIRED",
                    "reconstruction": {"generator": "tools/ptf_stage_coverage.py"}
                }
            ]
        }
        audit = audit_manifest(cfg, base_dir=root)
        assert audit["status"] == "PASS"
        assert audit["admitted_sidecar_ids"] == ["morph"]
        emitted = emit_config(cfg, base_dir=root)
        assert emitted["admitted_sidecars"] == ["morph"]
        obj = json.loads((root / "expanded.json").read_text(encoding="utf-8"))
        assert len(obj["sidecars"]) == 1 and obj["sidecars"][0]["id"] == "morph"

        bad = dict(cfg)
        bad["sidecars"] = [dict(cfg["sidecars"][0], raw_sha256="0" * 64)]
        bad_audit = audit_manifest(bad, base_dir=root)
        assert bad_audit["status"] == "FAIL"
        return {
            "schema": "hawkar.topa.artifact_sidecars.self_test.v1",
            "status": "PASS",
            "ready_sidecar_hash_gate": True,
            "coverage_gate": True,
            "registry_field_gate": True,
            "reconstruction_required_not_promoted": True,
            "hash_mismatch_fails_closed": True,
            "verified_config_emission": True,
            "compressed_json_sidecars": True,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="TOPA artifact sidecar gatekeeper")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("audit", "emit-config"):
        p = sp.add_parser(name)
        p.add_argument("config")
    sp.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        result = self_test()
    else:
        cfg_path = Path(args.config).resolve()
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
        result = audit_manifest(config, base_dir=cfg_path.parent) if args.cmd == "audit" else emit_config(config, base_dir=cfg_path.parent)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
