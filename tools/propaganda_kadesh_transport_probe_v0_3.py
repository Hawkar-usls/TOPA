#!/usr/bin/env python3
"""Diagnostic-only BR03 Kadesh transport probe v0.3.

Frozen authority/locus are immutable:
  John A. Wilson, "The Texts of the Battle of Kadesh", AJSL 43.4 (1927)
  DOI 10.1086/370157
  THE POEM, journal pp. 266-278; Record excluded.

This script may repair transport discovery only. It writes hashes/metadata/marker
booleans, never source bodies, never semantic coding, and never unlocks SCORE.
"""
from __future__ import annotations

import hashlib
import html
import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_TRANSPORT_PROBE.v0.3.json")
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
RESEARCH_UA = "TOPA-Kadesh-Transport-Probe/0.3 (+https://github.com/Hawkar-usls/TOPA)"
HTIDS = ["mdp.39015024059043", "uc1.b3604224", "coo.31924066155205"]


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def opener_with_cookies():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def fetch(url: str, *, opener=None, browser=False, accept="*/*", referer=None, max_bytes=20 * 1024 * 1024, timeout=35):
    headers = {
        "User-Agent": BROWSER_UA if browser else RESEARCH_UA,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    op = opener or urllib.request.build_opener()
    t0 = time.time()
    try:
        with op.open(req, timeout=timeout) as r:
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
                "bytes": len(b),
                "sha256": digest(b),
                "truncated": truncated,
                "elapsed_ms": int((time.time() - t0) * 1000),
                "body": b,
            }
    except Exception as e:
        return {
            "ok": False,
            "requested_url": url,
            "error": f"{type(e).__name__}: {e}",
            "elapsed_ms": int((time.time() - t0) * 1000),
        }


def public(x):
    return {k: v for k, v in x.items() if k != "body"}


def decode_declared(x) -> str:
    if not x.get("ok"):
        return ""
    ct = x.get("content_type") or ""
    m = re.search(r"charset=([^;\s]+)", ct, flags=re.I)
    enc = m.group(1).strip('"\'') if m else "utf-8"
    try:
        return x["body"].decode(enc, "replace")
    except LookupError:
        return x["body"].decode("utf-8", "replace")


def plain(s: str) -> str:
    s = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def parse_hathi_hit_seqs(s: str):
    # Search-result pages use seq in links. Keep all unique positive seq values;
    # later validation against page representations prevents nav links from counting.
    vals = []
    for m in re.finditer(r"(?:[?;&]|&amp;)seq=(\d+)", s):
        n = int(m.group(1))
        if n > 1 and n not in vals:
            vals.append(n)
    return vals


def hathi_search(op, htid: str, query: str):
    q = urllib.parse.quote(query, safe="")
    url = f"https://babel.hathitrust.org/cgi/pt/search?q1={q};id={htid};view=1up;seq=1;start=1;sz=50;page=search;orient=0"
    x = fetch(url, opener=op, browser=True, accept="text/html,application/xhtml+xml")
    text = decode_declared(x)
    return {
        "request": public(x),
        "hit_seqs": parse_hathi_hit_seqs(text) if x.get("ok") else [],
        "contains_query_words": all(w.lower() in plain(text).lower() for w in re.findall(r"[A-Za-z]+", query)[:3]) if text else False,
    }


def hathi_html(op, htid: str, seq: int):
    url = f"https://babel.hathitrust.org/cgi/imgsrv/html?id={htid};seq={seq}"
    x = fetch(url, opener=op, browser=True, accept="text/html,application/xhtml+xml", max_bytes=3 * 1024 * 1024)
    txt = plain(decode_declared(x)) if x.get("ok") else ""
    low = txt.lower()
    return {
        "request": public(x),
        "markers": {
            "title": "texts of the battle of kadesh" in low,
            "john_wilson": "john a. wilson" in low or "john wilson" in low,
            "poem": "the poem" in low,
            "record": "the record" in low,
        },
        "text_chars": len(txt),
        "text_sha256": digest(txt.encode("utf-8")) if txt else None,
    }


def probe_hathi():
    out = []
    for htid in HTIDS:
        op = opener_with_cookies()
        searches = {
            "title": hathi_search(op, htid, '"The Texts of the Battle of Kadesh"'),
            "author": hathi_search(op, htid, '"John A. Wilson"'),
            "poem": hathi_search(op, htid, '"THE POEM"'),
            "record": hathi_search(op, htid, '"THE RECORD"'),
        }
        candidate_seqs = []
        for v in searches.values():
            for n in v["hit_seqs"]:
                if n not in candidate_seqs:
                    candidate_seqs.append(n)
        # Validate only a bounded neighborhood around search hits; no blind whole-volume crawl.
        validated = {}
        neighborhood = []
        for n in candidate_seqs:
            for k in range(max(2, n - 1), n + 2):
                if k not in neighborhood:
                    neighborhood.append(k)
        neighborhood = sorted(neighborhood)[:36]
        for seq in neighborhood:
            validated[str(seq)] = hathi_html(op, htid, seq)

        title_pages = [int(k) for k, v in validated.items() if v["markers"]["title"] or v["markers"]["john_wilson"]]
        poem_pages = [int(k) for k, v in validated.items() if v["markers"]["poem"]]
        record_pages = [int(k) for k, v in validated.items() if v["markers"]["record"]]
        start = min(title_pages) if title_pages else None
        boundary = min([n for n in record_pages if start is not None and n > start], default=None)

        locus = None
        if start is not None and boundary is not None and boundary - start == 13:
            pages = []
            all_ok = True
            for seq in range(start, boundary + 1):
                key = str(seq)
                if key not in validated:
                    validated[key] = hathi_html(op, htid, seq)
                rec = validated[key]
                if not rec["request"].get("ok") or rec["text_chars"] < 100:
                    all_ok = False
                pages.append({"seq": seq, "text_sha256": rec["text_sha256"], "bytes": rec["request"].get("bytes"), "markers": rec["markers"]})
            locus = {
                "candidate_start_seq": start,
                "record_boundary_seq": boundary,
                "expected_locus_page_count": 13,
                "locus_seq_count": 13,
                "all_locus_pages_retrieved": all_ok,
                "poem_marker_inside_locus": any(start <= n < boundary for n in poem_pages),
                "record_marker_on_boundary": boundary in record_pages,
                "pages_including_boundary": pages,
            }
        out.append({
            "htid": htid,
            "searches": searches,
            "validated_pages": validated,
            "title_pages": title_pages,
            "poem_pages": poem_pages,
            "record_pages": record_pages,
            "locus_candidate": locus,
        })
    return out


def parse_google_json(x):
    if not x.get("ok"):
        return None, None
    s = decode_declared(x).strip()
    # Handle plain JSON or callback wrappers.
    if s.startswith("topa_cb(") and s.endswith(");"):
        s = s[len("topa_cb("):-2]
    try:
        return json.loads(s), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def probe_google():
    volume_id = "2l5uKJXiO70C"
    queries = ["The Texts of the Battle of Kadesh", "John A. Wilson", "THE POEM", "THE RECORD"]
    qout = {}
    for q in queries:
        url = "https://www.google.com/books?" + urllib.parse.urlencode({"id": volume_id, "jscmd": "SearchWithinVolume2", "q": q})
        x = fetch(url, browser=True, accept="application/json,text/plain,*/*")
        j, err = parse_google_json(x)
        entry = {"request": public(x), "parse_error": err}
        if isinstance(j, dict):
            arr = j.get("entry") or j.get("results") or []
            entry["searchable"] = j.get("searchable")
            entry["number_of_results"] = j.get("number_of_results", len(arr))
            entry["results"] = []
            for r in arr[:60]:
                snippet = r.get("snippet_text") or ""
                entry["results"].append({
                    "page_id": r.get("page_id"),
                    "page_number": r.get("page_number"),
                    "page_url": r.get("page_url"),
                    "snippet_sha256": digest(snippet.encode("utf-8")) if snippet else None,
                })
        qout[q] = entry

    view_url = "https://books.google.com/books?" + urllib.parse.urlencode({"jscmd": "viewapi", "bibkeys": volume_id, "callback": "topa_cb"})
    vx = fetch(view_url, browser=True, accept="application/javascript,text/javascript,*/*")
    vj, verr = parse_google_json(vx)
    return {
        "volume_id": volume_id,
        "search_within_volume": qout,
        "view_api": {"request": public(vx), "parse_error": verr, "parsed": vj},
    }


def probe_uchicago():
    doi = "10.1086/370157"
    article = f"https://www.journals.uchicago.edu/doi/{doi}"
    urls = [
        f"https://www.journals.uchicago.edu/doi/pdf/{doi}",
        f"https://www.journals.uchicago.edu/doi/epdf/{doi}",
        f"https://www.journals.uchicago.edu/doi/pdfplus/{doi}",
        f"https://www.journals.uchicago.edu/doi/pdf/{doi}?download=true",
    ]
    out = []
    op = opener_with_cookies()
    landing = fetch(article, opener=op, browser=True, accept="text/html,application/xhtml+xml")
    for u in urls:
        x = fetch(u, opener=op, browser=True, accept="application/pdf,text/html;q=0.9,*/*;q=0.8", referer=article, max_bytes=60 * 1024 * 1024)
        out.append({
            "request": public(x),
            "pdf_magic": bool(x.get("ok") and x.get("body", b"").startswith(b"%PDF")),
        })
    return {"landing": public(landing), "pdf_candidates": out}


def main():
    hathi = probe_hathi()
    google = probe_google()
    uchicago = probe_uchicago()

    hathi_sufficient = []
    for x in hathi:
        c = x.get("locus_candidate") or {}
        if c.get("all_locus_pages_retrieved") and c.get("poem_marker_inside_locus") and c.get("record_marker_on_boundary"):
            hathi_sufficient.append(x["htid"])
    uchicago_pdf = [x["request"].get("final_url") for x in uchicago["pdf_candidates"] if x.get("pdf_magic")]

    out = {
        "schema": "topa.propaganda_defense.kadesh_transport_probe.v0.3",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson, The Texts of the Battle of Kadesh, AJSL 43.4 (1927)",
            "doi": "10.1086/370157",
            "locus": "THE POEM, journal pp. 266-278; Record excluded",
            "changed": False,
        },
        "hathitrust": hathi,
        "google_books": google,
        "uchicago": uchicago,
        "diagnostic_summary": {
            "hathi_locus_sufficient_candidates": hathi_sufficient,
            "uchicago_pdf_transports": uchicago_pdf,
            "can_consider_retrieval_v0_3_repair": bool(hathi_sufficient or uchicago_pdf),
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False,
        },
        "laws": [
            "DIAGNOSTIC_PASS != RETRIEVAL_PASS",
            "TRANSPORT_REPAIR != LOCUS_CHANGE",
            "SEARCH_SNIPPET != SOURCE_CONTENT",
            "NO_TLS_VERIFICATION_BYPASS",
            "NO_CODING_UNLOCK_FROM_PROBE",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_TRANSPORT_PROBE_V0_3=COMPLETE")
    print("HATHI_LOCUS_SUFFICIENT=" + (",".join(hathi_sufficient) if hathi_sufficient else "NONE"))
    print("UCHICAGO_PDF_TRANSPORTS=" + str(len(uchicago_pdf)))
    print("RETRIEVAL_REPAIR_CANDIDATE=" + str(bool(hathi_sufficient or uchicago_pdf)).lower())
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
