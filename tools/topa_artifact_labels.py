#!/usr/bin/env python3
"""TOPA Artifact Classifier label-rail tooling v1.

Keeps label provenance separate from model features and provides three small,
auditable operations:

1. validate  - enforce the label contract and emit a receipt;
2. sample    - deterministic group-balanced blind review manifest from a feature rail;
3. consensus - combine independent reviewer rails, emitting agreements and a conflict ledger.

This tool never loads a nuclear calendar, harmonization result, classifier score,
or UAP/NHI label. Human/forensic review stays upstream of those questions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from topa_json_rails import JsonlWriter, iter_records, raw_sha256, write_json_atomic

ALLOWED_LABELS = {0, 1}
ALLOWED_TIERS = {"A", "B", "C"}
FORBIDDEN_REVIEW_KEYS = {
    "candidate_quality_score_raw",
    "artifact_likelihood_raw",
    "nuclear_window",
    "nuclear_test",
    "nuclear_event",
    "harmonization_outcome",
    "effect_p_value",
    "uap",
    "nhi",
}


def _resolve(base_dir: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base_dir / p).resolve()


def _records(path: Path) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for row in iter_records(path):
        if not isinstance(row, dict):
            raise ValueError(f"{path}: expected object records")
        cid = str(row.get("candidate_id", "")).strip()
        if not cid:
            raise ValueError(f"{path}: record missing candidate_id")
        if cid in seen:
            raise ValueError(f"{path}: duplicate candidate_id={cid}")
        seen.add(cid)
        out.append(row)
    return out


def _clean_witness_families(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("witness_families must be a JSON list")
    out = []
    for x in value:
        s = str(x).strip()
        if not s:
            raise ValueError("witness_families contains blank value")
        out.append(s)
    return sorted(set(out))


def validate_label_row(row: dict[str, Any], *, require_evidence_ref_for_tier_a: bool = True) -> dict[str, Any]:
    cid = str(row.get("candidate_id", "")).strip()
    if not cid:
        raise ValueError("label row missing candidate_id")
    try:
        label = int(row["label"])
    except Exception as exc:
        raise ValueError(f"{cid}: label must be integer 0/1") from exc
    if label not in ALLOWED_LABELS:
        raise ValueError(f"{cid}: label must be 0 or 1")
    tier = str(row.get("label_tier", "")).strip().upper()
    if tier not in ALLOWED_TIERS:
        raise ValueError(f"{cid}: label_tier must be A, B or C")
    source = str(row.get("label_source", "")).strip()
    if not source:
        raise ValueError(f"{cid}: label_source is required")
    witness = _clean_witness_families(row.get("witness_families"))
    evidence_refs = row.get("evidence_refs", [])
    if evidence_refs is None:
        evidence_refs = []
    if not isinstance(evidence_refs, list):
        raise ValueError(f"{cid}: evidence_refs must be a JSON list")
    evidence_refs = [str(x).strip() for x in evidence_refs if str(x).strip()]
    if tier == "A" and require_evidence_ref_for_tier_a and not evidence_refs:
        raise ValueError(f"{cid}: Tier-A direct forensic label requires at least one evidence_ref/hash/asset reference")
    reviewer = str(row.get("reviewer_id", "")).strip() or None
    notes = str(row.get("notes", "")).strip() or None
    return {
        "candidate_id": cid,
        "label": label,
        "label_tier": tier,
        "label_source": source,
        "witness_families": witness,
        "evidence_refs": evidence_refs,
        "reviewer_id": reviewer,
        "notes": notes,
    }


def validate_labels(config: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    path = _resolve(base_dir, config["label_path"])
    require_a = bool(config.get("require_evidence_ref_for_tier_a", True))
    rows = []
    seen = set()
    for raw in iter_records(path):
        if not isinstance(raw, dict):
            raise ValueError("label rail must contain JSON objects")
        row = validate_label_row(raw, require_evidence_ref_for_tier_a=require_a)
        if row["candidate_id"] in seen:
            raise ValueError(f"duplicate candidate label: {row['candidate_id']}")
        seen.add(row["candidate_id"])
        rows.append(row)
    if not rows:
        raise ValueError("label rail is empty")

    feature_path_value = config.get("feature_path")
    feature_ids = None
    group_by_id = {}
    if feature_path_value:
        feature_path = _resolve(base_dir, feature_path_value)
        feature_ids = set()
        for fr in iter_records(feature_path):
            if not isinstance(fr, dict):
                raise ValueError("feature rail contains non-object record")
            cid = str(fr.get("candidate_id", "")).strip()
            if not cid or cid in feature_ids:
                raise ValueError("feature rail missing/duplicate candidate_id")
            feature_ids.add(cid)
            group_by_id[cid] = str(fr.get("group_id", "")).strip() or "GROUP_MISSING"
    missing_features = sorted({r["candidate_id"] for r in rows} - feature_ids) if feature_ids is not None else []
    if missing_features and config.get("require_all_labels_in_feature_rail", True):
        raise ValueError(f"{len(missing_features)} labels are absent from feature rail")

    classes = Counter(r["label"] for r in rows)
    tiers = Counter(r["label_tier"] for r in rows)
    sources = Counter(r["label_source"] for r in rows)
    witnesses = Counter(fam for r in rows for fam in r["witness_families"])
    reviewers = Counter(r["reviewer_id"] or "UNSPECIFIED" for r in rows)
    groups = Counter(group_by_id.get(r["candidate_id"], "UNBOUND") for r in rows)

    receipt = {
        "schema": "hawkar.topa.artifact_label_validation_receipt.v1",
        "status": "PASS",
        "rows": len(rows),
        "label_file_raw_sha256": raw_sha256(path),
        "class_census": {str(k): int(v) for k, v in sorted(classes.items())},
        "tier_census": dict(sorted(tiers.items())),
        "source_census": dict(sorted(sources.items())),
        "witness_family_census": dict(sorted(witnesses.items())),
        "reviewer_census": dict(sorted(reviewers.items())),
        "independent_groups_represented": len(groups) if feature_ids is not None else None,
        "labels_without_feature_row": len(missing_features),
        "tier_a_evidence_ref_required": require_a,
        "semantic_contract": {
            "label_1": "POINT_SOURCE_LIKE_IMAGE_EVIDENCE",
            "label_0": "PLATE_OR_SCAN_ARTIFACT_LIKE_IMAGE_EVIDENCE",
            "not_claimed": ["real astrophysical transient", "UAP", "NHI", "nuclear response"],
        },
        "claim_ceiling": "LABEL_RAIL_VALIDITY_AND_PROVENANCE_ONLY",
    }
    if config.get("receipt_path"):
        write_json_atomic(_resolve(base_dir, config["receipt_path"]), receipt)
    return receipt


def _hash_rank(seed: int, group_id: str, candidate_id: str) -> int:
    material = f"TOPA_LABEL_SAMPLE|{seed}|{group_id}|{candidate_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest(), "big")


def sample_review(config: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    feature_path = _resolve(base_dir, config["feature_path"])
    out_path = _resolve(base_dir, config["output_path"])
    n_target = int(config.get("n", 500))
    seed = int(config.get("seed", 20260827))
    max_per_group = int(config.get("max_per_group", 2))
    if n_target <= 0 or max_per_group <= 0:
        raise ValueError("n and max_per_group must be positive")

    excluded = set()
    if config.get("exclude_label_path"):
        for row in iter_records(_resolve(base_dir, config["exclude_label_path"])):
            excluded.add(str(row.get("candidate_id", "")).strip())

    candidates = []
    forbidden_found = Counter()
    for row in iter_records(feature_path):
        if not isinstance(row, dict):
            raise ValueError("feature rail contains non-object record")
        cid = str(row.get("candidate_id", "")).strip()
        gid = str(row.get("group_id", "")).strip()
        if not cid or not gid:
            raise ValueError("feature rail review sampling requires candidate_id and group_id")
        if cid in excluded:
            continue
        for key in row:
            if key.lower() in FORBIDDEN_REVIEW_KEYS:
                forbidden_found[key] += 1
        candidates.append(row)
    if forbidden_found:
        raise ValueError(f"review input leaks forbidden outcome/score fields: {dict(forbidden_found)}")

    candidates.sort(key=lambda r: _hash_rank(seed, str(r["group_id"]), str(r["candidate_id"])))
    selected = []
    per_group = Counter()
    for row in candidates:
        gid = str(row["group_id"])
        if per_group[gid] >= max_per_group:
            continue
        per_group[gid] += 1
        selected.append(row)
        if len(selected) >= n_target:
            break
    if len(selected) < min(n_target, len(candidates)):
        # This is not necessarily an error: the group cap may make the requested N impossible.
        capacity_limited = True
    else:
        capacity_limited = False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with JsonlWriter(out_path) as writer:
        for idx, row in enumerate(selected, 1):
            writer.write({
                "schema": "hawkar.topa.artifact_blind_review_item.v1",
                "review_index": idx,
                "candidate_id": row["candidate_id"],
                "group_id": row["group_id"],
                "plate_id": row.get("plate_id"),
                "date_obs": row.get("date_obs"),
                "ra_deg": row.get("ra_deg"),
                "dec_deg": row.get("dec_deg"),
                "tile_id": row.get("tile_id"),
                "feature_families_present": row.get("feature_families_present", []),
                "blind_review_rule": "NO_CLASSIFIER_SCORE__NO_NUCLEAR_CONTEXT__NO_HARMONIZATION_CONTEXT",
            })

    receipt = {
        "schema": "hawkar.topa.artifact_blind_review_sampling_receipt.v1",
        "status": "PASS",
        "requested_n": n_target,
        "selected_n": len(selected),
        "available_unlabelled_n": len(candidates),
        "seed": seed,
        "max_per_group": max_per_group,
        "selected_groups": len({str(x["group_id"]) for x in selected}),
        "capacity_limited_by_group_cap": capacity_limited,
        "feature_file_raw_sha256": raw_sha256(feature_path),
        "excluded_existing_labels": len(excluded),
        "output_path": str(out_path),
        "output_raw_sha256": raw_sha256(out_path),
        "review_is_blind_to_classifier_and_nuclear_outcomes": True,
    }
    if config.get("receipt_path"):
        write_json_atomic(_resolve(base_dir, config["receipt_path"]), receipt)
    return receipt


def consensus(config: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    input_paths = [_resolve(base_dir, x) for x in config["label_paths"]]
    if len(input_paths) < 2:
        raise ValueError("consensus requires at least two independent label rails")
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    input_hashes = []
    for path in input_paths:
        reviewer_seen = set()
        for raw in iter_records(path):
            row = validate_label_row(raw, require_evidence_ref_for_tier_a=bool(config.get("require_evidence_ref_for_tier_a", True)))
            cid = row["candidate_id"]
            if cid in reviewer_seen:
                raise ValueError(f"{path}: duplicate candidate {cid}")
            reviewer_seen.add(cid)
            by_candidate[cid].append(row)
        input_hashes.append({"path": str(path), "raw_sha256": raw_sha256(path), "rows": len(reviewer_seen)})

    agreement_path = _resolve(base_dir, config["agreement_output_path"])
    conflict_path = _resolve(base_dir, config["conflict_output_path"])
    agreement_path.parent.mkdir(parents=True, exist_ok=True)
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    agreements = conflicts = insufficient = 0
    with JsonlWriter(agreement_path) as aw, JsonlWriter(conflict_path) as cw:
        for cid in sorted(by_candidate):
            rows = by_candidate[cid]
            if len(rows) < 2:
                insufficient += 1
                continue
            labels = {r["label"] for r in rows}
            if len(labels) != 1:
                conflicts += 1
                cw.write({
                    "schema": "hawkar.topa.artifact_label_conflict.v1",
                    "candidate_id": cid,
                    "status": "ADJUDICATION_REQUIRED",
                    "reviews": rows,
                })
                continue
            agreements += 1
            # Consensus tier is conservative: never promote above the weakest agreeing tier.
            tier_order = {"A": 3, "B": 2, "C": 1}
            consensus_tier = min((r["label_tier"] for r in rows), key=lambda x: tier_order[x])
            witness = sorted({fam for r in rows for fam in r["witness_families"]})
            evidence_refs = sorted({ref for r in rows for ref in r["evidence_refs"]})
            aw.write({
                "schema": "hawkar.topa.artifact_label_row.v1",
                "candidate_id": cid,
                "label": rows[0]["label"],
                "label_tier": consensus_tier,
                "label_source": "INDEPENDENT_REVIEW_CONSENSUS",
                "witness_families": witness,
                "evidence_refs": evidence_refs,
                "reviewer_count": len(rows),
                "reviewer_ids": sorted({r["reviewer_id"] or "UNSPECIFIED" for r in rows}),
            })

    receipt = {
        "schema": "hawkar.topa.artifact_label_consensus_receipt.v1",
        "status": "PASS",
        "input_label_rails": input_hashes,
        "candidate_union": len(by_candidate),
        "agreements": agreements,
        "conflicts_requiring_adjudication": conflicts,
        "insufficient_single_review": insufficient,
        "agreement_output_path": str(agreement_path),
        "agreement_output_raw_sha256": raw_sha256(agreement_path),
        "conflict_output_path": str(conflict_path),
        "conflict_output_raw_sha256": raw_sha256(conflict_path),
        "conflicts_auto_resolved": false,
        "tier_promotion_on_consensus": false,
    }
    if config.get("receipt_path"):
        write_json_atomic(_resolve(base_dir, config["receipt_path"]), receipt)
    return receipt


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="topa-labels-") as td:
        root = Path(td)
        features = root / "features.jsonl.gz"
        with JsonlWriter(features) as w:
            for i in range(30):
                w.write({
                    "candidate_id": f"c{i:02d}",
                    "group_id": f"g{i//3:02d}",
                    "plate_id": f"P{i//3:02d}",
                    "date_obs": "1950-01-01",
                    "ra_deg": 10+i/100,
                    "dec_deg": 20+i/100,
                    "tile_id": f"t{i:02d}",
                    "features": {"morph_fwhm_ratio": 1+i/100},
                    "feature_families_present": ["morphology_psf"],
                })
        sample_path = root / "review.ndjson.bz2"
        sample_receipt = sample_review({
            "feature_path": str(features), "output_path": str(sample_path),
            "n": 10, "seed": 7, "max_per_group": 1,
        }, base_dir=root)
        assert sample_receipt["selected_n"] == 10

        r1 = root / "r1.jsonl.gz"; r2 = root / "r2.jsonl.gz"
        with JsonlWriter(r1) as a, JsonlWriter(r2) as b:
            for i in range(10):
                base = {
                    "candidate_id": f"c{i:02d}", "label": i % 2,
                    "label_tier": "A", "label_source": "PIXEL_REVIEW",
                    "witness_families": [], "evidence_refs": [f"sha256:asset{i}"],
                }
                a.write(dict(base, reviewer_id="R1"))
                b.write(dict(base, reviewer_id="R2", label=(1-(i%2) if i == 9 else i%2)))
        valid = validate_labels({"label_path": str(r1), "feature_path": str(features)}, base_dir=root)
        assert valid["rows"] == 10
        agree = root / "agreement.jsonl.gz"; conflict = root / "conflict.jsonl.gz"
        con = consensus({
            "label_paths": [str(r1), str(r2)],
            "agreement_output_path": str(agree), "conflict_output_path": str(conflict),
        }, base_dir=root)
        assert con["agreements"] == 9 and con["conflicts_requiring_adjudication"] == 1
        return {
            "schema": "hawkar.topa.artifact_labels.self_test.v1",
            "status": "PASS",
            "deterministic_group_balanced_sample": True,
            "label_contract_validation": True,
            "independent_consensus": True,
            "conflicts_auto_resolved": False,
            "compressed_json_rails": True,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="TOPA Artifact Classifier label rails")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "sample", "consensus"):
        p = sp.add_parser(name); p.add_argument("config")
    sp.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        result = self_test()
    else:
        cfg_path = Path(args.config).resolve()
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
        if args.cmd == "validate":
            result = validate_labels(config, base_dir=cfg_path.parent)
        elif args.cmd == "sample":
            result = sample_review(config, base_dir=cfg_path.parent)
        else:
            result = consensus(config, base_dir=cfg_path.parent)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
