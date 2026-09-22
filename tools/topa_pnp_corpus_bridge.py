#!/usr/bin/env python3
"""Build the JANUS P-vs-NP corpus and routing-weight sidecar.

This module is intentionally NOT a truth scorer. It:
- normalizes Drive index records + TOPA discoveries;
- deduplicates only on stable hard identities;
- flags semantic near-duplicates for review;
- updates routing/attention weights in a separate ledger;
- preserves all provenance and contradictory/negative materials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

SCHEMA_CORPUS = "janus.topa.pnp_corpus.v1"
SCHEMA_LEDGER = "janus.topa.pnp_corpus_weight_ledger.v1"
SCHEMA_DEDUPE = "janus.topa.pnp_corpus_dedupe_receipt.v1"
TOKEN = re.compile(r"[a-z0-9]+", re.I)
ARXIV = re.compile(r"(?:arxiv[:/]|abs/)([0-9]{4}\.[0-9]{4,5}|[a-z-]+/[0-9]{7})(?:v\d+)?", re.I)
DOI = re.compile(r"(10\.\d{4,9}/[-._;()/:a-z0-9]+)", re.I)

SOURCE_QUALITY = {
    "OFFICIAL_STATUS": 0.95,
    "PEER_REVIEWED": 0.90,
    "PEER_REVIEWED_OPEN": 0.90,
    "PEER_REVIEWED_CLASSIC": 0.92,
    "PEER_REVIEWED_LINEAGE": 0.86,
    "SEALED_SOURCE_BOUND_INVENTORY": 1.00,
    "AUTHORITATIVE_CHECKPOINT": 1.00,
    "SOURCE_HISTORY_CLOSURE": 0.98,
    "THEOREM_LEVEL_FALSIFIER": 1.00,
    "PASS_WITH_REPAIRS": 0.98,
    "SEALED_POSTMORTEM": 0.98,
    "SEALED_BARRIER": 1.00,
    "FALSIFIED_AS_UNIVERSAL_POLY_REPRESENTATION_ROUTE": 1.00,
    "PREPRINT_2026": 0.68,
    "PREPRINT_OR_PAPER_LINEAGE": 0.65,
    "SCOPED_THEOREM": 0.92,
    "SCOPED_THEOREM_CANDIDATE": 0.75,
    "REPRESENTATION_DEPENDENCE_CONTROL": 0.90,
    "EXACT_CALCULUS_OPEN_GENERAL_COMPLEXITY": 0.82,
    "DISCOVERY_METADATA_ONLY": 0.35,
}

FRONTIER_EXPANSION = {
    "projection", "project", "forgetting", "existential", "quantification",
    "compositional", "composition", "interaction", "certificate", "invariant",
    "constraint", "csp", "sat", "cnf", "affine", "xor", "polymorphism",
    "compilation", "knowledge", "dnnf", "obdd", "circuit", "resolution",
    "elimination", "tractable", "consistency", "backdoor", "treewidth",
    "pp", "subpowers", "schaefer", "horn", "krom", "lower", "bound",
}


def canon(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(obj: Any) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def norm(x: Any) -> str:
    if isinstance(x, list):
        x = " ".join(str(v) for v in x)
    return " ".join(TOKEN.findall(str(x or "").casefold()))


def tokens(x: Any) -> set[str]:
    return set(TOKEN.findall(str(x or "").casefold()))


def strip_arxiv_version(value: str) -> str:
    return re.sub(r"v\d+$", "", value.strip(), flags=re.I)


def extract_doi(rec: dict[str, Any]) -> str:
    raw = str(rec.get("doi") or "")
    m = DOI.search(raw)
    if m:
        return m.group(1).casefold().rstrip(".,)")
    for field in ("source_url", "url", "archive_id"):
        m = DOI.search(str(rec.get(field) or ""))
        if m:
            return m.group(1).casefold().rstrip(".,)")
    return ""


def extract_arxiv(rec: dict[str, Any]) -> str:
    raw = str(rec.get("arxiv_id") or "")
    if raw:
        return strip_arxiv_version(raw.casefold())
    for field in ("archive_id", "source_url", "url"):
        m = ARXIV.search(str(rec.get(field) or ""))
        if m:
            return strip_arxiv_version(m.group(1).casefold())
    return ""


def normalized_url(rec: dict[str, Any]) -> str:
    raw = str(rec.get("source_url") or rec.get("github_url") or rec.get("drive_note") or rec.get("url") or "").strip()
    if not raw:
        return ""
    try:
        u = urlparse(raw)
        host = u.netloc.casefold().removeprefix("www.")
        path = re.sub(r"/+$", "", u.path)
        return f"{host}{path}".casefold()
    except Exception:
        return norm(raw)


HARD_IDENTITY_ORDER = (
    "DOI",
    "CANONICAL_ARXIV_ID",
    "NORMALIZED_TITLE_PLUS_FIRST_AUTHOR",
    "NORMALIZED_SOURCE_URL",
    "EXACT_CONTENT_SHA256",
)


def publication_keys(rec: dict[str, Any]) -> list[tuple[str, str]]:
    """Return every hard identity carried by a record, strongest first.

    A single-primary-key implementation misses cross-provider duplicates when,
    for example, one provider exposes a DOI while another exposes only arXiv
    plus the same title/author.  Keep every usable identity so records can be
    joined transitively, while weaker joins are blocked on conflicting strong
    identifiers.
    """
    out: list[tuple[str, str]] = []
    doi = extract_doi(rec)
    if doi:
        out.append(("DOI", f"doi:{doi}"))
    arxiv = extract_arxiv(rec)
    if arxiv:
        out.append(("CANONICAL_ARXIV_ID", f"arxiv:{arxiv}"))
    title = norm(rec.get("title"))
    authors = rec.get("authors") or []
    first_author = norm(authors[0]) if isinstance(authors, list) and authors else norm(rec.get("first_author"))
    if title and first_author:
        out.append(("NORMALIZED_TITLE_PLUS_FIRST_AUTHOR", f"title_author:{title}|{first_author}"))
    url = normalized_url(rec)
    if url:
        out.append(("NORMALIZED_SOURCE_URL", f"url:{url}"))
    digest = str(rec.get("source_record_sha256") or rec.get("record_sha256") or "")
    if digest:
        out.append(("EXACT_CONTENT_SHA256", f"sha256:{digest.casefold()}"))
    if not out:
        out.append(("EXACT_CONTENT_SHA256", f"record:{sha(rec)}"))
    return out


def publication_key(rec: dict[str, Any]) -> tuple[str, str]:
    return publication_keys(rec)[0]


def hard_identity_groups(rows: list[dict[str, Any]]) -> tuple[list[tuple[str, str, list[dict[str, Any]]]], list[dict[str, Any]]]:
    """Union records across all hard identifiers without weakly bridging contradictory IDs."""
    n = len(rows)
    parent = list(range(n))
    rank = [0] * n
    keys_by_row = [publication_keys(row) for row in rows]

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> int:
        ra, rb = find(a), find(b)
        if ra == rb:
            return ra
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        return ra

    def component_strong_ids(root: int, mode: str) -> set[str]:
        vals: set[str] = set()
        for i, candidates in enumerate(keys_by_row):
            if find(i) != root:
                continue
            vals.update(key for m, key in candidates if m == mode)
        return vals

    conflicts: list[dict[str, Any]] = []
    weak_modes = {"NORMALIZED_TITLE_PLUS_FIRST_AUTHOR", "NORMALIZED_SOURCE_URL"}
    for mode in HARD_IDENTITY_ORDER:
        owners: dict[str, list[int]] = {}
        for i, candidates in enumerate(keys_by_row):
            for m, key in candidates:
                if m == mode:
                    owners.setdefault(key, []).append(i)
        for token, idxs in sorted(owners.items()):
            if len(idxs) < 2:
                continue
            anchor = idxs[0]
            for idx in idxs[1:]:
                ra, rb = find(anchor), find(idx)
                if ra == rb:
                    continue
                if mode in weak_modes:
                    doi_a, doi_b = component_strong_ids(ra, "DOI"), component_strong_ids(rb, "DOI")
                    ax_a, ax_b = component_strong_ids(ra, "CANONICAL_ARXIV_ID"), component_strong_ids(rb, "CANONICAL_ARXIV_ID")
                    doi_conflict = bool(doi_a and doi_b and doi_a.isdisjoint(doi_b))
                    arxiv_conflict = bool(ax_a and ax_b and ax_a.isdisjoint(ax_b))
                    if doi_conflict or arxiv_conflict:
                        conflicts.append({
                            "identity_mode": mode,
                            "identity": token,
                            "action": "FLAG_ONLY__STRONG_ID_CONFLICT__DO_NOT_MERGE",
                            "doi_left": sorted(doi_a),
                            "doi_right": sorted(doi_b),
                            "arxiv_left": sorted(ax_a),
                            "arxiv_right": sorted(ax_b),
                        })
                        continue
                union(ra, rb)
                anchor = find(anchor)

    components: dict[int, list[int]] = {}
    for i in range(n):
        components.setdefault(find(i), []).append(i)

    grouped: list[tuple[str, str, list[dict[str, Any]]]] = []
    for idxs in components.values():
        chosen: tuple[str, str] | None = None
        for mode in HARD_IDENTITY_ORDER:
            vals = sorted({key for i in idxs for m, key in keys_by_row[i] if m == mode})
            if len(vals) == 1:
                chosen = (mode, vals[0])
                break
        if chosen is None:
            chosen = ("EXACT_CONTENT_SHA256", "component:" + sha(sorted(
                key for i in idxs for _, key in keys_by_row[i]
            )))
        grouped.append((chosen[0], chosen[1], [rows[i] for i in idxs]))
    grouped.sort(key=lambda item: item[1])
    return grouped, conflicts


def stable_id(key: str) -> str:
    return "pnp-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def read_json(path: Path | None, default: Any) -> Any:
    if path is None or not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            out.append(obj)
    return out


def flatten_drive_index(index: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for kind, collection in (("INTERNAL_AUTHORITY", index.get("internal_authority") or []),
                             ("OPEN_ACCESS_MATERIAL", index.get("open_access_materials") or [])):
        for src in collection:
            if not isinstance(src, dict):
                continue
            rec = dict(src)
            rec["provider"] = "JANUS_DRIVE_INDEX"
            rec["corpus_kind"] = kind
            rec["archive_id"] = rec.get("id")
            rec["text"] = " ".join(str(rec.get(k) or "") for k in ("why_relevant", "blocker", "use_when", "anti_loop"))
            rec["relation_tags"] = ["P_VS_NP", kind]
            rec["scientific_authority"] = "ROUTING_MEMORY_REQUIRES_SOURCE_VERIFICATION"
            rec["claim_ceiling"] = "INDEX_METADATA_DOES_NOT_PROMOTE_SOURCE_CLAIMS"
            rows.append(rec)
    return rows


def flatten_provenance(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for r in rows:
        p = {
            "provider": r.get("provider"),
            "archive_id": r.get("archive_id"),
            "source_url": r.get("source_url") or r.get("github_url") or r.get("drive_note"),
            "query_provenance": r.get("query_provenance"),
            "source_record_sha256": r.get("source_record_sha256") or r.get("record_sha256"),
        }
        key = json.dumps(p, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def quality_hint(rec: dict[str, Any]) -> float:
    status = str(rec.get("status") or rec.get("scientific_authority") or "")
    if status in SOURCE_QUALITY:
        return SOURCE_QUALITY[status]
    if rec.get("provider") == "JANUS_DRIVE_INDEX":
        return 0.80
    return 0.35


def frontier_terms(index: dict[str, Any]) -> set[str]:
    frontier = index.get("next_frontier") or {}
    raw = " ".join(str(frontier.get(k) or "") for k in ("missing_object", "status"))
    terms = tokens(raw) | FRONTIER_EXPANSION
    for law in index.get("anti_loop_laws") or []:
        terms |= tokens(law)
    return terms


def relevance(rec: dict[str, Any], frontier: set[str]) -> float:
    raw = " ".join([
        str(rec.get("title") or ""),
        str(rec.get("text") or ""),
        str(rec.get("why_relevant") or ""),
        str(rec.get("blocker") or ""),
        " ".join(map(str, rec.get("relation_tags") or [])),
        " ".join(map(str, rec.get("matched_families") or [])),
    ])
    ts = tokens(raw)
    if not ts:
        return 0.0
    overlap = len(ts & frontier)
    denom = max(8.0, math.sqrt(len(ts) * max(1, len(frontier))))
    score = overlap / denom
    if "p" in ts and "np" in ts:
        score += 0.10
    if {"sat", "cnf"} & ts:
        score += 0.08
    return max(0.0, min(1.0, score * 2.2))


def title_similarity(a: str, b: str) -> float:
    A, B = tokens(a), tokens(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def build(index: dict[str, Any], discoveries: list[dict[str, Any]],
          previous_corpus: dict[str, Any] | None, previous_ledger: dict[str, Any] | None) -> tuple[dict, dict, dict]:
    auth = index.get("scientific_authority") or {}
    if index.get("schema") != "JANUS_P_VS_NP_MATERIALS_INDEX":
        raise RuntimeError("PNP_CORPUS_INDEX_SCHEMA_REJECTED")
    if auth.get("P_VS_NP") != "OPEN" or auth.get("SUCCESSOR_ALGORITHM") != "LOCKED":
        raise RuntimeError("PNP_CORPUS_AUTHORITY_FIREWALL_REJECTED")

    drive_rows = flatten_drive_index(index)
    all_rows = drive_rows + discoveries
    grouped_rows, identity_conflicts = hard_identity_groups(all_rows)

    prev_keys: set[str] = set()
    prev_identity_to_record_ids: dict[str, set[str]] = {}
    if isinstance(previous_corpus, dict):
        for row in previous_corpus.get("records") or []:
            if not isinstance(row, dict):
                continue
            rid = str(row.get("record_id") or "")
            primary = str(row.get("publication_key") or "")
            keys = {primary} if primary else set()
            keys.update(key for _, key in publication_keys(row))
            prev_keys.update(keys)
            if rid:
                for key in keys:
                    prev_identity_to_record_ids.setdefault(key, set()).add(rid)

    old_weights = {}
    if isinstance(previous_ledger, dict):
        old_weights = {str(r.get("record_id")): r for r in previous_ledger.get("weights") or [] if r.get("record_id")}

    frontier = frontier_terms(index)
    corpus_records = []
    weight_rows = []
    merged_groups = []
    new_record_ids: set[str] = set()
    for identity_mode, key, rows in grouped_rows:
        rows = sorted(rows, key=lambda r: (
            quality_hint(r),
            float(r.get("route_score") or 0),
            str(r.get("updated") or r.get("published") or ""),
        ), reverse=True)
        base = dict(rows[0])
        current_identity_keys = {identity for r in rows for _, identity in publication_keys(r)}
        previous_record_ids = sorted({
            rid for identity in current_identity_keys
            for rid in prev_identity_to_record_ids.get(identity, set())
        })
        if len(previous_record_ids) == 1:
            record_id = previous_record_ids[0]
            novelty = 0.15
        else:
            record_id = stable_id(key)
            novelty = 0.15 if key in prev_keys else 1.0
        if len(previous_record_ids) > 1:
            identity_conflicts.append({
                "identity_mode": "PREVIOUS_CORPUS_LINEAGE",
                "identity": key,
                "action": "FLAG_ONLY__AMBIGUOUS_PREVIOUS_RECORD_IDS",
                "previous_record_ids": previous_record_ids,
            })
        if novelty == 1.0:
            new_record_ids.add(record_id)
        q = max(quality_hint(r) for r in rows)
        rel = max(relevance(r, frontier) for r in rows)
        priority = max(0.0, min(1.0, 0.35*q + 0.45*rel + 0.20*novelty))
        aliases = sorted({str(r.get("archive_id") or r.get("id") or "") for r in rows if r.get("archive_id") or r.get("id")})
        titles = sorted({str(r.get("title") or "") for r in rows if r.get("title")})
        rec = {
            "record_id": record_id,
            "publication_key": key,
            "identity_mode": identity_mode,
            "title": base.get("title") or (titles[0] if titles else ""),
            "authors": base.get("authors") or [],
            "doi": extract_doi(base) or None,
            "arxiv_id": extract_arxiv(base) or None,
            "source_url": base.get("source_url") or base.get("github_url") or base.get("drive_note"),
            "status": base.get("status") or base.get("review_state") or "UNEXAMINED",
            "provider": base.get("provider"),
            "corpus_kind": base.get("corpus_kind") or "DISCOVERY",
            "why_relevant": base.get("why_relevant"),
            "blocker": base.get("blocker"),
            "text": base.get("text") or "",
            "relation_tags": sorted({str(t) for r in rows for t in (r.get("relation_tags") or [])}),
            "aliases": aliases,
            "provenance": flatten_provenance(rows),
            "duplicate_record_count": len(rows),
            "independence_credit": 1,
            "routing": {
                "source_quality_hint": round(q, 6),
                "frontier_relevance_weight": round(rel, 6),
                "novelty_weight": round(novelty, 6),
                "attention_priority": round(priority, 6),
                "weights_are_truth": False,
            },
        }
        corpus_records.append(rec)
        old = old_weights.get(record_id)
        changed = not old or any(abs(float(old.get(k) or 0)-v) > 1e-9 for k, v in (
            ("source_quality_hint", q),
            ("frontier_relevance_weight", rel),
            ("novelty_weight", novelty),
            ("attention_priority", priority),
        ))
        rationale = [
            "SOURCE_STATUS_ROUTING_HINT_ONLY",
            "FRONTIER_TERM_OVERLAP",
            "UNSEEN_PUBLICATION_BONUS" if novelty == 1.0 else "ALREADY_PRESENT_IN_PREVIOUS_CORPUS",
        ]
        previous_priority = old.get("attention_priority") if old else None
        history = list(old.get("history") or []) if old else []
        if changed or not history:
            history.append({
                "revision": (int(history[-1].get("revision", len(history))) + 1) if history else 1,
                "from_attention_priority": previous_priority,
                "to_attention_priority": round(priority, 6),
                "delta": round(priority - float(previous_priority or 0.0), 6) if previous_priority is not None else None,
                "source_quality_hint": round(q, 6),
                "frontier_relevance_weight": round(rel, 6),
                "novelty_weight": round(novelty, 6),
                "rationale": rationale,
            })
        history = history[-16:]
        weight_rows.append({
            "record_id": record_id,
            "publication_key": key,
            "title": rec["title"],
            "source_quality_hint": round(q, 6),
            "frontier_relevance_weight": round(rel, 6),
            "novelty_weight": round(novelty, 6),
            "attention_priority": round(priority, 6),
            "previous_attention_priority": previous_priority,
            "changed": changed,
            "rationale": rationale,
            "history": history,
        })
        if len(rows) > 1:
            merged_groups.append({
                "publication_key": key,
                "identity_mode": identity_mode,
                "record_count": len(rows),
                "title": rec["title"],
                "aliases": aliases,
            })

    # Near-semantic duplicates are review flags only; they are never merged here.
    near = []
    candidates = sorted(corpus_records, key=lambda r: r["record_id"])
    for i, a in enumerate(candidates):
        if not a.get("title"):
            continue
        for b in candidates[i+1:]:
            if not b.get("title"):
                continue
            sim = title_similarity(str(a["title"]), str(b["title"]))
            if sim >= 0.92 and a["publication_key"] != b["publication_key"]:
                near.append({
                    "a": a["record_id"],
                    "b": b["record_id"],
                    "title_similarity": round(sim, 6),
                    "action": "FLAG_ONLY__DO_NOT_AUTO_MERGE",
                })

    corpus_records.sort(key=lambda r: (-float(r["routing"]["attention_priority"]), r["record_id"]))
    weight_rows.sort(key=lambda r: (-float(r["attention_priority"]), r["record_id"]))
    new_count = len(new_record_ids)
    corpus = {
        "schema": SCHEMA_CORPUS,
        "status": "READY_READ_ONLY_RESEARCH_CORPUS",
        "P_VS_NP": "OPEN",
        "D1": auth.get("D1", "EMPTY"),
        "successor_algorithm": "LOCKED",
        "record_count": len(corpus_records),
        "new_publication_count": new_count,
        "drive_index_version": index.get("version"),
        "drive_index_sha256": sha(index),
        "records": corpus_records,
        "authority": {
            "truth": False,
            "proof": False,
            "scientific_claim_promotion": False,
            "fundamentum_mutation": False,
            "weights_are_truth": False,
        },
        "laws": [
            "CORPUS_PRESENCE != SCIENTIFIC_VALIDITY",
            "ATTENTION_WEIGHT != TRUTH",
            "DUPLICATE_PUBLICATION != INDEPENDENT_CONFIRMATION",
            "NEAR_DUPLICATE_FLAG != HARD_MERGE",
            "P_VS_NP = OPEN",
        ],
    }
    corpus["semantic_sha256"] = sha(corpus)

    ledger = {
        "schema": SCHEMA_LEDGER,
        "status": "ACTIVE_ROUTING_WEIGHTS",
        "corpus_semantic_sha256": corpus["semantic_sha256"],
        "weight_count": len(weight_rows),
        "weights": weight_rows,
        "authority": {
            "weights_are_truth": False,
            "weights_are_evidence": False,
            "weights_change_theorem_status": False,
            "source_documents_immutable": True,
        },
        "formula": "0.35*source_quality_hint + 0.45*frontier_relevance_weight + 0.20*novelty_weight",
        "history_required": True,
        "history_limit_per_record": 16,
    }
    ledger["semantic_sha256"] = sha(ledger)

    receipt = {
        "schema": SCHEMA_DEDUPE,
        "status": "PASS",
        "input_drive_records": len(drive_rows),
        "input_discovery_records": len(discoveries),
        "input_total_records": len(all_rows),
        "unique_hard_identities": len(corpus_records),
        "records_collapsed": len(all_rows) - len(corpus_records),
        "merged_groups": merged_groups,
        "hard_identity_conflicts": identity_conflicts,
        "near_duplicate_review_flags": near,
        "new_publication_count": new_count,
        "hard_identity_order": [
            "DOI",
            "CANONICAL_ARXIV_ID",
            "NORMALIZED_TITLE_PLUS_FIRST_AUTHOR",
            "NORMALIZED_SOURCE_URL",
            "EXACT_CONTENT_SHA256",
        ],
        "near_semantic_duplicate_policy": "FLAG_ONLY__DO_NOT_AUTO_MERGE",
        "corpus_semantic_sha256": corpus["semantic_sha256"],
        "ledger_semantic_sha256": ledger["semantic_sha256"],
        "laws": [
            "DUPLICATE_PUBLICATION_RECORDS_DO_NOT_CREATE_INDEPENDENT_BRIDGES",
            "NEGATIVE_AND_CONTRADICTORY_RESULTS_ARE_PRESERVED",
            "P_VS_NP_IS_OPEN",
        ],
    }
    return corpus, ledger, receipt


def self_test() -> dict[str, Any]:
    idx = {
        "schema": "JANUS_P_VS_NP_MATERIALS_INDEX",
        "scientific_authority": {"P_VS_NP": "OPEN", "D1": "EMPTY", "SUCCESSOR_ALGORITHM": "LOCKED"},
        "anti_loop_laws": [],
        "internal_authority": [],
        "open_access_materials": [],
        "next_frontier": {"missing_object": "projection compositional invariant certificate"},
    }
    disc = [
        {"provider": "ARXIV", "archive_id": "2601.00001v1", "arxiv_id": "2601.00001v1", "title": "Projection Invariant", "authors": ["A"], "text": "projection invariant certificate", "status": "DISCOVERY_METADATA_ONLY"},
        {"provider": "OPENALEX", "archive_id": "x", "title": "Projection Invariant", "authors": ["A"], "source_url": "https://arxiv.org/abs/2601.00001v2", "text": "same paper", "status": "DISCOVERY_METADATA_ONLY"},
        {"provider": "OPENALEX", "archive_id": "doi-mirror", "doi": "10.1234/projection.1", "title": "Projection Invariant", "authors": ["A"], "source_url": "https://doi.org/10.1234/projection.1", "text": "same publication with DOI metadata only", "status": "DISCOVERY_METADATA_ONLY"},
        {"provider": "OPENALEX", "archive_id": "different-doi", "doi": "10.1234/projection.2", "title": "Projection Invariant", "authors": ["A"], "source_url": "https://doi.org/10.1234/projection.2", "text": "different strong identifier", "status": "DISCOVERY_METADATA_ONLY"},
    ]
    c, w, d = build(idx, disc, None, None)
    assert c["record_count"] == 2
    assert d["records_collapsed"] == 2
    assert any(g["record_count"] == 3 for g in d["merged_groups"])
    assert d["hard_identity_conflicts"]
    assert all(r["independence_credit"] == 1 for r in c["records"])
    assert w["authority"]["weights_are_truth"] is False
    assert w["history_required"] is True
    assert w["weights"][0]["history"]
    return {
        "schema": "janus.topa.pnp_corpus_bridge.self_test.v1",
        "status": "PASS",
        "publication_dedupe": True,
        "sidecar_weights_only": True,
        "near_duplicates_auto_merged": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("self-test")
    b = sp.add_parser("build")
    b.add_argument("--index", required=True)
    b.add_argument("--discoveries", required=True)
    b.add_argument("--previous-corpus")
    b.add_argument("--previous-ledger")
    b.add_argument("--out-corpus", required=True)
    b.add_argument("--out-ledger", required=True)
    b.add_argument("--receipt", required=True)
    a = ap.parse_args()
    if a.cmd == "self-test":
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0

    index = read_json(Path(a.index), {})
    discoveries = read_jsonl(Path(a.discoveries))
    previous_corpus = read_json(Path(a.previous_corpus), None) if a.previous_corpus else None
    previous_ledger = read_json(Path(a.previous_ledger), None) if a.previous_ledger else None
    corpus, ledger, receipt = build(index, discoveries, previous_corpus, previous_ledger)
    for path, obj in (
        (Path(a.out_corpus), corpus),
        (Path(a.out_ledger), ledger),
        (Path(a.receipt), receipt),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "unique_hard_identities": receipt["unique_hard_identities"],
        "records_collapsed": receipt["records_collapsed"],
        "new_publication_count": receipt["new_publication_count"],
        "near_duplicate_review_flags": len(receipt["near_duplicate_review_flags"]),
        "corpus_semantic_sha256": receipt["corpus_semantic_sha256"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
