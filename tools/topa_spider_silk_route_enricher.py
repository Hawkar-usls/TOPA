#!/usr/bin/env python3
"""Mission-local route + lineage enrichment for TOPA SPIDER SILK.

This post-processor fixes two research-routing problems without touching the target
algorithm:
1) new pattern families must route to explicit JANUS research anchors rather than
   depending on a hard-coded legacy table;
2) distinct publication records from the same author/core-result lineage must be
   visible as related, without being falsely collapsed as exact duplicates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Any

from topa_spider_silk import sha

ROUTING_LAW = "MISSION_LOCAL_FAMILY_ROUTING_OVERRIDES_LEGACY_EMPTY_ROUTING"
LINEAGE_LAW = "PUBLICATION_LINEAGE_IS_NOT_INDEPENDENT_REPLICATION"

STOP = {
    "a","an","and","are","as","at","be","between","by","for","from","in","into","is","of","on","or","the","to","using","with",
    "proof","proofs","system","systems","algorithm","algorithms","resolution","sat"
}


def norm(x: Any) -> str:
    if isinstance(x, list):
        x = " ".join(map(str, x))
    return " ".join(re.findall(r"[a-z0-9]+", str(x or "").casefold()))


def tokens(x: Any, *, drop_stop: bool = False) -> set[str]:
    ts = set(norm(x).split())
    return {t for t in ts if t not in STOP} if drop_stop else ts


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def title_similarity(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, float]:
    na, nb = norm(a.get("title")), norm(b.get("title"))
    seq = SequenceMatcher(None, na, nb).ratio() if na and nb else 0.0
    jac = jaccard(tokens(na, drop_stop=True), tokens(nb, drop_stop=True))
    return round(seq, 6), round(jac, 6)


def author_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    aa = {norm(x) for x in (a.get("authors") or []) if norm(x)}
    bb = {norm(x) for x in (b.get("authors") or []) if norm(x)}
    return round(jaccard(aa, bb), 6)


def abstract_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    # Token Jaccard is deliberately conservative and deterministic. This is a
    # routing signal, not semantic equivalence.
    return round(jaccard(tokens(a.get("abstract")), tokens(b.get("abstract"))), 6)


def family_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    return round(jaccard(set(a.get("matched_families") or []), set(b.get("matched_families") or [])), 6)


def lineage_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for a, b in combinations(candidates, 2):
        aid, bid = str(a.get("arxiv_id") or ""), str(b.get("arxiv_id") or "")
        if not aid or not bid:
            continue
        tseq, tj = title_similarity(a, b)
        aj = author_similarity(a, b)
        abj = abstract_similarity(a, b)
        fj = family_similarity(a, b)
        # Strong lineage gate: substantial author overlap plus strong textual/core
        # overlap. It intentionally does not assert that the papers are identical.
        strong = aj >= 0.50 and (tj >= 0.45 or tseq >= 0.72) and abj >= 0.40
        # Slightly looser route only when both title and abstract remain similar
        # and the same research families are involved.
        related = aj >= 0.34 and tj >= 0.35 and abj >= 0.30 and fj >= 0.50
        if not (strong or related):
            continue
        out.append({
            "lineage_id": "LINEAGE:" + hashlib.sha256("|".join(sorted([aid,bid])).encode()).hexdigest()[:16],
            "members": [aid, bid],
            "titles": [a.get("title"), b.get("title")],
            "authors_overlap_jaccard": aj,
            "title_sequence_similarity": tseq,
            "title_token_jaccard": tj,
            "abstract_token_jaccard": abj,
            "family_jaccard": fj,
            "classification": "STRONG_SHARED_CORE_RESULT_LINEAGE_CANDIDATE" if strong else "RELATED_RESEARCH_LINEAGE_CANDIDATE",
            "claim": "ROUTING_RELATION_ONLY__NOT_DUPLICATE_IDENTITY__NOT_INDEPENDENT_REPLICATION",
            "manual_review": "REQUIRED_BEFORE_TREATING_SHARED_CLAIMS_AS_INDEPENDENT_EVIDENCE",
        })
    out.sort(key=lambda x: (-x["abstract_token_jaccard"], -x["title_sequence_similarity"], x["members"]))
    return out


def enrich(data: dict[str, Any], pattern_cfg: dict[str, Any], route_cfg: dict[str, Any]) -> dict[str, Any]:
    anchor_by_id = {x["id"]: x for x in pattern_cfg.get("janus_anchors", [])}
    fam_routes = route_cfg.get("family_anchor_routes", {})

    unrouted = []
    routed_count = 0
    for b in data.get("research_bridges", []):
        ids = []
        seen = set()
        for fam in b.get("matched_families", []) or []:
            for aid in fam_routes.get(fam, []):
                if aid not in seen:
                    seen.add(aid)
                    ids.append(aid)
        anchors = [anchor_by_id[i] for i in ids if i in anchor_by_id]
        b["janus_insertion_points"] = anchors
        b["mission_local_route"] = {
            "family_route_ids": ids,
            "resolved_anchor_ids": [x["id"] for x in anchors],
            "claim": "RESEARCH_LOCATION_ONLY__NOT_ALGORITHM_RECOMMENDATION",
        }
        if anchors:
            routed_count += 1
        else:
            unrouted.append({"source_id": b.get("source_id"), "matched_families": b.get("matched_families", [])})

    candidates = data.setdefault("live_arxiv", {}).get("candidates", []) or []
    lineages = lineage_candidates(candidates)
    data["lineage_analysis"] = {
        "status": "PASS",
        "method": "DETERMINISTIC_TITLE_AUTHOR_ABSTRACT_FAMILY_OVERLAP",
        "candidate_pairs": len(lineages),
        "lineages": lineages,
        "law": LINEAGE_LAW,
        "note": "Lineage preserves both publications. It only warns that shared claims from the same author/core-result lineage are not independent replication by default."
    }
    data["routing_enrichment"] = {
        "status": "PASS" if not unrouted else "PARTIAL",
        "bridges_total": len(data.get("research_bridges", [])),
        "bridges_routed": routed_count,
        "bridges_unrouted": len(unrouted),
        "unrouted": unrouted,
        "route_config_artifact": route_cfg.get("artifact_id"),
        "law": ROUTING_LAW,
    }
    data["artifact_id"] = route_cfg.get("artifact_id") or data.get("artifact_id")
    data.setdefault("mission", {})["mission_id"] = route_cfg.get("mission_id") or data.get("mission", {}).get("mission_id")
    data["laws"] = sorted(set((data.get("laws") or []) + (route_cfg.get("laws") or []) + [ROUTING_LAW, LINEAGE_LAW]))
    data.pop("semantic_sha256", None)
    data["semantic_sha256"] = sha(data)
    return data


def self_test() -> dict[str, Any]:
    cfg = {"janus_anchors":[{"id":"A","path":"x"},{"id":"B","path":"y"}]}
    routes = {"artifact_id":"T","mission_id":"M","family_anchor_routes":{"F":["A"],"G":["B"]},"laws":["P_VS_NP_IS_OPEN"]}
    data = {
        "research_bridges":[{"source_id":"x","matched_families":["F"],"janus_insertion_points":[]}],
        "live_arxiv":{"candidates":[
            {"arxiv_id":"1","title":"Improved separation of regular resolution from clause learning","authors":["A Author","B Author"],"abstract":"we prove graph tautologies have polynomial pool proofs and clause learning proofs","matched_families":["F","G"]},
            {"arxiv_id":"2","title":"Improved separations of regular resolution from clause learning proof systems","authors":["A Author","B Author","C Author"],"abstract":"we prove graph tautologies have polynomial pool proofs and clause learning refutations","matched_families":["F","G"]}
        ]},
        "laws":[]
    }
    out=enrich(data,cfg,routes)
    assert out["routing_enrichment"]["bridges_unrouted"]==0
    assert out["research_bridges"][0]["janus_insertion_points"][0]["id"]=="A"
    assert out["lineage_analysis"]["candidate_pairs"]>=1
    return {"schema":"hawkar.topa.spider.silk.route_enricher.self_test.v1","status":"PASS","routing":True,"lineage":True}


def main() -> int:
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("self-test")
    p=sp.add_parser("enrich")
    p.add_argument("--input",required=True)
    p.add_argument("--pattern-config",required=True)
    p.add_argument("--route-config",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--receipt",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test":
        print(json.dumps(self_test(),indent=2,sort_keys=True)); return 0
    out=enrich(json.loads(Path(a.input).read_text()), json.loads(Path(a.pattern_config).read_text()), json.loads(Path(a.route_config).read_text()))
    op=Path(a.out); op.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    rec={
        "schema":"hawkar.topa.spider.silk.route_enricher.receipt.v1",
        "status":"PASS" if out["routing_enrichment"]["bridges_unrouted"]==0 else "PARTIAL",
        "artifact_id":out.get("artifact_id"),
        "bridges_total":out["routing_enrichment"]["bridges_total"],
        "bridges_routed":out["routing_enrichment"]["bridges_routed"],
        "bridges_unrouted":out["routing_enrichment"]["bridges_unrouted"],
        "lineage_candidate_pairs":out["lineage_analysis"]["candidate_pairs"],
        "output_sha256":hashlib.sha256(op.read_bytes()).hexdigest(),
        "semantic_sha256":out["semantic_sha256"],
        "laws":[ROUTING_LAW,LINEAGE_LAW,"P_VS_NP_IS_OPEN"]
    }
    Path(a.receipt).write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
