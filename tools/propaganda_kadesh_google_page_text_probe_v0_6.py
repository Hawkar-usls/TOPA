#!/usr/bin/env python3
"""Diagnostic-only Google Books page-text transport probe for frozen BR03.

Frozen object: Wilson 1927, DOI 10.1086/370157, THE POEM pp.266-278 with
THE RECORD excluded. Operationally pp.266-277 are content; p.278 is the
exclusion boundary. No source text is written to disk: only hashes, byte/text
lengths, transport metadata, and marker booleans are persisted.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_GOOGLE_PAGE_TEXT_PROBE.v0.6.json")
VOL = "2l5uKJXiO70C"
PAGES = list(range(266, 279))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str, max_bytes=8 * 1024 * 1024):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/plain,text/html,application/javascript,application/json,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            b = r.read(max_bytes + 1)
            truncated = len(b) > max_bytes
            if truncated:
                b = b[:max_bytes]
            ct = r.headers.get("Content-Type") or ""
            m = re.search(r"charset=([^;\s]+)", ct, re.I)
            enc = m.group(1).strip('"\'') if m else "utf-8"
            try:
                s = b.decode(enc, "replace")
            except LookupError:
                s = b.decode("utf-8", "replace")
            return {
                "ok": True,
                "status": getattr(r, "status", 200),
                "final_url": r.geturl(),
                "content_type": ct,
                "bytes": len(b),
                "sha256": sha(b),
                "truncated": truncated,
                "text": s,
            }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def normalize(s: str) -> str:
    # Decode common JS unicode escapes in memory only, then flatten markup.
    try:
        if "\\u" in s or "\\x" in s:
            s = bytes(s, "utf-8").decode("unicode_escape", "replace")
    except Exception:
        pass
    s = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def page_variants(page: int):
    pg = f"PA{page}"
    return [
        ("click2_text", "https://books.google.com/books?" + urllib.parse.urlencode({"id": VOL, "pg": pg, "jscmd": "click2", "output": "text"})),
        ("click2_text_alt", "https://books.google.com/books?" + urllib.parse.urlencode({"jscmd": "click2", "id": VOL, "pg": pg, "output": "text"})),
        ("html_text", "https://books.google.com/books?" + urllib.parse.urlencode({"id": VOL, "pg": pg, "output": "html_text"})),
    ]


def analyze_page(page: int):
    attempts = []
    selected = None
    for mode, url in page_variants(page):
        x = fetch(url)
        rec = {k: v for k, v in x.items() if k != "text"}
        rec["mode"] = mode
        if x.get("ok"):
            t = normalize(x["text"])
            low = t.lower()
            rec["normalized_chars"] = len(t)
            rec["normalized_sha256"] = sha(t.encode("utf-8")) if t else None
            rec["markers"] = {
                "article_title": "texts of the battle of kadesh" in low,
                "john_wilson": "john a. wilson" in low or "john wilson" in low,
                "kadesh": "kadesh" in low,
                "the_poem": "the poem" in low,
                "the_record": "the record" in low,
                "council_urges_peace": "council urges peace" in low,
                "printed_page": bool(re.search(rf"(?:^|\D){page}(?:\D|$)", t)),
            }
            # Candidate page representation must be non-trivial and not merely book metadata.
            candidate = len(t) >= 500 and (rec["markers"]["kadesh"] or rec["markers"]["printed_page"])
            rec["candidate_page_representation"] = candidate
            if candidate and selected is None:
                selected = {
                    "mode": mode,
                    "final_url": rec.get("final_url"),
                    "bytes": rec.get("bytes"),
                    "sha256": rec.get("sha256"),
                    "normalized_chars": rec.get("normalized_chars"),
                    "normalized_sha256": rec.get("normalized_sha256"),
                    "markers": rec.get("markers"),
                }
        attempts.append(rec)
    return {"printed_page": page, "attempts": attempts, "selected": selected}


def main():
    rows = [analyze_page(p) for p in PAGES]
    content = [r for r in rows if 266 <= r["printed_page"] <= 277]
    boundary = next(r for r in rows if r["printed_page"] == 278)

    selected_content = [r["selected"] for r in content if r["selected"]]
    distinct_hashes = {r["normalized_sha256"] for r in selected_content if r.get("normalized_sha256")}
    all_content = len(selected_content) == 12
    page266 = content[0]["selected"]
    page277 = content[-1]["selected"]
    page278 = boundary["selected"]

    title_ok = bool(page266 and page266["markers"]["article_title"] and page266["markers"]["john_wilson"])
    end_poem_ok = bool(page277 and (page277["markers"]["council_urges_peace"] or page277["markers"]["kadesh"]))
    record_boundary_ok = bool(page278 and page278["markers"]["the_record"])
    unique_enough = len(distinct_hashes) >= 10
    candidate_sufficient = all_content and title_ok and end_poem_ok and record_boundary_ok and unique_enough

    locus_hash_payload = [
        {"page": r["printed_page"], "sha256": r["selected"]["normalized_sha256"]}
        for r in content if r["selected"]
    ]
    locus_aggregate = sha(json.dumps(locus_hash_payload, sort_keys=True, separators=(",", ":")).encode()) if len(locus_hash_payload) == 12 else None

    out = {
        "schema": "topa.propaganda_defense.kadesh_google_page_text_probe.v0.6",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson, The Texts of the Battle of Kadesh, AJSL 43.4 (1927)",
            "doi": "10.1086/370157",
            "locus": "THE POEM, journal pp.266-278; Record excluded",
            "operational_boundary": "Poem content pp.266-277; p.278 is THE RECORD exclusion boundary",
            "changed": False
        },
        "google_books": {
            "volume_id": VOL,
            "viewability_prior": "FULL_VIEW_CONFIRMED_BY_DYNAMIC_VIEW_API_V0_3",
            "printed_pages_probed": PAGES,
            "rows": rows
        },
        "validation": {
            "all_12_poem_pages_have_candidate_representation": all_content,
            "distinct_content_page_hashes": len(distinct_hashes),
            "page_266_title_author_marker": title_ok,
            "page_277_end_poem_marker": end_poem_ok,
            "page_278_record_boundary_marker": record_boundary_ok,
            "candidate_content_sufficient": candidate_sufficient,
            "poem_pages_266_277_aggregate_sha256": locus_aggregate
        },
        "admission": {
            "diagnostic_can_justify_authoritative_retrieval_repair": candidate_sufficient,
            "br03_retrieval_pass": False,
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False
        },
        "laws": [
            "DIAGNOSTIC_CANDIDATE != AUTHORITATIVE_RETRIEVAL_PASS",
            "BOUNDARY_PAGE_IS_NOT_CONTENT_PAGE",
            "SAME_VOLUME_PAGE_HASHES_REQUIRED",
            "TRANSPORT_REPAIR != LOCUS_CHANGE",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_GOOGLE_PAGE_TEXT_PROBE_V0_6=COMPLETE")
    print(f"CONTENT_PAGES_RETRIEVED={len(selected_content)}/12")
    print(f"DISTINCT_PAGE_HASHES={len(distinct_hashes)}")
    print(f"PAGE266_TITLE_AUTHOR={str(title_ok).lower()}")
    print(f"PAGE277_END_POEM={str(end_poem_ok).lower()}")
    print(f"PAGE278_RECORD_BOUNDARY={str(record_boundary_ok).lower()}")
    print(f"CANDIDATE_CONTENT_SUFFICIENT={str(candidate_sufficient).lower()}")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
