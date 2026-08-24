#!/usr/bin/env python3
"""Diagnostic-only Common Crawl WARC transport probe for frozen BR03 Kadesh.

Queries recent versioned Common Crawl indexes for the two exact Scribd URLs that
public search indexing identifies as copies of the frozen Wilson 1927 article.
If a WARC record exists, this probe fetches the exact byte range, decompresses the
WARC member, validates bibliographic identity and frozen p266/p278 geometry in
memory, and persists only provenance, hashes, lengths and marker booleans.

Common Crawl and Scribd have zero evidence authority and add zero independent
source roots. Authority remains Wilson/AJSL/UChicago/JSTOR stable 528771.
"""
from __future__ import annotations

import gzip
import hashlib
import html
import json
import re
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_COMMONCRAWL_WARC_PROBE.v0.16.json")
COLLINFO = "https://index.commoncrawl.org/collinfo.json"
DATA_ROOT = "https://data.commoncrawl.org/"
UA = "TOPA-Kadesh-CommonCrawl-Probe/0.16 (+https://github.com/Hawkar-usls/TOPA)"
TARGETS = [
    "https://www.scribd.com/document/462138503/The-Texts-of-the-Battle-of-Kadesh",
    "https://www.scribd.com/document/493951399/Wilson-John-The-Texts-of-the-Battle-of-Kadesh",
]
MAX_INDEXES = 8
MAX_RECORDS_PER_TARGET = 12


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def request(url: str, *, headers=None, max_bytes=20 * 1024 * 1024, timeout=45):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            b = r.read(max_bytes + 1)
            trunc = len(b) > max_bytes
            if trunc:
                b = b[:max_bytes]
            return {
                "ok": True,
                "status": getattr(r, "status", 200),
                "final_url": r.geturl(),
                "content_type": r.headers.get("Content-Type"),
                "content_range": r.headers.get("Content-Range"),
                "bytes": len(b),
                "sha256": sha256(b),
                "truncated": trunc,
                "body": b,
            }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def pub(x):
    return {k: v for k, v in x.items() if k != "body"}


def latest_indexes():
    x = request(COLLINFO, max_bytes=4 * 1024 * 1024)
    if not x.get("ok"):
        return pub(x), []
    try:
        arr = json.loads(x["body"].decode("utf-8", "replace"))
    except Exception:
        return pub(x), []
    rows = []
    for item in arr[:MAX_INDEXES]:
        if item.get("id") and item.get("cdx-api"):
            rows.append({"id": item["id"], "cdx_api": item["cdx-api"], "name": item.get("name")})
    return pub(x), rows


def query_index(index: dict, target: str):
    q = urllib.parse.urlencode({
        "url": target,
        "output": "json",
        "matchType": "exact",
        "filter": "status:200",
    })
    x = request(index["cdx_api"] + "?" + q, max_bytes=8 * 1024 * 1024)
    records = []
    if x.get("ok"):
        for line in x["body"].decode("utf-8", "replace").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if all(k in rec for k in ("filename", "offset", "length")):
                records.append(rec)
    return pub(x), records[:MAX_RECORDS_PER_TARGET]


def warc_segment(rec: dict):
    try:
        off = int(rec["offset"]); length = int(rec["length"])
    except Exception:
        return {"ok": False, "error": "invalid offset/length"}
    url = DATA_ROOT + rec["filename"]
    x = request(url, headers={"Range": f"bytes={off}-{off+length-1}"}, max_bytes=length + 1024, timeout=60)
    result = {"transport": pub(x), "warc_url": url, "offset": off, "length": length}
    if not x.get("ok"):
        return result
    raw = x["body"]
    result["range_sha256"] = sha256(raw)
    try:
        member = gzip.decompress(raw)
        result["gzip_ok"] = True
        result["decompressed_bytes"] = len(member)
        result["decompressed_sha256"] = sha256(member)
    except Exception as e:
        result["gzip_ok"] = False
        result["gzip_error"] = f"{type(e).__name__}: {e}"
        return result

    # WARC header -> embedded HTTP response -> HTTP entity.
    split1 = re.split(br"\r?\n\r?\n", member, maxsplit=1)
    if len(split1) != 2:
        result["payload_parse_ok"] = False
        return result
    embedded = split1[1]
    split2 = re.split(br"\r?\n\r?\n", embedded, maxsplit=1)
    if len(split2) != 2:
        result["payload_parse_ok"] = False
        return result
    http_head, payload = split2
    result["payload_parse_ok"] = True
    result["http_header_sha256"] = sha256(http_head)
    result["payload_bytes"] = len(payload)
    result["payload_sha256"] = sha256(payload)
    result["payload"] = payload
    return result


def normalize_payload(b: bytes) -> str:
    s = b.decode("utf-8", "replace")
    # Decode JSON-style unicode escapes without touching ordinary UTF-8.
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    s = s.replace("\\/", "/").replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def marker_positions(text: str, regex: str):
    return [m.start() for m in re.finditer(regex, text, re.I)]


def near(text: str, pos: int, regex: str, radius: int):
    a = max(0, pos - radius); z = min(len(text), pos + radius)
    return bool(re.search(regex, text[a:z], re.I))


def analyze_text(text: str):
    low = text.lower()
    title = "the texts of the battle of kadesh" in low
    author = "john a. wilson" in low or "john a wilson" in low or "johna. wilson" in low
    journal = "american journal of semitic languages and literatures" in low
    year = "1927" in low
    page_range = bool(re.search(r"266\s*[-–—]\s*287", text))
    uchicago = "university of chicago press" in low or "university of chicago" in low
    jstor = "jstor" in low
    stable = "528771" in low
    poem = "the poem" in low
    council = "the council urges peace" in low
    record = "the record" in low
    comment = "comment on the texts" in low
    end_poem = "end of poem" in low

    p266 = marker_positions(text, r"(?<!\d)266(?!\d)")
    p277 = marker_positions(text, r"(?<!\d)277(?!\d)")
    p278 = marker_positions(text, r"(?<!\d)278(?!\d)")
    p287 = marker_positions(text, r"(?<!\d)287(?!\d)")

    p266_ok = any(near(text, p, r"the poem|texts of the battle of kadesh", 2600) for p in p266)
    p277_ok = any(near(text, p, r"the council urges peace|end of poem", 2600) for p in p277)
    p278_ok = any(near(text, p, r"the record", 1800) for p in p278)
    p287_ok = any(near(text, p, r"comment on the texts|prisoners presented to amon", 2600) for p in p287)
    page_nums = sorted({int(x) for x in re.findall(r"(?<!\d)(26[6-9]|27\d|28[0-7])(?!\d)", text)})

    identity_ok = title and author and journal and year and (uchicago or jstor)
    geometry_ok = p266_ok and p277_ok and p278_ok and p287_ok
    content_ok = len(text) >= 35_000 and poem and council and record and comment and len(page_nums) >= 18
    sufficient = identity_ok and geometry_ok and content_ok

    def window_hashes(ps):
        out = []
        for p in ps[:8]:
            a=max(0,p-1200);z=min(len(text),p+1200)
            out.append(sha256(text[a:z].encode("utf-8")))
        return out

    return {
        "normalized_chars": len(text),
        "normalized_sha256": sha256(text.encode("utf-8")) if text else None,
        "identity": {
            "title": title,
            "john_a_wilson": author,
            "journal": journal,
            "year_1927": year,
            "page_range_266_287": page_range,
            "university_chicago": uchicago,
            "jstor": jstor,
            "stable_528771": stable,
        },
        "content_markers": {
            "the_poem": poem,
            "council_urges_peace": council,
            "end_of_poem": end_poem,
            "the_record": record,
            "comment_on_the_texts": comment,
        },
        "page_geometry": {
            "page_numbers_seen_266_287": page_nums,
            "coverage_count": len(page_nums),
            "p266_start_ok": p266_ok,
            "p277_end_poem_ok": p277_ok,
            "p278_record_boundary_ok": p278_ok,
            "p287_end_ok": p287_ok,
            "anchor_window_sha256": {
                "p266": window_hashes(p266),
                "p277": window_hashes(p277),
                "p278": window_hashes(p278),
                "p287": window_hashes(p287),
            },
        },
        "identity_ok": identity_ok,
        "geometry_ok": geometry_ok,
        "content_ok": content_ok,
        "candidate_content_sufficient": sufficient,
    }


def main():
    collinfo_receipt, indexes = latest_indexes()
    targets_out = []
    strong = []

    for target in TARGETS:
        target_rec = {"target_url": target, "index_queries": [], "warc_candidates": []}
        seen_records = set()
        for idx in indexes:
            qreceipt, records = query_index(idx, target)
            target_rec["index_queries"].append({"index": idx, "request": qreceipt, "record_count": len(records)})
            for rec in records:
                key = (rec.get("filename"), rec.get("offset"), rec.get("length"))
                if key in seen_records:
                    continue
                seen_records.add(key)
                w = warc_segment(rec)
                payload = w.pop("payload", None)
                candidate = {
                    "index_id": idx["id"],
                    "cdx_record": {k: rec.get(k) for k in ("url", "timestamp", "mime", "status", "digest", "length", "offset", "filename", "languages")},
                    "warc": w,
                }
                if payload is not None:
                    text = normalize_payload(payload)
                    candidate["analysis"] = analyze_text(text)
                    if candidate["analysis"]["candidate_content_sufficient"]:
                        strong.append({"target_url": target, "index_id": idx["id"], "candidate": candidate})
                target_rec["warc_candidates"].append(candidate)
                if len(target_rec["warc_candidates"]) >= MAX_RECORDS_PER_TARGET:
                    break
            if len(target_rec["warc_candidates"]) >= MAX_RECORDS_PER_TARGET:
                break
        targets_out.append(target_rec)

    # Prefer latest index by input order; all are zero-authority archival transports.
    chosen = strong[0] if strong else None
    out = {
        "schema": "topa.propaganda_defense.kadesh_commoncrawl_warc_probe.v0.16",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson / AJSL / University of Chicago / JSTOR",
            "doi": "10.1086/370157",
            "jstor_stable_id": "528771",
            "locus": "THE POEM, journal pp.266-278; Record excluded",
            "operational_boundary": "Poem pp.266-277; p.278 is THE RECORD exclusion boundary",
            "changed": False,
        },
        "archive_firewall": {
            "common_crawl_evidence_authority": 0,
            "scribd_evidence_authority": 0,
            "warc_snapshot_adds_independent_source_root": False,
            "scribd_mirror_adds_independent_source_root": False,
            "source_root_count_if_admitted": 1,
            "authority_remains": "Wilson / AJSL / UChicago / JSTOR",
        },
        "collinfo_request": collinfo_receipt,
        "indexes_checked": indexes,
        "targets": targets_out,
        "diagnostic_summary": {
            "strong_warc_candidate_count": len(strong),
            "strong_candidates": [
                {
                    "target_url": s["target_url"],
                    "index_id": s["index_id"],
                    "timestamp": s["candidate"]["cdx_record"].get("timestamp"),
                    "commoncrawl_digest": s["candidate"]["cdx_record"].get("digest"),
                    "warc_filename": s["candidate"]["cdx_record"].get("filename"),
                    "offset": s["candidate"]["cdx_record"].get("offset"),
                    "length": s["candidate"]["cdx_record"].get("length"),
                    "payload_sha256": s["candidate"]["warc"].get("payload_sha256"),
                    "normalized_sha256": s["candidate"]["analysis"].get("normalized_sha256"),
                }
                for s in strong
            ],
            "preferred_candidate": {
                "target_url": chosen["target_url"],
                "index_id": chosen["index_id"],
                "timestamp": chosen["candidate"]["cdx_record"].get("timestamp"),
                "commoncrawl_digest": chosen["candidate"]["cdx_record"].get("digest"),
                "warc_filename": chosen["candidate"]["cdx_record"].get("filename"),
                "offset": chosen["candidate"]["cdx_record"].get("offset"),
                "length": chosen["candidate"]["cdx_record"].get("length"),
                "payload_sha256": chosen["candidate"]["warc"].get("payload_sha256"),
                "normalized_sha256": chosen["candidate"]["analysis"].get("normalized_sha256"),
            } if chosen else None,
            "can_enter_separate_archived_transport_admission_review": bool(chosen),
            "br03_retrieval_pass": False,
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False,
        },
        "laws": [
            "WARC_SNAPSHOT != SOURCE_AUTHORITY",
            "ARCHIVE_COPY != INDEPENDENT_WITNESS",
            "VERSIONED_WARC_FILENAME_OFFSET_LENGTH_DIGEST_REQUIRED",
            "RAW_PAYLOAD_SHA256_AND_FULL_LOCUS_GEOMETRY_REQUIRED",
            "DIAGNOSTIC_WARC_PASS != BR03_RETRIEVAL_PASS",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_COMMONCRAWL_WARC_PROBE_V0_16=COMPLETE")
    print(f"INDEXES_CHECKED={len(indexes)}")
    print(f"STRONG_WARC_CANDIDATES={len(strong)}")
    if chosen:
        c=chosen["candidate"]
        print("PREFERRED_INDEX="+chosen["index_id"])
        print("PREFERRED_TIMESTAMP="+str(c["cdx_record"].get("timestamp")))
        print("PREFERRED_PAYLOAD_SHA256="+str(c["warc"].get("payload_sha256")))
    else:
        print("PREFERRED_INDEX=NONE")
    print("ARCHIVED_TRANSPORT_ADMISSION_REVIEW_ELIGIBLE="+str(bool(chosen)).lower())
    print("BR03_RETRIEVAL_PASS=false")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
