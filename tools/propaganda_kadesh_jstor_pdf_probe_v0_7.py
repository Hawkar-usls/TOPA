#!/usr/bin/env python3
"""Diagnostic-only JSTOR stable-PDF probe for frozen BR03 Kadesh.

Tests the exact JSTOR stable object 528771 corresponding to Wilson 1927.
No extracted source text is persisted; only hashes, page counts, lengths and
marker booleans. A diagnostic success may justify authoritative retrieval v0.3
but cannot unlock semantic coding or SCORE.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import ssl
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

from pypdf import PdfReader

OUT = Path("research/propaganda-defense/execution/KADESH_JSTOR_PDF_PROBE.v0.7.json")
STABLE_ID = "528771"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def make_opener():
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar()),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )


def fetch(opener, url: str, accept="*/*", referer=None, max_bytes=80 * 1024 * 1024):
    headers = {
        "User-Agent": UA,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(req, timeout=45) as r:
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


def markers(text: str, page_no: int):
    low = re.sub(r"\s+", " ", text).lower()
    return {
        "article_title": "texts of the battle of kadesh" in low,
        "john_wilson": "john a. wilson" in low or "john a wilson" in low or "johna. wilson" in low,
        "kadesh": "kadesh" in low,
        "the_poem": "the poem" in low,
        "the_record": "the record" in low,
        "council_urges_peace": "council urges peace" in low,
        "printed_page": bool(re.search(rf"(?:^|\D){page_no}(?:\D|$)", text)),
    }


def inspect_pdf(b: bytes):
    try:
        reader = PdfReader(io.BytesIO(b))
    except Exception as e:
        return {"parse_ok": False, "parse_error": f"{type(e).__name__}: {e}"}

    rows = []
    for idx, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        journal_page = 266 + idx
        norm = re.sub(r"\s+", " ", text).strip()
        rows.append({
            "pdf_index": idx,
            "journal_page_assuming_article_start_266": journal_page,
            "text_chars": len(norm),
            "text_sha256": sha(norm.encode("utf-8")) if norm else None,
            "markers": markers(norm, journal_page),
        })

    p266 = rows[0] if len(rows) > 0 else None
    p277 = rows[11] if len(rows) > 11 else None
    p278 = rows[12] if len(rows) > 12 else None
    poem_rows = rows[:12]
    poem_nontrivial = len(poem_rows) == 12 and all(r["text_chars"] >= 150 for r in poem_rows)
    distinct = len({r["text_sha256"] for r in poem_rows if r["text_sha256"]})
    title_ok = bool(p266 and p266["markers"]["article_title"] and p266["markers"]["john_wilson"])
    end_poem_ok = bool(p277 and (p277["markers"]["council_urges_peace"] or p277["markers"]["kadesh"]))
    boundary_ok = bool(p278 and p278["markers"]["the_record"])
    page_count_ok = len(rows) >= 22
    sufficient = page_count_ok and poem_nontrivial and distinct >= 10 and title_ok and end_poem_ok and boundary_ok
    aggregate = sha(json.dumps(
        [{"page": r["journal_page_assuming_article_start_266"], "text_sha256": r["text_sha256"]} for r in poem_rows],
        sort_keys=True, separators=(",", ":")
    ).encode()) if len(poem_rows) == 12 else None

    return {
        "parse_ok": True,
        "pdf_page_count": len(rows),
        "page_count_at_least_22": page_count_ok,
        "poem_pages_266_277_nontrivial": poem_nontrivial,
        "distinct_poem_page_text_hashes": distinct,
        "page_266_title_author": title_ok,
        "page_277_end_poem": end_poem_ok,
        "page_278_record_boundary": boundary_ok,
        "candidate_content_sufficient": sufficient,
        "poem_pages_266_277_aggregate_sha256": aggregate,
        "pages": rows,
    }


def main():
    op = make_opener()
    landing_url = f"https://www.jstor.org/stable/{STABLE_ID}"
    landing = fetch(op, landing_url, accept="text/html,application/xhtml+xml")

    candidates = [
        f"https://www.jstor.org/stable/pdf/{STABLE_ID}.pdf",
        f"https://www.jstor.org/stable/pdf/{STABLE_ID}.pdf?seq=1",
        f"https://www.jstor.org/stable/pdf/{STABLE_ID}.pdf?acceptTC=true",
        f"https://www.jstor.org/stable/pdf/{STABLE_ID}",
    ]
    attempts = []
    chosen = None
    for url in candidates:
        x = fetch(op, url, accept="application/pdf,text/html;q=0.9,*/*;q=0.8", referer=landing_url)
        rec = pub(x)
        pdf_magic = bool(x.get("ok") and x.get("body", b"").startswith(b"%PDF"))
        rec["pdf_magic"] = pdf_magic
        if pdf_magic:
            inspected = inspect_pdf(x["body"])
            rec["inspection"] = inspected
            if inspected.get("candidate_content_sufficient") and chosen is None:
                chosen = {
                    "requested_url": url,
                    "final_url": x.get("final_url"),
                    "pdf_bytes": x.get("bytes"),
                    "pdf_sha256": x.get("sha256"),
                    "inspection": inspected,
                }
        attempts.append(rec)

    out = {
        "schema": "topa.propaganda_defense.kadesh_jstor_pdf_probe.v0.7",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson, The Texts of the Battle of Kadesh, AJSL 43.4 (1927)",
            "doi": "10.1086/370157",
            "jstor_stable_id": STABLE_ID,
            "locus": "THE POEM, journal pp.266-278; Record excluded",
            "operational_boundary": "Poem content pp.266-277; p.278 is THE RECORD exclusion boundary",
            "changed": False
        },
        "landing": pub(landing),
        "pdf_attempts": attempts,
        "chosen_candidate": chosen,
        "admission": {
            "diagnostic_can_justify_authoritative_retrieval_repair": bool(chosen),
            "br03_retrieval_pass": False,
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False
        },
        "laws": [
            "JSTOR_STABLE_OBJECT_IS_SAME_SOURCE_ROOT_NOT_NEW_WITNESS",
            "DIAGNOSTIC_CANDIDATE != AUTHORITATIVE_RETRIEVAL_PASS",
            "BOUNDARY_PAGE_IS_NOT_CONTENT_PAGE",
            "PDF_MAGIC_AND_TEXT_BOUNDARY_VALIDATION_REQUIRED",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_JSTOR_PDF_PROBE_V0_7=COMPLETE")
    print("LANDING_OK=" + str(bool(landing.get("ok"))).lower())
    print("PDF_CANDIDATE_FOUND=" + str(bool(chosen)).lower())
    if chosen:
        ins = chosen["inspection"]
        print(f"PDF_BYTES={chosen['pdf_bytes']}")
        print(f"PDF_SHA256={chosen['pdf_sha256']}")
        print(f"PDF_PAGE_COUNT={ins['pdf_page_count']}")
        print(f"PAGE266_TITLE_AUTHOR={str(ins['page_266_title_author']).lower()}")
        print(f"PAGE277_END_POEM={str(ins['page_277_end_poem']).lower()}")
        print(f"PAGE278_RECORD_BOUNDARY={str(ins['page_278_record_boundary']).lower()}")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
