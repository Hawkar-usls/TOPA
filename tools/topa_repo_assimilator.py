#!/usr/bin/env python3
"""TOPA repository assimilation engine.

Scans the repository as research memory, not as automatic supervised truth.
It builds a deterministic provenance index and a routing queue for methods,
negative results, preregistrations, source ledgers, integrations, and files
potentially relevant to the POSS-I artifact-classifier lane.

Critical boundary:
    REPOSITORY_CORPUS_IS_NOT_ARTIFACT_CLASSIFIER_GROUND_TRUTH

Text, JSON, code, and historical results may teach TOPA methods, failure modes,
source routes, schemas, and provenance. They do not become image-classifier
labels unless they independently pass the dedicated label-rail contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "hawkar.topa.repo_assimilation.v1"
TEXT_SUFFIXES = {
    ".json", ".jsonl", ".ndjson", ".md", ".txt", ".py", ".yml", ".yaml",
    ".csv", ".tsv", ".toml", ".ini", ".cfg", ".sh", ".ps1",
}
IGNORE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "dist", "build", "work", "tmp", ".cache",
}
MAX_TEXT_BYTES = 4 * 1024 * 1024

ARTIFACT_TERMS = {
    "poss-i": 5, "poss1": 5, "vasco": 4, "artifact classifier": 6,
    "photographic plate": 4, "plate edge": 4, "supercosmos": 5, "ptf": 4,
    "morphology": 2, "spread_model": 4, "psf": 3, "wcs": 3,
    "transient": 2, "candidate_quality_score_raw": 6, "107,875": 4,
    "107875": 4, "palomar": 2, "plate geometry": 4,
}

NEGATIVE_TERMS = {
    "refuted", "failure", "failed", "negative result", "negative_result",
    "insufficient_data", "i_do_not_know", "weakened", "blocked",
}

ROLE_PATTERNS = [
    ("PREREGISTRATION", re.compile(r"prereg|freeze|frozen", re.I)),
    ("NEGATIVE_RESULT", re.compile(r"refuted|failure|failed|negative", re.I)),
    ("SOURCE_LEDGER", re.compile(r"source[_ -]?ledger|provenance", re.I)),
    ("RECEIPT", re.compile(r"receipt", re.I)),
    ("TRAINING_GROUND", re.compile(r"training[-_ ]ground|training[_ -]state", re.I)),
    ("FEATURE_OR_LABEL_SPEC", re.compile(r"feature|label|sidecar|classifier", re.I)),
    ("HUNT", re.compile(r"hunt|investigat|forensic|audit", re.I)),
    ("INTEGRATION", re.compile(r"integration|router|swarm|demiurge", re.I)),
    ("METHOD", re.compile(r"method|protocol|foundation|gate", re.I)),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_stream_sha256(records: Iterable[dict[str, Any]]) -> str:
    h = hashlib.sha256()
    for record in records:
        blob = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        h.update(blob)
        h.update(b"\n")
    return h.hexdigest()


def iter_repo_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".tox"))
        base = Path(current)
        for name in sorted(files):
            path = base / name
            if path.suffix.lower() in TEXT_SUFFIXES or name in {"LICENSE", "README", "Makefile"}:
                yield path


def classify_domain(rel: str) -> str:
    if rel.startswith("research/uap-nuclear/"):
        return "UAP_NUCLEAR"
    if rel.startswith("research/mathematics/") or rel.startswith("data/TOPA-C025"):
        return "MATHEMATICS"
    if rel.startswith("research/tesla-sweep/"):
        return "TRAINING_AND_SIGNAL_HUNTS"
    if rel.startswith("hunts/"):
        return "HUNTS"
    if rel.startswith("integrations/") or rel.startswith(".janus/"):
        return "JANUS_INTEGRATION"
    if rel.startswith("protocols/") or rel.startswith("registry/"):
        return "FOUNDATION_AND_REGISTRY"
    if rel.startswith("tools/") or rel.startswith(".github/workflows/"):
        return "EXECUTABLE_INFRASTRUCTURE"
    if rel.startswith("corpus/"):
        return "HISTORICAL_CORPUS"
    return "GENERAL"


def extract_json_metadata(text: str, suffix: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    objects: list[Any] = []
    try:
        if suffix == ".json":
            objects = [json.loads(text)]
        elif suffix in {".jsonl", ".ndjson"}:
            for line in text.splitlines()[:20]:
                if line.strip():
                    objects.append(json.loads(line))
    except Exception as exc:
        return {"json_parse": "ERROR", "json_error": type(exc).__name__}

    if not objects:
        return meta
    meta["json_parse"] = "PASS"
    keys = {
        "schema", "id", "artifact_id", "status", "claim_ceiling", "purpose",
        "version", "next_training_gate", "next_scientific_gate",
    }
    extracted: dict[str, Any] = {}
    for obj in objects:
        if isinstance(obj, dict):
            for key in keys:
                if key in obj and key not in extracted:
                    value = obj[key]
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        extracted[key] = value
    if extracted:
        meta["declared_metadata"] = extracted
    return meta


def roles_for(path_text: str, content_lower: str) -> list[str]:
    probe = f"{path_text}\n{content_lower[:200000]}"
    roles = [name for name, pattern in ROLE_PATTERNS if pattern.search(probe)]
    if path_text.endswith(".py") or path_text.startswith(".github/workflows/"):
        roles.append("EXECUTABLE")
    if not roles:
        roles.append("CONTEXT")
    return sorted(set(roles))


def artifact_relevance(rel_lower: str, content_lower: str) -> tuple[int, list[str]]:
    haystack = f"{rel_lower}\n{content_lower[:400000]}"
    hits: list[str] = []
    score = 0
    for term, weight in ARTIFACT_TERMS.items():
        if term in haystack:
            hits.append(term)
            score += weight
    return score, sorted(hits)


def inspect_file(root: Path, path: Path) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    record: dict[str, Any] = {
        "schema": f"{SCHEMA}.file",
        "path": rel,
        "size_bytes": len(raw),
        "raw_sha256": sha256_bytes(raw),
        "suffix": path.suffix.lower(),
        "domain": classify_domain(rel),
    }
    if len(raw) > MAX_TEXT_BYTES:
        record.update({
            "text_inspected": False,
            "reason": "TEXT_SIZE_LIMIT",
            "scientific_authority": "PROVENANCE_ONLY_UNTIL_EXPLICITLY_OPENED",
        })
        return record

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
        record["utf8_decode_replacement"] = True

    lower = text.lower()
    record["text_inspected"] = True
    record["roles"] = roles_for(rel, lower)
    score, hits = artifact_relevance(rel.lower(), lower)
    record["artifact_routing_score"] = score
    record["artifact_routing_terms"] = hits
    record["artifact_lane_candidate"] = score >= 5
    record["contains_negative_or_failure_language"] = any(term in lower for term in NEGATIVE_TERMS)
    record["may_be_used_as_artifact_training_label"] = False
    record["corpus_use"] = [
        "METHOD_MEMORY", "FAILURE_MEMORY", "PROVENANCE_ROUTING", "SOURCE_ROUTE_DISCOVERY"
    ]
    record.update(extract_json_metadata(text, path.suffix.lower()))
    return record


def build_scan(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    records = [inspect_file(root, p) for p in iter_repo_files(root)]
    records.sort(key=lambda r: r["path"])

    queue: list[dict[str, Any]] = []
    for rec in records:
        if rec.get("artifact_lane_candidate"):
            queue.append({
                "path": rec["path"],
                "raw_sha256": rec["raw_sha256"],
                "domain": rec["domain"],
                "roles": rec.get("roles", []),
                "routing_score": rec.get("artifact_routing_score", 0),
                "routing_terms": rec.get("artifact_routing_terms", []),
                "allowed_use": "METHOD_OR_EVIDENCE_ROUTE_CONTEXT_ONLY",
                "automatic_label_authority": False,
            })
    queue.sort(key=lambda q: (-q["routing_score"], q["path"]))

    domains = Counter(rec["domain"] for rec in records)
    roles = Counter(role for rec in records for role in rec.get("roles", []))
    negative = sum(bool(rec.get("contains_negative_or_failure_language")) for rec in records)
    invalid_json = sum(rec.get("json_parse") == "ERROR" for rec in records)

    receipt = {
        "schema": f"{SCHEMA}.receipt",
        "status": "PASS" if records and invalid_json == 0 else "PASS_WITH_JSON_PARSE_WARNINGS" if records else "FAIL_EMPTY_SCAN",
        "root": str(root.resolve()),
        "files_indexed": len(records),
        "artifact_lane_candidates": len(queue),
        "files_with_negative_or_failure_language": negative,
        "domain_counts": dict(sorted(domains.items())),
        "role_counts": dict(sorted(roles.items())),
        "json_parse_errors": invalid_json,
        "record_stream_sha256": canonical_stream_sha256(records),
        "routing_queue_sha256": canonical_stream_sha256(queue),
        "assimilation_boundary": {
            "repository_corpus_is_supervised_artifact_truth": False,
            "repo_content_may_teach": [
                "METHODS", "SCHEMAS", "FAILURE_MODES", "NEGATIVE_RESULTS",
                "PROVENANCE", "SOURCE_ROUTES", "FALSIFICATION_PATTERNS",
            ],
            "artifact_labels_require_dedicated_label_rail": True,
            "nuclear_context_may_enter_classifier_training": False,
            "legacy_status_inherits_scientific_authority": False,
        },
        "claim_ceiling": "REPOSITORY_ASSIMILATION_BUILDS_RESEARCH_MEMORY_AND_ROUTING_ONLY__IT_DOES_NOT_BY_ITSELF_TRAIN_OR_VALIDATE_THE_POSS1_IMAGE_CLASSIFIER",
    }
    return records, queue, receipt


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            fh.write("\n")


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "protocols").mkdir()
        (root / "research/uap-nuclear").mkdir(parents=True)
        (root / "notes").mkdir()
        (root / "protocols/foundation.json").write_text(json.dumps({
            "schema": "fixture", "status": "ACTIVE", "claim_ceiling": "fixture"
        }), encoding="utf-8")
        (root / "research/uap-nuclear/plate.json").write_text(json.dumps({
            "schema": "fixture.plate", "status": "REFUTED", "purpose": "POSS-I plate edge WCS morphology"
        }), encoding="utf-8")
        (root / "notes/context.md").write_text("Historical report only; no labels.\n", encoding="utf-8")
        records1, queue1, receipt1 = build_scan(root)
        records2, queue2, receipt2 = build_scan(root)
        assert len(records1) == 3
        assert receipt1["record_stream_sha256"] == receipt2["record_stream_sha256"]
        assert receipt1["routing_queue_sha256"] == receipt2["routing_queue_sha256"]
        assert any(q["path"].endswith("plate.json") for q in queue1)
        assert all(not r.get("may_be_used_as_artifact_training_label") for r in records1)
        assert receipt1["assimilation_boundary"]["artifact_labels_require_dedicated_label_rail"]
        return {
            "schema": f"{SCHEMA}.self_test",
            "status": "PASS",
            "deterministic_index": True,
            "artifact_routing": True,
            "negative_memory_preserved": True,
            "automatic_label_authority": False,
            "fixture_files": len(records1),
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="TOPA repository assimilation engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    scan = sub.add_parser("scan")
    scan.add_argument("--root", default=".")
    scan.add_argument("--out-index", required=True)
    scan.add_argument("--out-queue", required=True)
    scan.add_argument("--receipt", required=True)
    args = ap.parse_args()

    if args.cmd == "self-test":
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0

    root = Path(args.root).resolve()
    records, queue, receipt = build_scan(root)
    write_jsonl(Path(args.out_index), records)
    write_jsonl(Path(args.out_queue), queue)
    write_json(Path(args.receipt), receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
