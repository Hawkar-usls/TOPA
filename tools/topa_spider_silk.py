#!/usr/bin/env python3
"""TOPA SPIDER SILK — Spider Investigative Link Kernel.

Turns a frozen research mission plus live arXiv discovery corpora into a compact,
provenance-preserving link kernel. SILK ranks routes for investigation; it does
not promote papers, search rank, diagnostic correlations, or finite experiments
into mathematical theorems.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "hawkar.topa.spider.silk.v1"
LAWS = [
    "SEARCH_HIT_IS_NOT_EVIDENCE",
    "PAPER_CLAIM_IS_NOT_A_JANUS_THEOREM",
    "SILK_LINK_IS_A_RESEARCH_ROUTE_NOT_A_PROOF",
    "DIAGNOSTIC_LOCALIZATION_IS_NOT_A_CAUSAL_OR_COMPLEXITY_PROOF",
    "ARTMONEY_PRINCIPLE_IS_DIAGNOSTIC_NOT_A_SAT_SPEEDUP",
    "EXPLICIT_STATE_SCAN_IS_NOT_IMPLICIT_2_POW_N_SEARCH",
    "VALIDITY_PRESERVING_PERTURBATION_ONLY",
    "CHEAP_VERIFICATION_IS_NOT_CHEAP_DISCOVERY",
    "FAILED_FETCH_IS_NOT_PROOF_OF_ABSENCE",
    "FINITE_N43_SUCCESS_IS_NOT_AN_ASYMPTOTIC_PROOF",
    "P_VS_NP_IS_OPEN",
]

ANCHOR_ROUTING = {
    "DIFFERENTIAL_STATE_NARROWING": ["POLICY0T_TRACE_CODE", "C023_JANUS_FC_LOCAL"],
    "FIRST_DIVERGENCE": ["POLICY0T_TRACE_CODE", "TOPA_FORENSIC_JOURNAL"],
    "DELTA_DEBUGGING": ["POLICY0T_TRACE_CODE", "C023_JANUS_FC_LOCAL"],
    "CAUSE_EFFECT_CHAIN": ["POLICY0T_TRACE_CODE"],
    "DYNAMIC_SLICING": ["C021_TRACE_PROOF_BRIDGE", "POLICY0T_TRACE_CODE"],
    "VALIDITY_PRESERVING_PERTURBATION": ["POLICY0T_TRACE_CODE", "PF2_SHARING_TRILEMMA"],
    "PROOF_TRACE": ["C021_TRACE_PROOF_BRIDGE", "C023_JANUS_FC_LOCAL"],
    "DRAT_FRAT_LRAT": ["C021_TRACE_PROOF_BRIDGE", "C023_JANUS_FC_LOCAL"],
    "BACKWARD_PROOF_TRIMMING": ["C021_TRACE_PROOF_BRIDGE", "C023_JANUS_FC_LOCAL"],
    "UNSAT_CORE": ["C023_JANUS_FC_LOCAL", "TOPA_FORENSIC_JOURNAL"],
    "CONFLICT_GRAPH_CUT": ["C021_TRACE_PROOF_BRIDGE", "C023_JANUS_FC_LOCAL"],
    "BACKDOOR_STRUCTURE": ["LIVE_WIDTH_DP", "TOPA_FORENSIC_JOURNAL"],
    "BOUNDARY_WIDTH": ["LIVE_WIDTH_DP"],
    "PROOF_COMPLEXITY": ["C023_GT_ROBUSTNESS", "PF2_SHARING_TRILEMMA"],
    "RESOURCE_ACCOUNTING": ["TOPA_FORENSIC_JOURNAL", "PF2_SHARING_TRILEMMA"],
}


def canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(obj: Any) -> str:
    payload = obj if isinstance(obj, str) else canon(obj)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def norm(text: Any) -> str:
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)
    return " ".join(re.findall(r"[a-z0-9]+", str(text or "").casefold()))


def compile_families(config: dict[str, Any]) -> dict[str, list[str]]:
    return {
        f["id"]: [norm(a) for a in f.get("aliases", []) if norm(a)]
        for f in config.get("families", [])
    }


def paper_surface(rec: dict[str, Any]) -> tuple[str, str]:
    title = norm(rec.get("title"))
    body = norm(" ".join([
        str(rec.get("abstract") or ""),
        " ".join(rec.get("authors") or []),
        " ".join(rec.get("categories") or []),
        str(rec.get("comments") or ""),
        str(rec.get("journal_ref") or ""),
    ]))
    return title, body


def match_record(rec: dict[str, Any], families: dict[str, list[str]]) -> tuple[list[str], dict[str, Any], float]:
    title, body = paper_surface(rec)
    matched: list[str] = []
    details: dict[str, Any] = {}
    score = 0.0
    for fid, aliases in families.items():
        title_hits = sorted({a for a in aliases if a and a in title})
        body_hits = sorted({a for a in aliases if a and a in body})
        if title_hits or body_hits:
            matched.append(fid)
            details[fid] = {"title_aliases": title_hits, "body_aliases": body_hits[:12]}
            score += 2.0 if title_hits else 1.0
            score += min(1.0, 0.15 * len(set(title_hits + body_hits)))
    return sorted(matched), details, round(score, 6)


def dedup_arxiv(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for r in records:
        aid = str(r.get("arxiv_id") or "").strip()
        if not aid:
            continue
        prev = by_id.get(aid)
        if prev is None or str(r.get("updated") or "") >= str(prev.get("updated") or ""):
            by_id[aid] = r
    return [by_id[k] for k in sorted(by_id)]


def collect_arxiv(paths: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    provenance = []
    for raw in paths:
        p = Path(raw)
        corpus = p / "arxiv-corpus.jsonl" if p.is_dir() or not p.suffix else p
        rs = read_jsonl(corpus)
        rows.extend(rs)
        receipt = corpus.parent / "arxiv-investigation-receipt.json"
        prov: dict[str, Any] = {"corpus": str(corpus), "records": len(rs)}
        if corpus.exists():
            prov["raw_sha256"] = hashlib.sha256(corpus.read_bytes()).hexdigest()
        if receipt.exists():
            rr = load_json(receipt)
            prov["investigation_receipt"] = rr
        provenance.append(prov)
    return dedup_arxiv(rows), provenance


def anchor_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {x["id"]: x for x in config.get("janus_anchors", [])}


def make_bridge(source_id: str, source_kind: str, families: list[str], config: dict[str, Any], score: float | None = None) -> dict[str, Any]:
    amap = anchor_map(config)
    anchors = []
    seen = set()
    for f in families:
        for aid in ANCHOR_ROUTING.get(f, []):
            if aid not in seen and aid in amap:
                seen.add(aid)
                anchors.append(amap[aid])
    return {
        "source_id": source_id,
        "source_kind": source_kind,
        "matched_families": families,
        "route_score": score,
        "janus_insertion_points": anchors,
        "allowed_use": "HYPOTHESIS_GENERATION__DIAGNOSTIC_DESIGN__TRACE_LOCALIZATION__COUNTEREXAMPLE_SEARCH",
        "forbidden_use": "NO_P_VS_NP_PROMOTION__NO_FREE_SEMANTIC_ORACLE__NO_UNCHARGED_EXPONENTIAL_CANDIDATE_MATERIALIZATION",
        "claim_authority": "RESEARCH_ROUTE_ONLY",
    }


def assemble(config: dict[str, Any], arxiv_records: list[dict[str, Any]], arxiv_prov: list[dict[str, Any]], max_candidates: int = 80) -> dict[str, Any]:
    fam = compile_families(config)
    selected = []
    family_counts = Counter()
    for rec in arxiv_records:
        matched, details, score = match_record(rec, fam)
        if not matched:
            continue
        family_counts.update(matched)
        selected.append({
            "arxiv_id": rec.get("arxiv_id"),
            "title": rec.get("title"),
            "authors": rec.get("authors"),
            "published": rec.get("published"),
            "updated": rec.get("updated"),
            "categories": rec.get("categories"),
            "abstract": rec.get("abstract"),
            "doi": rec.get("doi"),
            "abs_url": rec.get("abs_url"),
            "pdf_url": rec.get("pdf_url"),
            "record_sha256": rec.get("record_sha256"),
            "matched_families": matched,
            "match_details": details,
            "route_score": score,
            "query_provenance": rec.get("query_provenance"),
            "claim_authority": "ARXIV_DISCOVERY_METADATA_AND_PAPER_CLAIMS_REQUIRE_REVIEW",
        })
    selected.sort(key=lambda r: (-r["route_score"], str(r.get("arxiv_id"))))
    selected = selected[:max_candidates]

    canonical_bridges = [
        make_bridge(x["id"], "CANONICAL_EXTERNAL_SOURCE", x.get("families", []), config)
        for x in config.get("canonical_external_sources", [])
    ]
    live_bridges = [
        make_bridge(x["arxiv_id"], "LIVE_ARXIV_CANDIDATE", x["matched_families"], config, x["route_score"])
        for x in selected
    ]

    high_priority = [
        {
            "priority": "P0",
            "route": "N43_EXACT_TAIL_FIRST",
            "reason": "The current mission explicitly freezes the existing algorithmic road. Capture exact N=43 T/Smax/Uraw tails before introducing a new runtime mechanism.",
            "experiment": "N43-01",
        },
        {
            "priority": "P0",
            "route": "FIRST_DIVERGENCE_OVER_EXISTING_TRACE",
            "reason": "JANUS-FC_local and Policy-0T already expose the state/reason/event fields needed for a GOOD/BAD differential trace without inventing a new solver primitive.",
            "experiment": "DSN-01",
        },
        {
            "priority": "P1",
            "route": "VALIDITY_PRESERVING_DELTA_DEBUGGING",
            "reason": "If a hostile state is captured, minimize differences by perturbing the deterministic generator/transition trace rather than arbitrary proof-state bytes.",
            "experiment": "DSN-02",
        },
        {
            "priority": "P1",
            "route": "BACKWARD_PROOF_DEPENDENCY_SLICE",
            "reason": "For compatible UNSAT proof logs, intersect backward proof dependencies with the state-delta slice. Agreement is a stronger diagnostic than either slice alone but remains finite evidence.",
            "experiment": "TRACE-01",
        },
        {
            "priority": "P2",
            "route": "STRUCTURAL_BACKDOOR_AND_BOUNDARY_DIAGNOSTICS",
            "reason": "Backdoor depth/treewidth/live-width are orthogonal structural observables; useful only if their construction and input-relative costs are explicit.",
            "experiment": "GRAPH-01",
        },
    ]

    out = {
        "schema": SCHEMA,
        "artifact_id": "TOPA-SPIDER-SILK-JANUS-PROOF-STATE-FIRST-DIVERGENCE-2026-08-27-v1.0",
        "silk_expansion": config.get("silk"),
        "status": "PASS",
        "mission": {
            "mission_id": config.get("mission_id"),
            "purpose": config.get("purpose"),
            "current_checkpoint": config.get("current_checkpoint"),
        },
        "canonical_external_sources": config.get("canonical_external_sources", []),
        "live_arxiv": {
            "records_scanned": len(arxiv_records),
            "candidates_retained": len(selected),
            "family_counts_before_topk": dict(sorted(family_counts.items())),
            "provenance": arxiv_prov,
            "candidates": selected,
        },
        "janus_anchors": config.get("janus_anchors", []),
        "research_bridges": canonical_bridges + live_bridges,
        "high_priority_routes": high_priority,
        "planned_experiments": config.get("planned_experiments", []),
        "negative_and_boundary_findings": [
            "ARTMONEY_STYLE_DIFFERENTIAL_NARROWING_HAS_A_STRONG_METHOD_ANALOGUE_IN_DELTA_DEBUGGING__THIS_IS_DIAGNOSTIC_NOT_A_SAT_COMPLEXITY_RESULT",
            "BACKWARD_PROOF_TRIMMING_CAN_LOCALIZE_NECESSARY_CLAUSE_DEPENDENCIES_FOR_A_GIVEN_PROOF__THIS_IS_NOT_A_UNIVERSAL_CAUSE_OR_LOWER_BOUND",
            "MINIMAL_UNSAT_CORE_EXTRACTION_IS_USEFUL_OFFLINE_BUT_MINIMALITY_COST_CANNOT_BE_ASSUMED_FREE",
            "GENERAL_SEMANTIC_EQUIVALENCE_OR_CANONICALIZATION_CANNOT_BE_INSERTED_AS_A_FREE_NARROWING_ORACLE",
            "NO_EXTERNAL_METHOD_FOUND_BY_SILK_RESOLVES_THE_CURRENT_N43_TAIL_OR_P_VS_NP_BY_ITSELF",
        ],
        "laws": sorted(set(LAWS + config.get("laws", []))),
        "claim_ceiling": "DISCOVERY_DIAGNOSTICS_AND_EXACT_FINITE_EXPERIMENT_DESIGN_ONLY__P_VS_NP_OPEN",
    }
    out["semantic_sha256"] = sha({k: v for k, v in out.items() if k != "semantic_sha256"})
    return out


def self_test() -> dict[str, Any]:
    cfg = {
        "silk": "Spider Investigative Link Kernel",
        "mission_id": "T",
        "families": [
            {"id": "DELTA_DEBUGGING", "aliases": ["delta debugging"]},
            {"id": "PROOF_TRACE", "aliases": ["proof trace"]},
        ],
        "janus_anchors": [
            {"id": "POLICY0T_TRACE_CODE", "path": "x"},
            {"id": "C023_JANUS_FC_LOCAL", "path": "y"},
        ],
        "canonical_external_sources": [],
        "planned_experiments": [],
        "laws": ["P_VS_NP_IS_OPEN"],
    }
    recs = [
        {"arxiv_id": "1", "title": "Delta debugging for proof traces", "abstract": "proof trace analysis", "authors": [], "categories": [], "updated": "2026", "record_sha256": "a"},
        {"arxiv_id": "2", "title": "Unrelated astronomy", "abstract": "stars", "authors": [], "categories": [], "updated": "2026", "record_sha256": "b"},
    ]
    d = assemble(cfg, recs, [], 10)
    assert d["status"] == "PASS"
    assert d["live_arxiv"]["candidates_retained"] == 1
    assert set(d["live_arxiv"]["candidates"][0]["matched_families"]) == {"DELTA_DEBUGGING", "PROOF_TRACE"}
    assert "P_VS_NP_IS_OPEN" in d["laws"]
    return {"schema": SCHEMA + ".self_test", "status": "PASS", "selective": True, "p_vs_np_open": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("self-test")
    a = sp.add_parser("assemble")
    a.add_argument("--config", required=True)
    a.add_argument("--arxiv", action="append", default=[])
    a.add_argument("--out", required=True)
    a.add_argument("--receipt", required=True)
    a.add_argument("--max-candidates", type=int, default=80)
    args = ap.parse_args()
    if args.cmd == "self-test":
        print(json.dumps(self_test(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    cfg = load_json(args.config)
    records, prov = collect_arxiv(args.arxiv)
    d = assemble(cfg, records, prov, args.max_candidates)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "schema": SCHEMA + ".receipt",
        "status": d["status"],
        "artifact_id": d["artifact_id"],
        "output": str(out),
        "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "semantic_sha256": d["semantic_sha256"],
        "arxiv_records_scanned": d["live_arxiv"]["records_scanned"],
        "arxiv_candidates_retained": d["live_arxiv"]["candidates_retained"],
        "research_bridges": len(d["research_bridges"]),
        "laws": ["SILK_LINK_IS_A_RESEARCH_ROUTE_NOT_A_PROOF", "P_VS_NP_IS_OPEN"],
    }
    rp = Path(args.receipt)
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
