#!/usr/bin/env python3
"""Bridge TOPA repository-assimilation memory into SPIDER discovery seeds.

Repository memory is allowed to steer discovery but is never archival evidence
or supervised truth. The bridge reads the deterministic repo index, enriches
research-memory entries with bounded UTF-8 excerpts from the checkout, and
emits SPIDER-compatible JSONL records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SKIP_DOMAINS = {"EXECUTABLE_INFRASTRUCTURE"}
SKIP_PREFIXES = (".github/", "tools/")


def canon(o: Any) -> str:
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_hash(r: dict[str, Any]) -> str:
    clean = {k:v for k,v in r.items() if k != "record_sha256"}
    return hashlib.sha256(canon(clean).encode("utf-8")).hexdigest()


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def bounded_excerpt(root: Path, rel: str, max_bytes: int) -> str:
    path = root / rel
    if not path.is_file():
        return ""
    raw = path.read_bytes()[:max_bytes]
    text = raw.decode("utf-8", errors="replace")
    return " ".join(text.split())


def convert(index_path: Path, root: Path, max_bytes: int = 80000):
    out = []
    skipped = 0
    for rec in read_jsonl(index_path):
        rel = str(rec.get("path") or "")
        domain = str(rec.get("domain") or "GENERAL")
        if not rel or domain in SKIP_DOMAINS or rel.startswith(SKIP_PREFIXES):
            skipped += 1
            continue
        if not rec.get("text_inspected", False):
            skipped += 1
            continue
        meta = rec.get("declared_metadata") or {}
        roles = [str(x) for x in (rec.get("roles") or [])]
        routing = [str(x) for x in (rec.get("artifact_routing_terms") or [])]
        excerpt = bounded_excerpt(root, rel, max_bytes)
        summary_bits = [
            f"Repository path: {rel}.",
            f"Domain: {domain}.",
            "Roles: " + ", ".join(roles) + "." if roles else "",
            "Routing terms: " + ", ".join(routing) + "." if routing else "",
            "Declared metadata: " + canon(meta) if meta else "",
            excerpt,
        ]
        tags = sorted(set([domain] + roles + routing))
        r = {
            "schema":"hawkar.topa.spider_repo_seed.v1",
            "provider":"TOPA_REPO",
            "archive_id":rel,
            "title":rel,
            "text":" ".join(x for x in summary_bits if x)[:160000],
            "source_url":"https://github.com/Hawkar-usls/TOPA/blob/main/" + rel,
            "relation_tags":tags,
            "review_state":"RESEARCH_MEMORY",
            "scientific_authority":"DISCOVERY_CONTEXT_ONLY",
            "claim_ceiling":"REPOSITORY_MEMORY_MAY_ROUTE_DISCOVERY__IT_IS_NOT_ARCHIVAL_EVIDENCE_OR_CLAIM_TRUTH",
            "repo_provenance":{
                "path":rel,
                "raw_sha256":rec.get("raw_sha256"),
                "domain":domain,
                "roles":roles,
                "contains_negative_or_failure_language":bool(rec.get("contains_negative_or_failure_language")),
            },
        }
        r["record_sha256"] = record_hash(r)
        out.append(r)
    out.sort(key=lambda r:r["archive_id"])
    return out, skipped


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "research").mkdir()
        (root / "tools").mkdir()
        (root / "research/a.json").write_text('{"artifact_id":"A","purpose":"retrocausal null test"}', encoding="utf-8")
        (root / "tools/x.py").write_text('print(1)', encoding="utf-8")
        idx = root / "index.jsonl"
        rows = [
            {"path":"research/a.json","domain":"GENERAL","text_inspected":True,"raw_sha256":"a","roles":["HUNT"],"artifact_routing_terms":[],"declared_metadata":{"artifact_id":"A"}},
            {"path":"tools/x.py","domain":"EXECUTABLE_INFRASTRUCTURE","text_inspected":True,"raw_sha256":"b","roles":["EXECUTABLE"]},
        ]
        write_jsonl(idx, rows)
        out, skipped = convert(idx, root, 10000)
        assert len(out) == 1 and skipped == 1
        assert "retrocausal" in out[0]["text"]
        assert out[0]["scientific_authority"] == "DISCOVERY_CONTEXT_ONLY"
        return {"schema":"hawkar.topa.spider_seed_bridge.self_test.v1","status":"PASS","research_memory_included":True,"executable_noise_excluded":True,"truth_authority":False}


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("self-test")
    q = sp.add_parser("build")
    q.add_argument("--index", required=True)
    q.add_argument("--root", default=".")
    q.add_argument("--out", required=True)
    q.add_argument("--receipt", required=True)
    q.add_argument("--max-bytes", type=int, default=80000)
    a = ap.parse_args()
    if a.cmd == "self-test":
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
        return 0
    rows, skipped = convert(Path(a.index), Path(a.root).resolve(), a.max_bytes)
    write_jsonl(Path(a.out), rows)
    receipt = {
        "schema":"hawkar.topa.spider_seed_bridge.receipt.v1",
        "status":"PASS" if rows else "FAIL_EMPTY",
        "seed_records":len(rows),
        "skipped_records":skipped,
        "stream_sha256":hashlib.sha256("".join(canon(r)+"\n" for r in rows).encode("utf-8")).hexdigest(),
        "law":"REPOSITORY_MEMORY_IS_DISCOVERY_CONTEXT_NOT_ARCHIVAL_EVIDENCE"
    }
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
