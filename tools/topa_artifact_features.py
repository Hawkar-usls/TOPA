#!/usr/bin/env python3
"""TOPA Artifact Classifier feature-rail builder v1.

Builds one machine-readable candidate feature stream from a base POSS-I
candidate catalogue plus independently generated sidecars (plate geometry,
morphology, pixel shape, cross-scan checks, persistence and acquisition
provenance).

Important boundaries:
- input CSV/CSV.GZ/CSV.BZ2 exists only as an adapter for public astronomy tables;
- canonical output is JSONL/NDJSON on TOPA JSON rails;
- plate/date identities are provenance/group fields, never model predictors;
- nuclear/UAP/harmonization fields are rejected as predictors;
- missing measurements stay missing; values are never silently imputed here.
"""
from __future__ import annotations

import argparse
import bz2
import csv
import gzip
import hashlib
import json
import math
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from topa_json_rails import JsonlWriter, iter_records, raw_sha256, write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "research/uap-nuclear/TOPA-ARTIFACT-FEATURE-REGISTRY-v1.0.json"

FORBIDDEN_EXACT = {
    "plate_id", "date_obs", "obs_date", "group_id", "nuclear_window",
    "nuclear_test", "nuclear_event", "harmonization_outcome", "effect_p_value",
    "uap", "nhi", "label", "target", "ground_truth",
}
FORBIDDEN_FRAGMENTS = (
    "nuclear_", "atomic_test", "bomb_test", "detonation_", "harmonization_",
    "uap_", "nhi_", "outcome_",
)


def _is_json_path(path: Path) -> bool:
    n = path.name.lower()
    return any(n.endswith(s) for s in (
        ".json", ".json.gz", ".json.bz2", ".jsonl", ".ndjson",
        ".jsonl.gz", ".ndjson.gz", ".jsonl.bz2", ".ndjson.bz2",
    ))


def _is_csv_path(path: Path) -> bool:
    n = path.name.lower()
    return n.endswith(".csv") or n.endswith(".csv.gz") or n.endswith(".csv.bz2")


@contextmanager
def _open_text(path: Path):
    n = path.name.lower()
    if n.endswith(".gz"):
        fh = gzip.open(path, "rt", encoding="utf-8-sig", newline="")
    elif n.endswith(".bz2"):
        fh = bz2.open(path, "rt", encoding="utf-8-sig", newline="")
    else:
        fh = path.open("rt", encoding="utf-8-sig", newline="")
    try:
        yield fh
    finally:
        fh.close()


def iter_table(path: str | Path) -> Iterable[dict[str, Any]]:
    p = Path(path)
    if _is_json_path(p):
        for row in iter_records(p):
            if not isinstance(row, dict):
                raise ValueError(f"{p}: expected object records, got {type(row).__name__}")
            yield row
        return
    if _is_csv_path(p):
        with _open_text(p) as fh:
            for row in csv.DictReader(fh):
                yield dict(row)
        return
    raise ValueError(f"unsupported tabular input {p}; use JSON rails or CSV(.gz/.bz2) adapter")


def _resolve(base_dir: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base_dir / p).resolve()


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    s = str(value).strip().lower()
    if s in {"1", "true", "t", "yes", "y"}:
        return True
    if s in {"0", "false", "f", "no", "n"}:
        return False
    raise ValueError(f"cannot parse boolean value {value!r}")


def _coerce(value: Any, typ: str) -> float | bool | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if typ == "bool":
        return _parse_bool(value)
    if typ in {"float", "int"}:
        x = float(value)
        if not math.isfinite(x):
            raise ValueError(f"non-finite feature value {value!r}")
        return int(x) if typ == "int" else x
    raise ValueError(f"unsupported feature type {typ!r}; v1 predictors must be numeric/bool")


def _load_registry(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    features = {x["name"]: x for x in obj.get("features", [])}
    if not features:
        raise ValueError("feature registry contains no features")
    return features, hashlib.sha256(raw).hexdigest()


def _guard_feature_name(name: str) -> None:
    low = name.lower()
    if low in FORBIDDEN_EXACT or any(fragment in low for fragment in FORBIDDEN_FRAGMENTS):
        raise ValueError(f"forbidden predictor name {name!r}")


def _apply_fields(
    record: dict[str, Any],
    source_row: dict[str, Any],
    mappings: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
) -> int:
    n = 0
    for m in mappings:
        src = m["source"]
        dest = m["feature"]
        _guard_feature_name(dest)
        if dest not in registry:
            raise ValueError(f"feature {dest!r} is not registered")
        expected = registry[dest].get("type")
        typ = m.get("type", expected)
        if expected and typ != expected:
            raise ValueError(f"feature {dest}: mapping type={typ} disagrees with registry type={expected}")
        if src not in source_row:
            if m.get("required", False):
                raise KeyError(f"required source field {src!r} missing for feature {dest!r}")
            continue
        value = _coerce(source_row.get(src), typ)
        if value is None:
            continue
        if dest in record["features"] and record["features"][dest] != value:
            raise ValueError(f"candidate {record['candidate_id']}: conflicting values for {dest}")
        record["features"][dest] = value
        n += 1
    return n


def _group_id(plate_id: str | None, date_obs: str | None) -> str:
    if not plate_id:
        raise ValueError("plate_id is required to construct a leakage-safe group")
    material = f"{plate_id}|{date_obs or 'DATE_UNKNOWN'}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def build_feature_rail(config: dict[str, Any], *, base_dir: Path = Path.cwd()) -> dict[str, Any]:
    registry_path = _resolve(base_dir, config.get("feature_registry_path", DEFAULT_REGISTRY))
    registry, registry_sha = _load_registry(registry_path)

    base_spec = config["base"]
    base_path = _resolve(base_dir, base_spec["path"])
    id_field = base_spec.get("id_field", "src_id")
    tile_field = base_spec.get("tile_field", "tile_id")
    ra_field = base_spec.get("ra_field", "ra")
    dec_field = base_spec.get("dec_field", "dec")
    plate_field = base_spec.get("plate_field")
    date_field = base_spec.get("date_field")

    rows: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for source_row in iter_table(base_path):
        cid = str(source_row.get(id_field, "")).strip()
        if not cid:
            raise ValueError(f"base row missing {id_field}")
        if cid in rows:
            raise ValueError(f"duplicate candidate id in base: {cid}")
        tile = str(source_row.get(tile_field, "")).strip() or None
        ra = _coerce(source_row.get(ra_field), "float")
        dec = _coerce(source_row.get(dec_field), "float")
        if ra is None or dec is None:
            raise ValueError(f"candidate {cid}: missing RA/Dec")
        plate = str(source_row.get(plate_field, "")).strip() if plate_field else ""
        date_obs = str(source_row.get(date_field, "")).strip() if date_field else ""
        rec = {
            "schema": "hawkar.topa.artifact_feature_row.v1",
            "candidate_id": cid,
            "tile_id": tile,
            "plate_id": plate or None,
            "date_obs": date_obs or None,
            "ra_deg": float(ra),
            "dec_deg": float(dec),
            "features": {},
            "source_presence": {"base": True},
        }
        _apply_fields(rec, source_row, base_spec.get("fields", []), registry)
        rows[cid] = rec
        order.append(cid)

    input_receipts: list[dict[str, Any]] = [{
        "id": "base", "path": str(base_path), "raw_sha256": raw_sha256(base_path), "rows": len(rows)
    }]

    tile_spec = config.get("tile_manifest")
    if tile_spec:
        tile_path = _resolve(base_dir, tile_spec["path"])
        tfield = tile_spec.get("tile_field", "tile_id")
        pfield = tile_spec.get("plate_field", "plate_id")
        tile_map: dict[str, str] = {}
        tile_meta: dict[str, dict[str, Any]] = {}
        tile_rows = 0
        for tr in iter_table(tile_path):
            tile_rows += 1
            tile = str(tr.get(tfield, "")).strip()
            plate = str(tr.get(pfield, "")).strip()
            if not tile or not plate:
                raise ValueError("tile manifest contains blank tile/plate")
            if tile in tile_map and tile_map[tile] != plate:
                raise ValueError(f"tile {tile} maps to multiple plates")
            tile_map[tile] = plate
            tile_meta[tile] = tr
        for rec in rows.values():
            tile = rec.get("tile_id")
            if not tile or tile not in tile_map:
                raise ValueError(f"candidate {rec['candidate_id']}: tile not found in tile manifest: {tile}")
            if rec["plate_id"] and rec["plate_id"] != tile_map[tile]:
                raise ValueError(f"candidate {rec['candidate_id']}: base plate disagrees with tile manifest")
            rec["plate_id"] = tile_map[tile]
            _apply_fields(rec, tile_meta[tile], tile_spec.get("fields", []), registry)
            rec["source_presence"]["tile_manifest"] = True
        input_receipts.append({
            "id": "tile_manifest", "path": str(tile_path), "raw_sha256": raw_sha256(tile_path), "rows": tile_rows
        })

    plate_spec = config.get("plate_metadata")
    if plate_spec:
        plate_path = _resolve(base_dir, plate_spec["path"])
        pfield = plate_spec.get("plate_field", "plate_id")
        dfield = plate_spec.get("date_field", "date_obs")
        plate_map: dict[str, dict[str, Any]] = {}
        for pr in iter_table(plate_path):
            pid = str(pr.get(pfield, "")).strip()
            if not pid:
                raise ValueError("plate metadata contains blank plate id")
            if pid in plate_map:
                raise ValueError(f"duplicate plate metadata id {pid}")
            plate_map[pid] = pr
        for rec in rows.values():
            pid = rec.get("plate_id")
            if pid not in plate_map:
                if plate_spec.get("required", True):
                    raise ValueError(f"candidate {rec['candidate_id']}: no plate metadata for {pid}")
                continue
            pr = plate_map[pid]
            if dfield and pr.get(dfield) not in (None, ""):
                date_obs = str(pr[dfield]).strip()[:10]
                if rec["date_obs"] and rec["date_obs"][:10] != date_obs:
                    raise ValueError(f"candidate {rec['candidate_id']}: conflicting observation dates")
                rec["date_obs"] = date_obs
            _apply_fields(rec, pr, plate_spec.get("fields", []), registry)
            rec["source_presence"]["plate_metadata"] = True
        input_receipts.append({
            "id": "plate_metadata", "path": str(plate_path), "raw_sha256": raw_sha256(plate_path), "rows": len(plate_map)
        })

    sidecar_receipts = []
    for side in config.get("sidecars", []):
        sid = side["id"]
        path = _resolve(base_dir, side["path"])
        side_id_field = side.get("id_field", "src_id")
        matched = unmatched = side_rows = values_added = 0
        seen: set[str] = set()
        for sr in iter_table(path):
            side_rows += 1
            cid = str(sr.get(side_id_field, "")).strip()
            if not cid:
                raise ValueError(f"sidecar {sid}: blank candidate id")
            if cid in seen and not side.get("allow_duplicate_ids", False):
                raise ValueError(f"sidecar {sid}: duplicate candidate id {cid}")
            seen.add(cid)
            rec = rows.get(cid)
            if rec is None:
                unmatched += 1
                continue
            matched += 1
            values_added += _apply_fields(rec, sr, side.get("fields", []), registry)
            rec["source_presence"][sid] = True
        if side.get("require_full_base_coverage", False) and matched != len(rows):
            raise ValueError(f"sidecar {sid}: expected coverage of all {len(rows)} base rows, matched {matched}")
        receipt = {
            "id": sid,
            "path": str(path),
            "raw_sha256": raw_sha256(path),
            "rows": side_rows,
            "matched_base_rows": matched,
            "unmatched_sidecar_rows": unmatched,
            "feature_values_added": values_added,
        }
        sidecar_receipts.append(receipt)
        input_receipts.append(receipt)

    missing_date = 0
    feature_counts: dict[str, int] = {name: 0 for name in registry}
    family_counts: dict[str, int] = {}
    for rec in rows.values():
        if not rec.get("plate_id"):
            raise ValueError(f"candidate {rec['candidate_id']}: plate_id unresolved")
        if not rec.get("date_obs"):
            missing_date += 1
        rec["group_id"] = _group_id(rec["plate_id"], rec.get("date_obs"))
        families = set()
        for name in rec["features"]:
            feature_counts[name] += 1
            families.add(registry[name]["family"])
        rec["feature_families_present"] = sorted(families)
        for fam in families:
            family_counts[fam] = family_counts.get(fam, 0) + 1

    out_path = _resolve(base_dir, config["output_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with JsonlWriter(out_path) as writer:
        for cid in order:
            writer.write(rows[cid])

    emitted_feature_counts = {k: v for k, v in feature_counts.items() if v}
    receipt = {
        "schema": "hawkar.topa.artifact_feature_build_receipt.v1",
        "status": "PASS",
        "candidate_rows": len(rows),
        "feature_registry_path": str(registry_path),
        "feature_registry_raw_sha256": registry_sha,
        "inputs": input_receipts,
        "sidecars": sidecar_receipts,
        "output_path": str(out_path),
        "output_raw_sha256": raw_sha256(out_path),
        "observation_date_missing_rows": missing_date,
        "feature_nonmissing_counts": emitted_feature_counts,
        "feature_family_row_presence": dict(sorted(family_counts.items())),
        "predictor_identity_policy": "plate_id/date_obs/group_id/coordinates remain provenance fields and are not inside features",
        "nuclear_or_uap_predictors": "FORBIDDEN_AND_NAME_GUARDED",
        "missingness_policy": "PRESERVED_NOT_IMPUTED",
        "claim_ceiling": "FEATURE_ASSEMBLY_AND_PROVENANCE_ONLY",
    }
    receipt_path = config.get("receipt_path")
    if receipt_path:
        write_json_atomic(_resolve(base_dir, receipt_path), receipt)
    return receipt


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="topa-artifact-features-") as td:
        root = Path(td)
        base = root / "base.csv.gz"
        with gzip.open(base, "wt", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["src_id", "tile_id", "ra", "dec"])
            w.writeheader()
            for i in range(4):
                w.writerow({"src_id": f"c{i}", "tile_id": f"t{i%2}", "ra": 10+i, "dec": 20+i})
        tiles = root / "tiles.csv.bz2"
        with bz2.open(tiles, "wt", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["tile_id", "plate_id", "rows_emitted_to_S0"])
            w.writeheader(); w.writerow({"tile_id":"t0","plate_id":"P0","rows_emitted_to_S0":2}); w.writerow({"tile_id":"t1","plate_id":"P1","rows_emitted_to_S0":2})
        plates = root / "plates.jsonl.gz"
        with JsonlWriter(plates) as w:
            w.write({"plate_id":"P0","date_obs":"1950-01-01","exposure_min":45,"wcs":0.2})
            w.write({"plate_id":"P1","date_obs":"1950-01-02","exposure_min":50,"wcs":0.3})
        geo = root / "geo.ndjson.bz2"
        with JsonlWriter(geo) as w:
            for i in range(4):
                w.write({"src_id":f"c{i}","is_primary":i%2==0,"sep_primary_deg":1.0+i/10,"sep_margin":0.2+i/100})
        morph = root / "morph.jsonl.gz"
        with JsonlWriter(morph) as w:
            for i in range(4):
                w.write({"src_id":f"c{i}","fwhm_ratio":1.0+i/10,"spread_snr":float(i)})
        out = root / "features.jsonl.gz"
        receipt_path = root / "receipt.json"
        cfg = {
            "feature_registry_path": str(DEFAULT_REGISTRY),
            "base": {"path": str(base), "id_field":"src_id", "tile_field":"tile_id", "ra_field":"ra", "dec_field":"dec"},
            "tile_manifest": {"path": str(tiles), "tile_field":"tile_id", "plate_field":"plate_id", "fields":[
                {"source":"rows_emitted_to_S0","feature":"acq_tile_rows_emitted_s0","type":"float"}
            ]},
            "plate_metadata": {"path": str(plates), "plate_field":"plate_id", "date_field":"date_obs", "fields":[
                {"source":"exposure_min","feature":"acq_exposure_min","type":"float"},
                {"source":"wcs","feature":"acq_wcs_offset_arcsec","type":"float"}
            ]},
            "sidecars": [
                {"id":"primary_plate", "path":str(geo), "id_field":"src_id", "require_full_base_coverage":True, "fields":[
                    {"source":"is_primary","feature":"geo_is_primary","type":"bool"},
                    {"source":"sep_primary_deg","feature":"geo_sep_primary_deg","type":"float"},
                    {"source":"sep_margin","feature":"geo_sep_margin","type":"float"}
                ]},
                {"id":"morph", "path":str(morph), "id_field":"src_id", "require_full_base_coverage":True, "fields":[
                    {"source":"fwhm_ratio","feature":"morph_fwhm_ratio","type":"float"},
                    {"source":"spread_snr","feature":"morph_spread_snr","type":"float"}
                ]}
            ],
            "output_path": str(out), "receipt_path": str(receipt_path)
        }
        receipt = build_feature_rail(cfg, base_dir=root)
        emitted = list(iter_records(out))
        assert receipt["status"] == "PASS" and len(emitted) == 4
        assert all(r["plate_id"] and r["group_id"] and r["date_obs"] for r in emitted)
        assert all("geo_is_primary" in r["features"] and "morph_fwhm_ratio" in r["features"] for r in emitted)
        assert json.loads(receipt_path.read_text(encoding="utf-8"))["candidate_rows"] == 4
        return {
            "schema": "hawkar.topa.artifact_feature_builder.self_test.v1",
            "status": "PASS",
            "rows": 4,
            "csv_gzip_adapter": True,
            "csv_bzip2_adapter": True,
            "jsonl_gzip_sidecar": True,
            "ndjson_bzip2_sidecar": True,
            "jsonl_gzip_output": True,
            "group_id_created": True,
            "feature_registry_enforced": True,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build TOPA artifact-classifier feature rails")
    sp = ap.add_subparsers(dest="cmd", required=True)
    runp = sp.add_parser("build")
    runp.add_argument("config")
    sp.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        result = self_test()
    else:
        config_path = Path(args.config).resolve()
        config = json.loads(config_path.read_text(encoding="utf-8"))
        result = build_feature_rail(config, base_dir=config_path.parent)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
