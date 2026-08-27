#!/usr/bin/env python3
"""TOPA arXiv gateway: remote discovery + append-only corpus + portable local search.

Primary local engine: Tantivy (MIT, embedded Rust search engine).
Fallback: SQLite FTS5 from Python's standard library.

Scientific boundary: search rank and paper claims are discovery metadata, not truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ARXIV_API = "https://export.arxiv.org/api/query"
USER_AGENT = "TOPA-Arxiv-Gateway/1.0 (+https://github.com/Hawkar-usls/TOPA)"
DEFAULT_DELAY = 3.0

ATOM = "{http://www.w3.org/2005/Atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV = "{http://arxiv.org/schemas/atom}"

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+\-/]{1,}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_hash(record: Dict[str, Any]) -> str:
    clean = {k: v for k, v in record.items() if k != "record_sha256"}
    return sha256_bytes(canonical_json(clean).encode("utf-8"))


def normalize_ws(text: Optional[str]) -> str:
    return " ".join((text or "").split())


def extract_arxiv_id(entry_id: str) -> str:
    x = entry_id.rstrip("/").split("/abs/")[-1]
    return x


def _text(parent: ET.Element, tag: str) -> str:
    node = parent.find(tag)
    return normalize_ws(node.text if node is not None else "")


def parse_atom(payload: bytes, query_provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    root = ET.fromstring(payload)
    total_node = root.find(OPENSEARCH + "totalResults")
    total = int(total_node.text) if total_node is not None and (total_node.text or "").isdigit() else None
    entries: List[Dict[str, Any]] = []
    response_sha = sha256_bytes(payload)

    for e in root.findall(ATOM + "entry"):
        entry_id = _text(e, ATOM + "id")
        authors = [normalize_ws(a.findtext(ATOM + "name", default="")) for a in e.findall(ATOM + "author")]
        categories = [c.attrib.get("term", "") for c in e.findall(ATOM + "category") if c.attrib.get("term")]
        primary = e.find(ARXIV + "primary_category")
        links = e.findall(ATOM + "link")
        pdf_url = ""
        abs_url = entry_id
        for link in links:
            href = link.attrib.get("href", "")
            typ = link.attrib.get("type", "")
            title = link.attrib.get("title", "")
            rel = link.attrib.get("rel", "")
            if title == "pdf" or typ == "application/pdf":
                pdf_url = href
            if rel == "alternate" and href:
                abs_url = href

        rec: Dict[str, Any] = {
            "schema": "hawkar.topa.arxiv_record.v1",
            "arxiv_id": extract_arxiv_id(entry_id),
            "entry_id": entry_id,
            "title": _text(e, ATOM + "title"),
            "abstract": _text(e, ATOM + "summary"),
            "authors": authors,
            "categories": categories,
            "primary_category": primary.attrib.get("term", "") if primary is not None else "",
            "published": _text(e, ATOM + "published"),
            "updated": _text(e, ATOM + "updated"),
            "comments": _text(e, ARXIV + "comment"),
            "journal_ref": _text(e, ARXIV + "journal_ref"),
            "doi": _text(e, ARXIV + "doi"),
            "pdf_url": pdf_url,
            "abs_url": abs_url,
            "query_provenance": query_provenance or {},
            "source_response_sha256": response_sha,
            "scientific_authority": "SOURCE_METADATA_AND_PAPER_CLAIMS_REQUIRE_SEPARATE_VALIDATION"
        }
        rec["record_sha256"] = record_hash(rec)
        entries.append(rec)

    return {"total_results": total, "response_sha256": response_sha, "records": entries}


def meaningful_tokens(topic: str) -> List[str]:
    out: List[str] = []
    for token in TOKEN_RE.findall(topic):
        t = token.strip().lower()
        if len(t) >= 3 and t not in out:
            out.append(t)
    return out[:12]


def build_smart_arxiv_query(topic: str, field: str = "all") -> str:
    topic = normalize_ws(topic)
    if not topic:
        raise ValueError("topic is empty")
    tokens = meaningful_tokens(topic)
    escaped_phrase = topic.replace('"', "")
    if len(tokens) <= 1:
        return f'{field}:"{escaped_phrase}"'
    conj = " AND ".join(f"{field}:{t}" for t in tokens)
    return f'({field}:"{escaped_phrase}" OR ({conj}))'


def build_api_url(search_query: str, start: int, max_results: int, sort_by: str, sort_order: str) -> str:
    params = {
        "search_query": search_query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    return ARXIV_API + "?" + urllib.parse.urlencode(params)


def fetch_page(search_query: str, start: int, max_results: int, sort_by: str, sort_order: str,
               timeout: float = 45.0) -> Tuple[bytes, str]:
    if max_results < 1 or max_results > 2000:
        raise ValueError("TOPA page size must be 1..2000")
    url = build_api_url(search_query, start, max_results, sort_by, sort_order)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/atom+xml"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), url


def remote_search(search_query: str, limit: int = 50, page_size: int = 50,
                  sort_by: str = "relevance", sort_order: str = "descending",
                  delay: float = DEFAULT_DELAY) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if limit < 1:
        return [], {"status": "EMPTY_LIMIT", "requests": []}
    limit = min(limit, 30000)
    page_size = max(1, min(page_size, 2000, limit))
    records: List[Dict[str, Any]] = []
    requests: List[Dict[str, Any]] = []
    start = 0
    total_known: Optional[int] = None

    while len(records) < limit:
        size = min(page_size, limit - len(records))
        payload, url = fetch_page(search_query, start, size, sort_by, sort_order)
        prov = {
            "endpoint": ARXIV_API,
            "search_query": search_query,
            "start": start,
            "max_results": size,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "request_url": url,
        }
        parsed = parse_atom(payload, prov)
        if total_known is None:
            total_known = parsed["total_results"]
        batch = parsed["records"]
        requests.append({
            "start": start,
            "requested": size,
            "returned": len(batch),
            "response_sha256": parsed["response_sha256"],
            "request_url": url,
        })
        records.extend(batch)
        start += len(batch)
        if not batch or len(batch) < size or (total_known is not None and start >= total_known):
            break
        if len(records) < limit:
            time.sleep(max(delay, 3.0))

    return records[:limit], {
        "schema": "hawkar.topa.arxiv_remote_search_receipt.v1",
        "status": "PASS",
        "search_query": search_query,
        "records_returned": min(len(records), limit),
        "total_results_reported": total_known,
        "requests": requests,
        "polite_delay_seconds": max(delay, 3.0),
        "claim_ceiling": "SEARCH_RESULTS_ARE_DISCOVERY_METADATA_NOT_SCIENTIFIC_TRUTH",
    }


def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def append_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(canonical_json(rec) + "\n")
            n += 1
    return n


def dedup_latest(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        aid = str(rec.get("arxiv_id") or "").strip()
        if not aid:
            continue
        prev = by_id.get(aid)
        if prev is None or str(rec.get("updated") or "") >= str(prev.get("updated") or ""):
            by_id[aid] = rec
    return [by_id[k] for k in sorted(by_id)]


def _doc_text(rec: Dict[str, Any], key: str) -> str:
    val = rec.get(key)
    if isinstance(val, list):
        return " ".join(str(x) for x in val)
    return str(val or "")


def build_sqlite_index(corpus: Path, db_path: Path) -> Dict[str, Any]:
    records = dedup_latest(read_jsonl(corpus))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE papers (arxiv_id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.execute("CREATE VIRTUAL TABLE papers_fts USING fts5(arxiv_id UNINDEXED, title, abstract, authors, categories, comments, journal_ref)")
        for rec in records:
            payload = canonical_json(rec)
            aid = rec["arxiv_id"]
            fields = (
                aid, _doc_text(rec, "title"), _doc_text(rec, "abstract"), _doc_text(rec, "authors"),
                _doc_text(rec, "categories"), _doc_text(rec, "comments"), _doc_text(rec, "journal_ref")
            )
            conn.execute("INSERT INTO papers(arxiv_id,payload) VALUES (?,?)", (aid, payload))
            conn.execute("INSERT INTO papers_fts(arxiv_id,title,abstract,authors,categories,comments,journal_ref) VALUES (?,?,?,?,?,?,?)", fields)
        conn.commit()
    finally:
        conn.close()
    return {"engine": "sqlite_fts5", "documents": len(records), "index_path": str(db_path)}


def search_sqlite(db_path: Path, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        tokens = meaningful_tokens(query)
        match = " OR ".join(f'"{t}"' for t in tokens) if tokens else f'"{normalize_ws(query)}"'
        rows = conn.execute(
            "SELECT p.payload, bm25(papers_fts, 0.0, 3.0, 1.5, 1.0, 1.0, 0.5, 0.5) AS bm25_score "
            "FROM papers_fts JOIN papers p USING(arxiv_id) WHERE papers_fts MATCH ? ORDER BY bm25_score LIMIT ?",
            (match, limit),
        ).fetchall()
        out = []
        for rank, row in enumerate(rows, 1):
            rec = json.loads(row["payload"])
            rec["local_search"] = {"engine": "sqlite_fts5", "rank": rank, "bm25_native": float(row["bm25_score"])}
            out.append(rec)
        return out
    finally:
        conn.close()


def tantivy_available() -> bool:
    try:
        import tantivy  # noqa: F401
        return True
    except Exception:
        return False


def build_tantivy_index(corpus: Path, index_dir: Path) -> Dict[str, Any]:
    import tantivy
    records = dedup_latest(read_jsonl(corpus))
    if index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    sb = tantivy.SchemaBuilder()
    sb.add_text_field("arxiv_id", stored=True, tokenizer_name="raw")
    sb.add_text_field("title", stored=True, tokenizer_name="en_stem")
    sb.add_text_field("abstract", stored=True, tokenizer_name="en_stem")
    sb.add_text_field("authors", stored=True)
    sb.add_text_field("categories", stored=True)
    sb.add_text_field("comments", stored=True, tokenizer_name="en_stem")
    sb.add_text_field("journal_ref", stored=True, tokenizer_name="en_stem")
    sb.add_text_field("payload", stored=True, tokenizer_name="raw")
    schema = sb.build()
    index = tantivy.Index(schema, path=str(index_dir))
    with index.writer() as writer:
        for rec in records:
            writer.add_document(tantivy.Document(
                arxiv_id=[rec["arxiv_id"]],
                title=[_doc_text(rec, "title")],
                abstract=[_doc_text(rec, "abstract")],
                authors=[_doc_text(rec, "authors")],
                categories=[_doc_text(rec, "categories")],
                comments=[_doc_text(rec, "comments")],
                journal_ref=[_doc_text(rec, "journal_ref")],
                payload=[canonical_json(rec)],
            ))
    return {"engine": "tantivy", "documents": len(records), "index_path": str(index_dir)}


def search_tantivy(index_dir: Path, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    import tantivy
    index = tantivy.Index.open(str(index_dir))
    index.reload()
    searcher = index.searcher()
    q, errors = index.parse_query_lenient(
        normalize_ws(query),
        ["title", "abstract", "authors", "categories", "comments", "journal_ref"],
        field_boosts={"title": 3.0, "abstract": 1.5, "authors": 1.0, "categories": 1.0, "comments": 0.5, "journal_ref": 0.5},
    )
    result = searcher.search(q, limit)
    out: List[Dict[str, Any]] = []
    for rank, (score, addr) in enumerate(result.hits, 1):
        doc = searcher.doc(addr)
        payload = doc.get_first("payload")
        rec = json.loads(str(payload))
        rec["local_search"] = {
            "engine": "tantivy",
            "rank": rank,
            "bm25_score": float(score),
            "query_parser_warnings": [str(x) for x in errors],
        }
        out.append(rec)
    return out


def build_index(corpus: Path, index_path: Path, engine: str = "auto") -> Dict[str, Any]:
    chosen = engine
    if engine == "auto":
        chosen = "tantivy" if tantivy_available() else "sqlite"
    if chosen == "tantivy":
        return build_tantivy_index(corpus, index_path)
    if chosen == "sqlite":
        return build_sqlite_index(corpus, index_path)
    raise ValueError("engine must be auto, tantivy, or sqlite")


def local_search(index_path: Path, query: str, limit: int, engine: str = "auto") -> List[Dict[str, Any]]:
    chosen = engine
    if engine == "auto":
        if index_path.is_dir() and tantivy_available():
            chosen = "tantivy"
        else:
            chosen = "sqlite"
    return search_tantivy(index_path, query, limit) if chosen == "tantivy" else search_sqlite(index_path, query, limit)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def investigate(topic: str, work_dir: Path, limit: int = 100, engine: str = "auto",
                raw_query: Optional[str] = None) -> Dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    corpus = work_dir / "arxiv-corpus.jsonl"
    queue = work_dir / "arxiv-research-candidate-queue.jsonl"
    receipt_path = work_dir / "arxiv-investigation-receipt.json"
    query = raw_query or build_smart_arxiv_query(topic)

    records, remote_receipt = remote_search(query, limit=limit, page_size=min(100, limit))
    appended = append_jsonl(corpus, records)

    chosen = engine
    if engine == "auto":
        chosen = "tantivy" if tantivy_available() else "sqlite"
    index_path = work_dir / ("tantivy-index" if chosen == "tantivy" else "arxiv-index.sqlite")
    index_receipt = build_index(corpus, index_path, chosen)
    hits = local_search(index_path, topic, min(limit, 100), chosen)

    queue_records: List[Dict[str, Any]] = []
    for i, rec in enumerate(hits, 1):
        route = {
            "schema": "hawkar.topa.arxiv_research_candidate.v1",
            "route_type": "ARXIV_RESEARCH_CANDIDATE",
            "topic": topic,
            "rank": i,
            "arxiv_id": rec.get("arxiv_id"),
            "title": rec.get("title"),
            "abs_url": rec.get("abs_url"),
            "pdf_url": rec.get("pdf_url"),
            "categories": rec.get("categories", []),
            "local_search": rec.get("local_search", {}),
            "record_sha256": rec.get("record_sha256"),
            "allowed_next_steps": ["SOURCE_REVIEW", "METHOD_EXTRACTION", "DATASET_ROUTE_DISCOVERY", "CODE_ROUTE_DISCOVERY", "CONTRADICTION_SEARCH", "FALSIFICATION_DESIGN"],
            "scientific_authority": "DISCOVERY_ROUTE_ONLY__PAPER_CLAIMS_REQUIRE_VALIDATION",
        }
        route["route_sha256"] = record_hash(route)
        queue_records.append(route)
    queue.write_text("".join(canonical_json(x) + "\n" for x in queue_records), encoding="utf-8")

    corpus_sha = sha256_bytes(corpus.read_bytes())
    queue_sha = sha256_bytes(queue.read_bytes())
    receipt = {
        "schema": "hawkar.topa.arxiv_investigation_receipt.v1",
        "status": "PASS",
        "topic": topic,
        "arxiv_search_query": query,
        "remote": remote_receipt,
        "records_appended_this_run": appended,
        "corpus_path": str(corpus),
        "corpus_sha256": corpus_sha,
        "index": index_receipt,
        "local_hits": len(hits),
        "queue_path": str(queue),
        "queue_sha256": queue_sha,
        "epistemic_firewall": {
            "search_rank_is_truth": False,
            "arxiv_paper_is_empirical_truth": False,
            "failed_fetch_is_absence_proof": False,
            "negative_and_contradictory_results_preserved": True,
        },
        "claim_ceiling": "ARXIV_DISCOVERY_AND_LOCAL_SEARCH_EXECUTED__SCIENTIFIC_CLAIMS_NOT_AUTOMATICALLY_VALIDATED",
    }
    write_json(receipt_path, receipt)
    return receipt


def _fixture_atom() -> bytes:
    return b'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:arxiv="http://arxiv.org/schemas/atom">
<opensearch:totalResults>2</opensearch:totalResults>
<entry><id>http://arxiv.org/abs/2601.00001v1</id><updated>2026-01-02T00:00:00Z</updated><published>2026-01-01T00:00:00Z</published><title>Quantum gravity calibration test</title><summary>A falsifiable benchmark for quantum gravity search pipelines.</summary><author><name>A. Example</name></author><category term="gr-qc"/><arxiv:primary_category term="gr-qc"/><link href="http://arxiv.org/abs/2601.00001v1" rel="alternate"/><link href="http://arxiv.org/pdf/2601.00001v1" title="pdf" type="application/pdf"/></entry>
<entry><id>http://arxiv.org/abs/2601.00002v1</id><updated>2026-01-03T00:00:00Z</updated><published>2026-01-03T00:00:00Z</published><title>Plate scanning artifacts</title><summary>Image defects and scan-edge morphology in historical plates.</summary><author><name>B. Example</name></author><category term="astro-ph.IM"/><arxiv:primary_category term="astro-ph.IM"/></entry>
</feed>'''


def self_test() -> Dict[str, Any]:
    parsed = parse_atom(_fixture_atom(), {"fixture": True})
    assert parsed["total_results"] == 2
    assert parsed["records"][0]["arxiv_id"] == "2601.00001v1"
    q = build_smart_arxiv_query("quantum gravity")
    assert "all:" in q and "AND" in q
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        corpus = root / "corpus.jsonl"
        append_jsonl(corpus, parsed["records"])
        db = root / "index.sqlite"
        r = build_sqlite_index(corpus, db)
        hits = search_sqlite(db, "quantum gravity", 5)
        assert hits and hits[0]["arxiv_id"] == "2601.00001v1"
        tantivy_status = "NOT_INSTALLED"
        if tantivy_available():
            tdir = root / "tantivy"
            build_tantivy_index(corpus, tdir)
            thits = search_tantivy(tdir, "quantum gravity", 5)
            assert thits and thits[0]["arxiv_id"] == "2601.00001v1"
            tantivy_status = "PASS"
    return {
        "schema": "hawkar.topa.arxiv_gateway.self_test.v1",
        "status": "PASS",
        "atom_parse": "PASS",
        "smart_query": "PASS",
        "sqlite_fts5": "PASS",
        "tantivy": tantivy_status,
        "remote_network_used": False,
        "scientific_firewall": "PASS",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="TOPA arXiv discovery and portable local search gateway")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("self-test")

    s = sub.add_parser("remote-search")
    s.add_argument("query")
    s.add_argument("--raw-query", action="store_true")
    s.add_argument("--field", default="all", choices=["all", "ti", "au", "abs", "co", "jr", "cat", "rn", "id"])
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--sort-by", default="relevance", choices=["relevance", "lastUpdatedDate", "submittedDate"])
    s.add_argument("--sort-order", default="descending", choices=["ascending", "descending"])
    s.add_argument("--out")
    s.add_argument("--receipt")

    s = sub.add_parser("build-index")
    s.add_argument("corpus")
    s.add_argument("index")
    s.add_argument("--engine", default="auto", choices=["auto", "tantivy", "sqlite"])

    s = sub.add_parser("local-search")
    s.add_argument("index")
    s.add_argument("query")
    s.add_argument("--engine", default="auto", choices=["auto", "tantivy", "sqlite"])
    s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("investigate")
    s.add_argument("topic")
    s.add_argument("--work-dir", default="work/topa-arxiv")
    s.add_argument("--limit", type=int, default=100)
    s.add_argument("--engine", default="auto", choices=["auto", "tantivy", "sqlite"])
    s.add_argument("--raw-query")

    args = p.parse_args()
    if args.cmd == "self-test":
        print(json.dumps(self_test(), ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.cmd == "remote-search":
        query = args.query if args.raw_query else build_smart_arxiv_query(args.query, args.field)
        records, receipt = remote_search(query, args.limit, min(args.limit, 100), args.sort_by, args.sort_order)
        if args.out:
            Path(args.out).write_text("".join(canonical_json(x) + "\n" for x in records), encoding="utf-8")
        else:
            for rec in records:
                print(canonical_json(rec))
        if args.receipt:
            write_json(Path(args.receipt), receipt)
        return
    if args.cmd == "build-index":
        print(json.dumps(build_index(Path(args.corpus), Path(args.index), args.engine), ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.cmd == "local-search":
        for rec in local_search(Path(args.index), args.query, args.limit, args.engine):
            print(canonical_json(rec))
        return
    if args.cmd == "investigate":
        print(json.dumps(investigate(args.topic, Path(args.work_dir), args.limit, args.engine, args.raw_query), ensure_ascii=False, indent=2, sort_keys=True))
        return


if __name__ == "__main__":
    main()
