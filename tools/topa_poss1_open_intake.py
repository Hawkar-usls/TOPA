#!/usr/bin/env python3
"""Pinned public POSS-I intake for the TOPA Artifact Classifier.

Downloads the public `jannefi/poss1-plate-slice` release from a frozen commit,
verifies published transfer/content hashes, optionally reconstructs plate-level
DATE-OBS/EXPOSURE provenance from IRSA FITS primary headers, and writes a ready
feature-build config for `topa_artifact_features.py`.

No unpublished VASCO catalogue is required or accepted.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import gzip
import hashlib
import io
import json
import re
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from topa_json_rails import JsonlWriter, raw_sha256, write_json_atomic

UPSTREAM_REPO = "jannefi/poss1-plate-slice"
UPSTREAM_COMMIT = "554aae5d4c48d800898cdd6aab261d9cba648e8c"
RELEASE_DIR = "results/s0-642-20260814"
RAW_BASE = f"https://raw.githubusercontent.com/jannefi/poss1-plate-slice/{UPSTREAM_COMMIT}"
IRSA_BASE = "https://irsa.ipac.caltech.edu/data/DSS/images/dss1red"

PINNED = {
    "stage_S0.csv.gz": {
        "path": f"{RELEASE_DIR}/stage_S0.csv.gz",
        "compressed_sha256": "f19cf987756c62a68f55a472992d860e73ae63b3a4664189092b0e1fda77f7bb",
        "uncompressed_sha256": "2ff92f2210acb387ef9ef4b88d561595d3883e9aab27065042627272b96590f0",
        "expected_rows": 122820,
    },
    "tile_manifest.csv.gz": {
        "path": f"{RELEASE_DIR}/tile_manifest.csv.gz",
        "compressed_sha256": "a1652db2d15470a9e8630a1a2ac3a055e49be65880ca615126a9aaa8cc2da02d",
        "uncompressed_sha256": "5dcb90dc5d98550e5a60246aced2b097922a267c69e81f27d45d16a288142a99",
        "expected_rows": 31458,
    },
    "primary_plate_flags.csv.gz": {
        "path": f"{RELEASE_DIR}/primary_plate_flags.csv.gz",
        "compressed_sha256": "4d5bb1e889d5e0778d4809d0d229dad20c8003062c40c1452b40d908e9330400",
        "uncompressed_sha256": "1f86ab0d5fb96733881e58f72fda8b2dbc3401405500f30ae924b9d736fdeee9",
        "expected_rows": 122820,
    },
    "repaired_astrometry_tiles.csv": {
        "path": f"{RELEASE_DIR}/repaired_astrometry_tiles.csv",
        "compressed_sha256": "8492e16077c83daa13a7449b9ae6b0a472aee9d2dcff0ab1c739b78779da222e",
        "uncompressed_sha256": None,
        "expected_rows": None,
    },
}
AUXILIARY = {
    "plate_manifest.csv": "data/plate_manifest.csv",
    "plate_crpix_table.csv": "data/plate_crpix_table.csv",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, *, max_bytes: int | None = None, range_header: str | None = None, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "TOPA-POSS1-open-intake/1.0", "Accept-Encoding": "identity"})
    if range_header:
        req.add_header("Range", range_header)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read() if max_bytes is None else r.read(max_bytes)


def _count_csv_rows(raw: bytes) -> int:
    text = raw.decode("utf-8-sig")
    return sum(1 for _ in csv.DictReader(io.StringIO(text)))


def verify_pinned_blob(name: str, blob: bytes, spec: dict[str, Any]) -> dict[str, Any]:
    got = sha256_bytes(blob)
    if got != spec["compressed_sha256"]:
        raise ValueError(f"{name}: transfer/content SHA-256 mismatch {got} != {spec['compressed_sha256']}")
    if name.endswith(".gz"):
        raw = gzip.decompress(blob)
        uncompressed = sha256_bytes(raw)
        if spec.get("uncompressed_sha256") and uncompressed != spec["uncompressed_sha256"]:
            raise ValueError(f"{name}: decompressed SHA-256 mismatch {uncompressed} != {spec['uncompressed_sha256']}")
        rows = _count_csv_rows(raw) if name.endswith(".csv.gz") else None
    else:
        raw = blob
        uncompressed = got
        rows = _count_csv_rows(raw) if name.endswith(".csv") else None
    if spec.get("expected_rows") is not None and rows != spec["expected_rows"]:
        raise ValueError(f"{name}: expected {spec['expected_rows']} rows, got {rows}")
    return {
        "raw_sha256": got,
        "decompressed_or_content_sha256": uncompressed,
        "rows": rows,
        "bytes": len(blob),
    }


def fetch_release(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, spec in PINNED.items():
        url = f"{RAW_BASE}/{spec['path']}"
        blob = fetch_bytes(url)
        receipt = verify_pinned_blob(name, blob, spec)
        path = out_dir / name
        path.write_bytes(blob)
        receipt.update({"url": url, "path": str(path)})
        files[name] = receipt
    for name, rel in AUXILIARY.items():
        url = f"{RAW_BASE}/{rel}"
        blob = fetch_bytes(url)
        path = out_dir / name
        path.write_bytes(blob)
        files[name] = {
            "url": url, "path": str(path), "raw_sha256": sha256_bytes(blob),
            "bytes": len(blob), "pinned_by_upstream_commit": UPSTREAM_COMMIT,
        }
    return {
        "schema": "hawkar.topa.poss1_open_intake.release_receipt.v1",
        "status": "PASS",
        "upstream_repository": UPSTREAM_REPO,
        "upstream_commit": UPSTREAM_COMMIT,
        "release_dir": RELEASE_DIR,
        "files": files,
        "unpublished_inputs_used": False,
    }


def _parse_fits_header(data: bytes) -> dict[str, str]:
    out = {}
    for pos in range(0, len(data) - 79, 80):
        card = data[pos:pos+80].decode("ascii", errors="ignore")
        key = card[:8].strip()
        if key == "END":
            break
        if not key or card[8:10] != "= ":
            continue
        raw = card[10:80]
        if raw.lstrip().startswith("'"):
            q = raw.find("'")
            q2 = raw.find("'", q + 1)
            value = raw[q+1:q2] if q >= 0 and q2 > q else raw.strip().strip("'")
        else:
            value = raw.split("/", 1)[0].strip()
        out[key] = value.strip()
    return out


def _parse_date_obs(value: str) -> str:
    s = str(value or "").strip().strip("'")
    if len(s) >= 10 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", s[:10]):
        return s[:10]
    for fmt in ("%d/%m/%y", "%m/%d/%y", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            d = datetime.strptime(s[:10], fmt).date()
            if d.year >= 2000 and len(s.split("/")[-1]) == 2:
                d = d.replace(year=d.year - 100)
            return d.isoformat()
        except ValueError:
            pass
    raise ValueError(f"unparseable DATE-OBS {value!r}")


def _parse_float(value: Any) -> float:
    return float(str(value).strip().replace("D", "E"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("rt", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _fetch_plate_header(plate_id: str) -> dict[str, Any]:
    url = f"{IRSA_BASE}/dss1red_{plate_id}.fits"
    raw = fetch_bytes(url, max_bytes=131072, range_header="bytes=0-131071")
    hdr = _parse_fits_header(raw)
    if not hdr:
        raise RuntimeError(f"{plate_id}: no FITS header parsed")
    region = str(hdr.get("REGION", plate_id)).strip()
    if region and region != plate_id:
        raise RuntimeError(f"{plate_id}: REGION identity mismatch {region}")
    exposure = _parse_float(hdr.get("EXPOSURE"))
    if not math_is_positive(exposure):
        raise RuntimeError(f"{plate_id}: missing/nonpositive EXPOSURE")
    return {
        "plate_id": plate_id,
        "date_obs": _parse_date_obs(hdr.get("DATE-OBS", "")),
        "exposure_min": exposure,
        "region": region,
        "telescope": hdr.get("TELESCOP"),
        "emulsion": hdr.get("EMULSION"),
        "filter": hdr.get("FILTER"),
        "header_prefix_sha256": sha256_bytes(raw),
        "source_url": url,
    }


def math_is_positive(x: float) -> bool:
    return x == x and x > 0 and x != float("inf")


def fetch_plate_metadata(out_dir: Path, *, workers: int = 10) -> dict[str, Any]:
    manifest_path = out_dir / "plate_manifest.csv"
    wcs_path = out_dir / "plate_crpix_table.csv"
    if not manifest_path.exists() or not wcs_path.exists():
        raise FileNotFoundError("run fetch-release first; plate_manifest.csv and plate_crpix_table.csv are required")
    manifest = _read_csv(manifest_path)
    plates = sorted({str(r["plate_id"]).strip() for r in manifest if str(r.get("plate_id", "")).strip()})
    wcs_rows = {str(r["plate"]).strip(): r for r in _read_csv(wcs_path)}
    if len(plates) < 600:
        raise RuntimeError(f"unexpected plate manifest size {len(plates)}")
    results = []
    errors = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_fetch_plate_header, p): p for p in plates}
        for fut in cf.as_completed(futures):
            p = futures[fut]
            try:
                row = fut.result()
                wcs = wcs_rows.get(p)
                if wcs is None:
                    raise RuntimeError(f"{p}: WCS metadata missing")
                row.update({
                    "wcs_offset_arcsec": _parse_float(wcs["offset_arcsec"]),
                    "wcs_scatter_px": _parse_float(wcs["scatter_px"]),
                    "wcs_status": wcs.get("status"),
                })
                results.append(row)
            except Exception as exc:
                errors.append(f"{p}:{exc}")
    if errors:
        raise RuntimeError("plate header intake failed closed: " + " | ".join(errors[:10]))
    results.sort(key=lambda r: r["plate_id"])
    path = out_dir / "plate_observation_metadata.jsonl.gz"
    with JsonlWriter(path) as writer:
        for row in results:
            writer.write(row)
    return {
        "schema": "hawkar.topa.poss1_open_intake.plate_metadata_receipt.v1",
        "status": "PASS",
        "plates": len(results),
        "output_path": str(path),
        "output_raw_sha256": raw_sha256(path),
        "workers": workers,
        "source": "IRSA_DSS1_RED_FITS_PRIMARY_HEADERS_PLUS_PINNED_POSS1_WCS_TABLE",
    }


def write_feature_config(out_dir: Path) -> Path:
    config = {
        "feature_registry_path": "../../research/uap-nuclear/TOPA-ARTIFACT-FEATURE-REGISTRY-v1.0.json",
        "base": {
            "path": "stage_S0.csv.gz", "id_field": "src_id", "tile_field": "tile_id",
            "ra_field": "ra", "dec_field": "dec"
        },
        "tile_manifest": {
            "path": "tile_manifest.csv.gz", "tile_field": "tile_id", "plate_field": "plate_id",
            "fields": [
                {"source":"rows_emitted_to_S0","feature":"acq_tile_rows_emitted_s0","type":"float"}
            ]
        },
        "plate_metadata": {
            "path": "plate_observation_metadata.jsonl.gz", "plate_field": "plate_id", "date_field": "date_obs",
            "fields": [
                {"source":"exposure_min","feature":"acq_exposure_min","type":"float"},
                {"source":"wcs_offset_arcsec","feature":"acq_wcs_offset_arcsec","type":"float"}
            ]
        },
        "sidecars": [
            {
                "id": "primary_plate_geometry", "path": "primary_plate_flags.csv.gz", "id_field": "src_id",
                "require_full_base_coverage": True,
                "fields": [
                    {"source":"is_primary","feature":"geo_is_primary","type":"bool"},
                    {"source":"sep_primary_deg","feature":"geo_sep_primary_deg","type":"float"},
                    {"source":"sep_margin","feature":"geo_sep_margin","type":"float"}
                ]
            }
        ],
        "output_path": "topa_artifact_features_minimal.jsonl.gz",
        "receipt_path": "topa_artifact_features_minimal.receipt.json",
        "note": "Add morphology/shape/edge/SuperCOSMOS/PTF/persistence sidecars as they are generated; never choose sidecars by nuclear-window outcome."
    }
    path = out_dir / "topa_artifact_feature_build_config.json"
    write_json_atomic(path, config)
    return path


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="topa-poss1-intake-") as td:
        root = Path(td)
        raw = b"a,b\n1,2\n3,4\n"
        blob = gzip.compress(raw)
        spec = {
            "compressed_sha256": sha256_bytes(blob),
            "uncompressed_sha256": sha256_bytes(raw),
            "expected_rows": 2,
        }
        checked = verify_pinned_blob("x.csv.gz", blob, spec)
        cards = []
        def card(key, value):
            text = f"{key:<8}= {value:<70}"
            return text[:80].ljust(80).encode("ascii")
        cards.append(card("REGION", "'XE001'"))
        cards.append(card("DATE-OBS", "'1950-01-02'"))
        cards.append(card("EXPOSURE", "45.0"))
        cards.append(b"END".ljust(80))
        hdr = _parse_fits_header(b"".join(cards))
        assert hdr["REGION"] == "XE001" and _parse_date_obs(hdr["DATE-OBS"]) == "1950-01-02"
        assert checked["rows"] == 2
        return {
            "schema": "hawkar.topa.poss1_open_intake.self_test.v1",
            "status": "PASS",
            "gzip_transfer_hash_verified": True,
            "decompressed_content_hash_verified": True,
            "csv_row_invariant_verified": True,
            "fits_header_parser_verified": True,
            "upstream_commit_pin": UPSTREAM_COMMIT,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="TOPA pinned POSS-I public intake")
    sp = ap.add_subparsers(dest="cmd", required=True)
    fr = sp.add_parser("fetch-release"); fr.add_argument("--out-dir", required=True); fr.add_argument("--receipt")
    ph = sp.add_parser("fetch-plate-metadata"); ph.add_argument("--out-dir", required=True); ph.add_argument("--workers", type=int, default=10); ph.add_argument("--receipt")
    wc = sp.add_parser("write-feature-config"); wc.add_argument("--out-dir", required=True)
    sp.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        result = self_test()
    elif args.cmd == "fetch-release":
        out = Path(args.out_dir).resolve(); result = fetch_release(out)
        if args.receipt: write_json_atomic(Path(args.receipt).resolve(), result)
    elif args.cmd == "fetch-plate-metadata":
        out = Path(args.out_dir).resolve(); result = fetch_plate_metadata(out, workers=args.workers)
        if args.receipt: write_json_atomic(Path(args.receipt).resolve(), result)
    else:
        path = write_feature_config(Path(args.out_dir).resolve())
        result = {"status":"PASS","feature_config_path":str(path)}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
