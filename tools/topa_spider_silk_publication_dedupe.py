#!/usr/bin/env python3
"""Publication-level dedupe for TOPA SPIDER SILK discovery outputs.

Different arXiv identifiers / versions / mirrors of the same work must not create
multiple independent research bridges. This layer is routing-only and never alters
the target JANUS algorithm.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from topa_spider_silk import make_bridge, sha

LAW = "DUPLICATE_PUBLICATION_RECORDS_DO_NOT_CREATE_INDEPENDENT_BRIDGES"


def norm(x: Any) -> str:
    if isinstance(x, list):
        x = " ".join(map(str, x))
    return " ".join(re.findall(r"[a-z0-9]+", str(x or "").casefold()))


def publication_key(c: dict[str, Any]) -> str:
    doi = norm(c.get("doi"))
    if doi:
        return "doi:" + doi
    title = norm(c.get("title"))
    authors = c.get("authors") or []
    first_author = norm(authors[0]) if authors else ""
    if title and first_author:
        return f"title_author:{title}|{first_author}"
    return "arxiv:" + str(c.get("arxiv_id") or "")


def flatten_prov(items: list[Any]) -> list[Any]:
    out = []
    seen = set()
    for x in items:
        vals = x if isinstance(x, list) else [x]
        for v in vals:
            if v is None:
                continue
            key = json.dumps(v, sort_keys=True, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
            if key not in seen:
                seen.add(key)
                out.append(v)
    return out


def dedupe_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for c in candidates:
        groups.setdefault(publication_key(c), []).append(c)

    kept: list[dict[str, Any]] = []
    merged_groups: list[dict[str, Any]] = []
    for key, rows in sorted(groups.items()):
        rows = sorted(rows, key=lambda r: (float(r.get("route_score") or 0), str(r.get("updated") or ""), str(r.get("arxiv_id") or "")), reverse=True)
        base = dict(rows[0])
        ids = sorted({str(r.get("arxiv_id")) for r in rows if r.get("arxiv_id")})
        hashes = sorted({str(r.get("record_sha256")) for r in rows if r.get("record_sha256")})
        fam = sorted({f for r in rows for f in (r.get("matched_families") or [])})
        base["matched_families"] = fam
        base["route_score"] = max(float(r.get("route_score") or 0) for r in rows)
        base["publication_dedupe"] = {
            "key": key,
            "merged_arxiv_ids": ids,
            "merged_record_sha256s": hashes,
            "merged_query_provenance": flatten_prov([r.get("query_provenance") for r in rows]),
            "duplicate_record_count": len(rows),
            "independence_credit": 1,
            "rule": LAW,
        }
        kept.append(base)
        if len(rows) > 1:
            merged_groups.append({
                "publication_key": key,
                "canonical_arxiv_id": base.get("arxiv_id"),
                "title": base.get("title"),
                "merged_arxiv_ids": ids,
                "record_count": len(rows),
            })

    kept.sort(key=lambda r: (-float(r.get("route_score") or 0), str(r.get("arxiv_id") or "")))
    return kept, merged_groups


def run(data: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    live = data.setdefault("live_arxiv", {})
    before = list(live.get("candidates") or [])
    kept, merged = dedupe_candidates(before)
    live["pre_publication_dedupe_candidates"] = len(before)
    live["candidates"] = kept
    live["candidates_retained"] = len(kept)
    live["publication_dedupe"] = {
        "status": "PASS",
        "mode": "DOI_ELSE_NORMALIZED_TITLE_PLUS_FIRST_AUTHOR",
        "input_records": len(before),
        "unique_publications": len(kept),
        "records_collapsed": len(before) - len(kept),
        "merged_groups": merged,
        "law": LAW,
    }
    counts = Counter(f for c in kept for f in (c.get("matched_families") or []))
    live["family_counts_after_publication_dedupe"] = dict(sorted(counts.items()))

    canonical = [b for b in data.get("research_bridges", []) if b.get("source_kind") == "CANONICAL_EXTERNAL_SOURCE"]
    live_bridges = []
    for c in kept:
        b = make_bridge(str(c.get("arxiv_id") or ""), "LIVE_ARXIV_CANDIDATE", c.get("matched_families") or [], config, float(c.get("route_score") or 0))
        b["source_aliases"] = c.get("publication_dedupe", {}).get("merged_arxiv_ids", [])
        b["independence_credit"] = 1
        live_bridges.append(b)
    data["research_bridges"] = canonical + live_bridges
    data["laws"] = sorted(set((data.get("laws") or []) + [LAW]))
    data.pop("semantic_sha256", None)
    data["semantic_sha256"] = sha(data)
    return data


def self_test() -> dict[str, Any]:
    cfg = {"janus_anchors": []}
    d = {
        "live_arxiv": {"candidates": [
            {"arxiv_id":"1202.1","title":"Same Paper","authors":["A. Author"],"doi":None,"route_score":2,"matched_families":["X"],"updated":"2020"},
            {"arxiv_id":"1208.2","title":"Same  Paper","authors":["A. Author"],"doi":None,"route_score":3,"matched_families":["X","Y"],"updated":"2021"},
            {"arxiv_id":"9","title":"Different Paper","authors":["A. Author"],"doi":None,"route_score":1,"matched_families":["Z"],"updated":"2022"},
        ]},
        "research_bridges": [],
        "laws": [],
    }
    out = run(d, cfg)
    assert out["live_arxiv"]["candidates_retained"] == 2
    assert out["live_arxiv"]["publication_dedupe"]["records_collapsed"] == 1
    same = next(x for x in out["live_arxiv"]["candidates"] if x["title"].startswith("Same"))
    assert same["publication_dedupe"]["independence_credit"] == 1
    assert set(same["publication_dedupe"]["merged_arxiv_ids"]) == {"1202.1","1208.2"}
    assert set(same["matched_families"]) == {"X","Y"}
    return {"schema":"hawkar.topa.spider.silk.publication_dedupe.self_test.v1","status":"PASS","duplicate_independence":True}


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("self-test")
    p = sp.add_parser("dedupe")
    p.add_argument("--input", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--receipt", required=True)
    a = ap.parse_args()
    if a.cmd == "self-test":
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0
    inp = Path(a.input)
    outp = Path(a.out)
    data = run(json.loads(inp.read_text()), json.loads(Path(a.config).read_text()))
    outp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    r = {
        "schema":"hawkar.topa.spider.silk.publication_dedupe.receipt.v1",
        "status":"PASS",
        "input_candidates":data["live_arxiv"].get("pre_publication_dedupe_candidates"),
        "unique_publications":data["live_arxiv"].get("candidates_retained"),
        "records_collapsed":data["live_arxiv"]["publication_dedupe"]["records_collapsed"],
        "output_sha256":hashlib.sha256(outp.read_bytes()).hexdigest(),
        "semantic_sha256":data["semantic_sha256"],
        "laws":[LAW,"P_VS_NP_IS_OPEN"],
    }
    Path(a.receipt).write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    print(json.dumps(r, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
