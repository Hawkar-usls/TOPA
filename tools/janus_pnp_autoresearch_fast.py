#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ASSOC_URL = "https://raw.githubusercontent.com/Hawkar-usls/iNaiHR/janus/fundamentum-associative-memory/data/fundamentum-associative/ASSOCIATIONS.json"
FORGE_URL = "https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/janus/autonomous-keymaster-lockpick/janus_model/autonomous-keymaster/KEYMASTER_AUTONOMOUS_FORGE_LATEST.json"
UA = "TOPA-JANUS-PNP-Autoresearch-Fast/1.0 (+https://github.com/Hawkar-usls/TOPA)"

BASE_QUERIES = [
    "independent transversal maximum degree two partitioned graph algorithm",
    "multilinear monomial read twice Pi Sigma 3 Pi 2 algorithm",
    "XOR parity constraints knowledge compilation vtree width exact algorithm",
    "Tseitin parity structured d-DNNF lower bounds treewidth",
    "bounded occurrence 3-SAT exact structural decomposition algorithm",
    "Boolean CSP affine quotient parity decomposition polynomial algorithm",
]

ROTATIONS = [
    [
        "rainbow independent set paths cycles partition constraints",
        "partitioned independent set matching augmentation degree two",
        "squarefree monomial bounded occurrence arithmetic formula",
    ],
    [
        "GF2 affine quotient residual width SAT exact algorithm",
        "matroid parity matching parity constraints SAT decomposition",
        "branchwidth rankwidth parity CSP exact dynamic programming",
    ],
    [
        "separator signatures SAT dynamic programming exact",
        "proof carrying elimination SAT width",
        "circuit SAT knowledge compilation exact transformation polynomial",
    ],
    [
        "XOR circuits parity decision diagram TDD",
        "factor width CNF parameterized complexity SAT",
        "Tseitin formulas structured decomposable circuits",
    ],
]


def request_json(url: str, timeout: float = 12.0) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def safe_json(url: str) -> dict:
    try:
        value = request_json(url, 15.0)
        return value if isinstance(value, dict) else {}
    except Exception as exc:
        return {"status": "UNAVAILABLE", "error": f"{type(exc).__name__}:{exc}"}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def normalize_doi(value: Any) -> str:
    doi = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi


def record_key(row: dict) -> tuple[str, str]:
    doi = normalize_doi(row.get("doi"))
    if doi:
        return ("DOI", doi)
    archive = str(row.get("archive_id") or "").strip().lower()
    if archive:
        return ("ARCHIVE", archive)
    url = str(row.get("source_url") or "").strip().lower()
    if url:
        return ("URL", url)
    title = " ".join(str(row.get("title") or "").lower().split())
    return ("TITLE", title or digest(row))


def read_jsonl(path: str | None) -> list[dict]:
    if not path or not Path(path).exists():
        return []
    rows: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def merge_records(*groups: list[dict]) -> list[dict]:
    merged: dict[tuple[str, str], dict] = {}
    for group in groups:
        for row in group:
            if isinstance(row, dict):
                merged[record_key(row)] = row
    return list(merged.values())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def forge_queries(forge: dict, limit: int) -> list[str]:
    cycle = int(forge.get("cycle_count") or 0) if isinstance(forge, dict) else 0
    target = forge.get("target") or {} if isinstance(forge, dict) else {}
    target_phrase = " ".join([
        str(target.get("from_type") or "").replace("_", " ").lower(),
        str(target.get("to_type") or "").replace("_", " ").lower(),
    ]).strip()

    raw: list[str] = []
    if target_phrase:
        raw += [
            target_phrase + " exact polynomial algorithm",
            target_phrase + " decomposition lower bound",
        ]
    raw += BASE_QUERIES
    raw += ROTATIONS[cycle % len(ROTATIONS)]

    out: list[str] = []
    seen: set[str] = set()
    for query in raw:
        query = " ".join(query.split())
        key = query.lower()
        if query and key not in seen:
            seen.add(key)
            out.append(query)
        if len(out) >= limit:
            break
    return out


def crossref(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode({
        "query.bibliographic": query,
        "rows": max(1, min(limit, 20)),
        "select": "DOI,title,abstract,URL,published",
    })
    data = request_json("https://api.crossref.org/works?" + params)
    rows: list[dict] = []
    for item in ((data.get("message") or {}).get("items") or []):
        titles = item.get("title") or []
        title = titles[0] if isinstance(titles, list) and titles else str(titles or "")
        doi = normalize_doi(item.get("DOI"))
        rows.append({
            "provider": "CROSSREF",
            "archive_id": doi or item.get("URL"),
            "doi": doi or None,
            "title": title,
            "text": str(item.get("abstract") or "")[:12000],
            "source_url": item.get("URL") or ("https://doi.org/" + doi if doi else ""),
            "relation_tags": ["P_VS_NP", "LITERATURE_DISCOVERY"],
            "review_state": "UNEXAMINED",
            "scientific_authority": "DISCOVERY_METADATA_ONLY",
            "claim_ceiling": "PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION",
        })
    return rows


def openalex(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode({"search": query, "per-page": max(1, min(limit, 20))})
    data = request_json("https://api.openalex.org/works?" + params)
    rows: list[dict] = []
    for item in data.get("results") or []:
        doi = normalize_doi(item.get("doi"))
        inv = item.get("abstract_inverted_index") or {}
        words: list[tuple[int, str]] = []
        for token, positions in inv.items():
            for pos in positions:
                words.append((int(pos), str(token)))
        rows.append({
            "provider": "OPENALEX",
            "archive_id": doi or item.get("id"),
            "doi": doi or None,
            "title": item.get("title") or "",
            "text": " ".join(token for _, token in sorted(words))[:12000],
            "source_url": item.get("doi") or item.get("id") or "",
            "relation_tags": ["P_VS_NP", "LITERATURE_DISCOVERY"],
            "review_state": "UNEXAMINED",
            "scientific_authority": "DISCOVERY_METADATA_ONLY",
            "claim_ceiling": "PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--prior-records")
    parser.add_argument("--max-queries", type=int, default=6)
    parser.add_argument("--per-source", type=int, default=10)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prior = read_jsonl(args.prior_records)
    forge = safe_json(FORGE_URL)
    assoc = safe_json(ASSOC_URL)
    queries = forge_queries(forge, max(1, args.max_queries))

    current: list[dict] = []
    receipts: list[dict] = []
    health = {
        "crossref": {"pass_queries": 0, "unavailable_queries": 0, "records_retrieved": 0},
        "openalex": {"pass_queries": 0, "unavailable_queries": 0, "records_retrieved": 0},
    }

    for query in queries:
        receipt = {"query": query, "crossref": {}, "openalex": {}}
        try:
            rows = crossref(query, args.per_source)
            current.extend(rows)
            receipt["crossref"] = {"status": "PASS", "records": len(rows)}
            health["crossref"]["pass_queries"] += 1
            health["crossref"]["records_retrieved"] += len(rows)
        except Exception as exc:
            receipt["crossref"] = {"status": "UNAVAILABLE", "error": f"{type(exc).__name__}:{exc}"}
            health["crossref"]["unavailable_queries"] += 1

        time.sleep(0.8)
        try:
            rows = openalex(query, args.per_source)
            current.extend(rows)
            receipt["openalex"] = {"status": "PASS", "records": len(rows)}
            health["openalex"]["pass_queries"] += 1
            health["openalex"]["records_retrieved"] += len(rows)
        except Exception as exc:
            receipt["openalex"] = {"status": "UNAVAILABLE", "error": f"{type(exc).__name__}:{exc}"}
            health["openalex"]["unavailable_queries"] += 1

        receipts.append(receipt)
        time.sleep(0.8)

    cycle_unique = merge_records(current)
    prior_keys = {record_key(row) for row in prior}
    novel = [row for row in cycle_unique if record_key(row) not in prior_keys]
    merged = merge_records(prior, cycle_unique)

    write_jsonl(out / "source-records.jsonl", merged)
    # Keep small deterministic graph artifacts for downstream consumers. They are discovery structure only.
    nodes = [
        {"id": f"paper:{i}", "title": row.get("title"), "provider": row.get("provider"), "source_url": row.get("source_url")}
        for i, row in enumerate(merged)
    ]
    write_jsonl(out / "spider-nodes.jsonl", nodes)
    write_jsonl(out / "spider-edges.jsonl", [])

    source_bytes = (out / "source-records.jsonl").read_bytes()
    spider = {
        "schema": "hawkar.topa.spider.receipt.v1",
        "status": "PASS",
        "documents": len(merged),
        "nodes": len(nodes),
        "edges": 0,
        "laws": [
            "GRAPH_EDGE_IS_NOT_CAUSATION",
            "DISCOVERY_METADATA_IS_NOT_PROOF",
            "REPEATED_SAME_SOURCE_IS_NOT_INDEPENDENT_WITNESS",
        ],
        "promotion_rule": "NO_AUTOMATIC_SCIENTIFIC_PROMOTION_FROM_DISCOVERY",
    }
    write_json(out / "spider-receipt.json", spider)

    source_live = any(v["pass_queries"] > 0 for v in health.values())
    status = "PASS_NOVEL_SOURCES_ADDED" if novel else ("PASS_STALLED_NO_NOVEL_SOURCES" if source_live else "DEGRADED_ALL_DISCOVERY_SOURCES_UNAVAILABLE")
    latest = {
        "schema": "janus.topa.pnp_autoresearch_cycle.v3",
        "status": status,
        "autoreserch_active": source_live,
        "query_seed_count": len(queries),
        "targeted_query_count": len(queries),
        "query_rotation": "ADAPTIVE_BY_FORGE_CYCLE",
        "query_receipts": receipts,
        "source_health": health,
        "prior_record_count": len(prior),
        "retrieved_cycle_record_count": len(cycle_unique),
        "novel_cycle_record_count": len(novel),
        "new_cycle_record_count": len(novel),
        "record_count": len(merged),
        "duplicate_cycle_record_count": max(0, len(cycle_unique) - len(novel)),
        "corpus_merge_policy": "APPEND_MERGE_HARD_DEDUPE__EMPTY_CYCLE_DOES_NOT_ERASE_HISTORY",
        "source_records_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "keymaster_forge": {
            "url": FORGE_URL,
            "status": forge.get("status"),
            "cycle_count": forge.get("cycle_count"),
            "state_sha256": forge.get("state_sha256"),
            "target": forge.get("target"),
            "query_is_evidence": False,
            "query_grants_authority": False,
        },
        "associative_memory": {
            "url": ASSOC_URL,
            "source_commit": assoc.get("source_commit"),
        },
        "spider_receipt": spider,
        "authority": {
            "truth": False,
            "proof": False,
            "scientific_claim_promotion": False,
            "fundamentum_mutation": False,
        },
        "claim_ceiling": "DISCOVERY_AND_CANDIDATE_RELATIONS_ONLY__NO_PNP_CLAIM_PROMOTION",
    }
    write_json(out / "LATEST.json", latest)
    print(json.dumps(latest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
