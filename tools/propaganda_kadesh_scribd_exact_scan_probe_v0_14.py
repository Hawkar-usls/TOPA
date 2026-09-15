#!/usr/bin/env python3
"""Diagnostic-only exact-scan mirror probe for frozen BR03 Kadesh.

Scribd is treated ONLY as a possible transport mirror of the already frozen
Wilson 1927 AJSL/JSTOR object. It is never source authority and never an
independent witness. No source prose is persisted: only bibliographic fields,
transport URLs, byte/text hashes, lengths, page-number coverage and marker
booleans.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
import ssl
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

OUT = Path("research/propaganda-defense/execution/KADESH_SCRIBD_EXACT_SCAN_PROBE.v0.14.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
DOCS = [
    "https://www.scribd.com/document/462138503/The-Texts-of-the-Battle-of-Kadesh",
    "https://www.scribd.com/document/493951399/Wilson-John-The-Texts-of-the-Battle-of-Kadesh",
]
TITLE = "the texts of the battle of kadesh"
SHELL_MIN = 20_000


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def opener():
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar()),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )


def fetch(op, url: str, *, referer=None, accept="*/*", max_bytes=80 * 1024 * 1024):
    headers = {
        "User-Agent": UA,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        with op.open(req, timeout=45) as r:
            b = r.read(max_bytes + 1)
            truncated = len(b) > max_bytes
            if truncated:
                b = b[:max_bytes]
            return {
                "ok": True,
                "requested_url": url,
                "final_url": r.geturl(),
                "status": getattr(r, "status", 200),
                "content_type": r.headers.get("Content-Type"),
                "content_disposition": r.headers.get("Content-Disposition"),
                "bytes": len(b),
                "sha256": sha(b),
                "truncated": truncated,
                "body": b,
            }
    except Exception as e:
        return {"ok": False, "requested_url": url, "error": f"{type(e).__name__}: {e}"}


def pub(x):
    return {k: v for k, v in x.items() if k != "body"}


def decode(x):
    if not x.get("ok"):
        return ""
    ct = x.get("content_type") or ""
    m = re.search(r"charset=([^;\s]+)", ct, re.I)
    enc = m.group(1).strip('"\'') if m else "utf-8"
    try:
        return x["body"].decode(enc, "replace")
    except LookupError:
        return x["body"].decode("utf-8", "replace")


def flatten(s: str) -> str:
    # Script JSON can contain useful scan OCR metadata, so remove markup tags only,
    # not script bodies. Collapse to a normalized in-memory representation.
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def identity_markers(text: str):
    low = text.lower()
    pages = sorted({int(x) for x in re.findall(r"(?<!\d)(26[6-9]|27\d|28[0-7])(?!\d)", text)})
    return {
        "title": TITLE in low,
        "john_a_wilson": "john a. wilson" in low or "john a wilson" in low,
        "ajsl_or_full_journal": (
            "american journal of semitic languages and literatures" in low
            or "the american journal of semitic languages and literatures" in low
            or "ajsl" in low
        ),
        "volume_43": bool(re.search(r"(?:vol(?:ume)?\.?\s*43|43\s*\(?4\)?)", low)),
        "issue_4": bool(re.search(r"(?:no\.?\s*4|issue\s*4|43\s*\(?4\)?)", low)),
        "year_1927": "1927" in low,
        "page_range_266_287": bool(re.search(r"266\s*[-–—]\s*287", text)),
        "university_chicago": "university of chicago" in low,
        "jstor": "jstor" in low,
        "stable_528771": "528771" in low,
        "page_numbers_seen_266_287": pages,
        "page_number_coverage": len(pages),
        "p266": 266 in pages,
        "p277": 277 in pages,
        "p278": 278 in pages,
        "p287": 287 in pages,
        "the_poem": "the poem" in low,
        "council_urges_peace": "council urges peace" in low,
        "the_record": "the record" in low,
        "comment_on_the_texts": "comment on the texts" in low,
    }


def jsonld_blocks(page: str):
    out = []
    for m in re.finditer(r'''<script[^>]+type=["']application/ld\+json["'][^>]*>(.*?)</script>''', page, re.I | re.S):
        raw = html.unescape(m.group(1)).strip()
        try:
            obj = json.loads(raw)
            out.append({"type": type(obj).__name__, "sha256": sha(raw.encode()), "keys": sorted(obj.keys()) if isinstance(obj, dict) else None})
        except Exception:
            out.append({"type": "parse_fail", "sha256": sha(raw.encode())})
    return out


def discovered_urls(page: str, base: str):
    vals = []
    # URLs in HTML attrs and embedded JSON. Bound to Scribd/CDN-ish references
    # plausibly related to document/download/page assets.
    candidates = []
    for pat in [
        r'''(?:href|src)=["']([^"']+)["']''',
        r'''["'](?:download_url|downloadUrl|asset_url|assetUrl|page_url|pageUrl|document_url|documentUrl)["']\s*:\s*["']([^"']+)["']''',
        r'''https?://[^"'<>\\\s]+''',
    ]:
        for m in re.finditer(pat, page, re.I):
            v = m.group(1) if m.groups() else m.group(0)
            candidates.append(html.unescape(v).replace("\\/", "/"))
    for v in candidates:
        u = urllib.parse.urljoin(base, v)
        try:
            p = urllib.parse.urlparse(u)
        except Exception:
            continue
        low = u.lower()
        if p.scheme not in {"http", "https"}:
            continue
        if not any(h in p.netloc.lower() for h in ("scribd", "everand", "doccdn", "s-cdn", "html.scribdassets", "scribdassets")):
            continue
        if not any(k in low for k in ("download", ".pdf", "document", "page", "asset", "text_layer", "content")):
            continue
        if u not in vals:
            vals.append(u)
        if len(vals) >= 120:
            break
    return vals


def inspect_pdf(b: bytes):
    if PdfReader is None:
        return {"parse_ok": False, "error": "pypdf unavailable"}
    try:
        reader = PdfReader(io.BytesIO(b))
    except Exception as e:
        return {"parse_ok": False, "error": f"{type(e).__name__}: {e}"}
    page_rows = []
    aggregate_parts = []
    for idx, p in enumerate(reader.pages):
        try:
            t = p.extract_text() or ""
        except Exception:
            t = ""
        norm = re.sub(r"\s+", " ", t).strip()
        aggregate_parts.append(norm)
        page_rows.append({
            "pdf_index": idx,
            "text_chars": len(norm),
            "text_sha256": sha(norm.encode()) if norm else None,
            "markers": identity_markers(norm),
        })
    all_text = " ".join(aggregate_parts)
    ids = identity_markers(all_text)
    # Locate strongest candidate positions rather than assuming PDF index == journal page.
    p266_idxs = [r["pdf_index"] for r in page_rows if r["markers"]["p266"] and (r["markers"]["title"] or r["markers"]["the_poem"])]
    p277_idxs = [r["pdf_index"] for r in page_rows if r["markers"]["p277"] and (r["markers"]["council_urges_peace"] or r["markers"]["the_poem"])]
    p278_idxs = [r["pdf_index"] for r in page_rows if r["markers"]["p278"] and r["markers"]["the_record"]]
    p287_idxs = [r["pdf_index"] for r in page_rows if r["markers"]["p287"] and (r["markers"]["comment_on_the_texts"] or r["markers"]["kadesh"] if "kadesh" in r["markers"] else True)]
    page_count_ok = len(page_rows) >= 22
    identity_ok = ids["title"] and ids["john_a_wilson"] and ids["year_1927"] and (ids["ajsl_or_full_journal"] or ids["jstor"])
    boundary_ok = bool(p266_idxs and p278_idxs and min(p278_idxs) > min(p266_idxs))
    end_ok = bool(ids["p287"] and (ids["comment_on_the_texts"] or ids["jstor"]))
    sufficient = page_count_ok and identity_ok and boundary_ok and ids["the_poem"] and ids["the_record"] and end_ok
    return {
        "parse_ok": True,
        "pdf_page_count": len(page_rows),
        "identity": ids,
        "p266_candidate_indices": p266_idxs,
        "p277_candidate_indices": p277_idxs,
        "p278_record_candidate_indices": p278_idxs,
        "p287_candidate_indices": p287_idxs,
        "page_count_at_least_22": page_count_ok,
        "boundary_order_ok": boundary_ok,
        "candidate_exact_scan_sufficient": sufficient,
        "normalized_document_text_sha256": sha(re.sub(r"\s+", " ", all_text).encode()),
        "page_hashes": [{"pdf_index": r["pdf_index"], "text_chars": r["text_chars"], "text_sha256": r["text_sha256"]} for r in page_rows],
    }


def inspect_document(url: str):
    op = opener()
    x = fetch(op, url, accept="text/html,application/xhtml+xml")
    rec = {"url": url, "landing": pub(x), "jsonld": [], "identity": None, "discovered_transport_urls": [], "transport_attempts": []}
    if not x.get("ok"):
        return rec
    page = decode(x)
    flat = flatten(page)
    rec["landing_normalized_chars"] = len(flat)
    rec["landing_normalized_sha256"] = sha(flat.encode()) if flat else None
    rec["identity"] = identity_markers(flat)
    rec["jsonld"] = jsonld_blocks(page)
    urls = discovered_urls(page, x.get("final_url") or url)
    rec["discovered_transport_urls"] = urls
    for u in urls[:40]:
        y = fetch(op, u, referer=x.get("final_url") or url, accept="application/pdf,text/plain,application/json,text/html,image/*,*/*;q=0.5")
        tr = pub(y)
        b = y.get("body", b"")
        tr["pdf_magic"] = bool(b.startswith(b"%PDF"))
        if tr["pdf_magic"]:
            tr["pdf_inspection"] = inspect_pdf(b)
        elif y.get("ok") and len(b) >= SHELL_MIN:
            ct = (y.get("content_type") or "").lower()
            if any(k in ct for k in ("text", "json", "javascript", "html")):
                t = flatten(decode(y))
                tr["normalized_chars"] = len(t)
                tr["normalized_sha256"] = sha(t.encode()) if t else None
                tr["identity"] = identity_markers(t)
        rec["transport_attempts"].append(tr)
    return rec


def main():
    docs = [inspect_document(u) for u in DOCS]
    strong_landings = []
    strong_pdfs = []
    strong_text_reps = []
    for d in docs:
        i = d.get("identity") or {}
        if i.get("title") and i.get("john_a_wilson") and i.get("year_1927") and i.get("p266") and i.get("p278") and i.get("the_record"):
            strong_landings.append(d["url"])
        for t in d.get("transport_attempts", []):
            if t.get("pdf_magic") and t.get("pdf_inspection", {}).get("candidate_exact_scan_sufficient"):
                strong_pdfs.append({"document_url": d["url"], "transport_url": t.get("final_url"), "bytes": t.get("bytes"), "sha256": t.get("sha256"), "inspection": t.get("pdf_inspection")})
            ii = t.get("identity") or {}
            if ii.get("title") and ii.get("john_a_wilson") and ii.get("p266") and ii.get("p278") and ii.get("the_record") and t.get("normalized_chars", 0) >= 20_000:
                strong_text_reps.append({"document_url": d["url"], "transport_url": t.get("final_url"), "bytes": t.get("bytes"), "sha256": t.get("sha256"), "normalized_sha256": t.get("normalized_sha256"), "identity": ii})

    can_validate = bool(strong_pdfs or strong_text_reps or strong_landings)
    out = {
        "schema": "topa.propaganda_defense.kadesh_scribd_exact_scan_probe.v0.14",
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
        "mirror_firewall": {
            "scribd_is_source_authority": False,
            "scribd_is_independent_witness": False,
            "source_root_count_if_admitted": 1,
            "admission_class": "EXACT_SCAN_TRANSPORT_MIRROR_ONLY",
        },
        "documents": docs,
        "diagnostic_summary": {
            "strong_landing_count": len(strong_landings),
            "strong_pdf_count": len(strong_pdfs),
            "strong_text_representation_count": len(strong_text_reps),
            "strong_landings": strong_landings,
            "strong_pdfs": strong_pdfs,
            "strong_text_representations": strong_text_reps,
            "can_enter_separate_mirror_admission_review": can_validate,
            "br03_retrieval_pass": False,
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False,
        },
        "laws": [
            "TRANSPORT_MIRROR != SOURCE_AUTHORITY",
            "MIRROR_COPY != INDEPENDENT_WITNESS",
            "SEARCH_INDEX_SNIPPET != RETRIEVED_MIRROR",
            "EXACT_BIBLIOGRAPHIC_IDENTITY_AND_BOUNDARY_REQUIRED",
            "MIRROR_DIAGNOSTIC_PASS != BR03_RETRIEVAL_PASS",
            "NO_CODING_UNLOCK_FROM_MIRROR_DISCOVERY",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_SCRIBD_EXACT_SCAN_PROBE_V0_14=COMPLETE")
    print(f"STRONG_LANDINGS={len(strong_landings)}")
    print(f"STRONG_PDFS={len(strong_pdfs)}")
    print(f"STRONG_TEXT_REPS={len(strong_text_reps)}")
    print(f"MIRROR_ADMISSION_REVIEW_ELIGIBLE={str(can_validate).lower()}")
    print("BR03_RETRIEVAL_PASS=false")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
