#!/usr/bin/env python3
"""Diagnostic-only browser-rendering proxy probe for frozen BR03 Kadesh.

Jina Reader is used only as an HTTP/browser rendering transport. It has zero
source/evidence authority. Targets are ordered by provenance: official UChicago,
official JSTOR stable object, then two exact-scan Scribd mirrors. No returned
source prose is persisted; only hashes, lengths, page geometry and marker booleans.
"""
from __future__ import annotations

import hashlib
import json
import re
import ssl
import urllib.request
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_READER_PROXY_PROBE.v0.15.json")
UA = "TOPA-Kadesh-Reader-Proxy-Probe/0.15 (+https://github.com/Hawkar-usls/TOPA)"
TARGETS = [
    {
        "id": "UCHICAGO_DOI",
        "target": "https://www.journals.uchicago.edu/doi/10.1086/370157",
        "chain_class": "RENDERING_PROXY_OVER_SOURCE_AUTHORITY",
        "mirror_layers": 0,
    },
    {
        "id": "JSTOR_STABLE_528771",
        "target": "https://www.jstor.org/stable/528771",
        "chain_class": "RENDERING_PROXY_OVER_SOURCE_AUTHORITY",
        "mirror_layers": 0,
    },
    {
        "id": "SCRIBD_462138503",
        "target": "https://www.scribd.com/document/462138503/The-Texts-of-the-Battle-of-Kadesh",
        "chain_class": "RENDERING_PROXY_OVER_EXACT_SCAN_MIRROR",
        "mirror_layers": 1,
    },
    {
        "id": "SCRIBD_493951399",
        "target": "https://www.scribd.com/document/493951399/Wilson-John-The-Texts-of-the-Battle-of-Kadesh",
        "chain_class": "RENDERING_PROXY_OVER_EXACT_SCAN_MIRROR",
        "mirror_layers": 1,
    },
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str, max_bytes=8 * 1024 * 1024):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/plain,text/markdown,*/*;q=0.5",
        "X-Return-Format": "markdown",
        "X-Engine": "browser",
    })
    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
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
                "sha256": sha(b),
                "truncated": truncated,
                "body": b,
            }
    except Exception as e:
        return {"ok": False, "requested_url": url, "error": f"{type(e).__name__}: {e}"}


def pub(x):
    return {k: v for k, v in x.items() if k != "body"}


def normalize(b: bytes) -> str:
    s = b.decode("utf-8", "replace")
    return re.sub(r"\s+", " ", s).strip()


def positions(text: str, pattern: str):
    return [m.start() for m in re.finditer(pattern, text, re.I)]


def near(text: str, pos: int, pattern: str, radius=1800):
    if pos is None:
        return False
    a = max(0, pos - radius)
    z = min(len(text), pos + radius)
    return bool(re.search(pattern, text[a:z], re.I))


def analyze(text: str):
    low = text.lower()
    title = "the texts of the battle of kadesh" in low
    author = "john a. wilson" in low or "john a wilson" in low or "johna. wilson" in low
    journal = "american journal of semitic languages and literatures" in low
    year = "1927" in low
    pages_range = bool(re.search(r"266\s*[-–—]\s*287", text))
    uchicago = "university of chicago press" in low or "university of chicago" in low
    jstor = "jstor" in low
    stable = "528771" in low
    poem = "the poem" in low
    council = "the council urges peace" in low
    record = "the record" in low
    comment = "comment on the texts" in low

    p266s = positions(text, r"(?<!\d)266(?!\d)")
    p277s = positions(text, r"(?<!\d)277(?!\d)")
    p278s = positions(text, r"(?<!\d)278(?!\d)")
    p287s = positions(text, r"(?<!\d)287(?!\d)")

    p266_geom = any(near(text, p, r"the poem|texts of the battle of kadesh", 2200) for p in p266s)
    p277_geom = any(near(text, p, r"the council urges peace|end of poem", 2200) for p in p277s)
    p278_geom = any(near(text, p, r"the record", 1600) for p in p278s)
    p287_geom = any(near(text, p, r"comment on the texts|prisoners presented to amon", 2200) for p in p287s)

    page_numbers = sorted({int(x) for x in re.findall(r"(?<!\d)(26[6-9]|27\d|28[0-7])(?!\d)", text)})
    # Strong full-locus representation: substantive output and enough page geometry
    # to reconstruct the frozen p266 start and p278 exclusion boundary.
    identity_ok = title and author and journal and year and (uchicago or jstor)
    geometry_ok = p266_geom and p277_geom and p278_geom and p287_geom
    content_ok = len(text) >= 35_000 and poem and council and record and comment and len(page_numbers) >= 16
    sufficient = identity_ok and geometry_ok and content_ok

    # Persist positions/hashes, not source text.
    anchor_hashes = {}
    for label, ps in {"p266": p266s, "p277": p277s, "p278": p278s, "p287": p287s}.items():
        hashes = []
        for p in ps[:8]:
            a = max(0, p - 1200); z = min(len(text), p + 1200)
            hashes.append(sha(text[a:z].encode("utf-8")))
        anchor_hashes[label] = hashes

    return {
        "normalized_chars": len(text),
        "normalized_sha256": sha(text.encode("utf-8")) if text else None,
        "identity": {
            "title": title,
            "john_a_wilson": author,
            "journal": journal,
            "year_1927": year,
            "page_range_266_287": pages_range,
            "university_chicago": uchicago,
            "jstor": jstor,
            "stable_528771": stable,
        },
        "content_markers": {
            "the_poem": poem,
            "council_urges_peace": council,
            "the_record": record,
            "comment_on_the_texts": comment,
        },
        "page_geometry": {
            "page_numbers_seen_266_287": page_numbers,
            "coverage_count": len(page_numbers),
            "p266_anchor_ok": p266_geom,
            "p277_anchor_ok": p277_geom,
            "p278_record_boundary_ok": p278_geom,
            "p287_end_anchor_ok": p287_geom,
            "anchor_window_sha256": anchor_hashes,
        },
        "identity_ok": identity_ok,
        "geometry_ok": geometry_ok,
        "content_ok": content_ok,
        "candidate_content_sufficient": sufficient,
    }


def main():
    rows = []
    for t in TARGETS:
        reader_url = "https://r.jina.ai/" + t["target"]
        x = fetch(reader_url)
        rec = {
            "id": t["id"],
            "target_url": t["target"],
            "reader_url": reader_url,
            "chain_class": t["chain_class"],
            "mirror_layers": t["mirror_layers"],
            "reader_transport": pub(x),
        }
        if x.get("ok"):
            rec["analysis"] = analyze(normalize(x["body"]))
        rows.append(rec)

    strong = [r for r in rows if r.get("analysis", {}).get("candidate_content_sufficient")]
    # Prefer proxy-over-authority over proxy-over-mirror.
    strong_sorted = sorted(strong, key=lambda r: (r["mirror_layers"], r["id"]))
    chosen = strong_sorted[0] if strong_sorted else None

    out = {
        "schema": "topa.propaganda_defense.kadesh_reader_proxy_probe.v0.15",
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
        "transport_firewall": {
            "jina_reader_evidence_authority": 0,
            "scribd_evidence_authority": 0,
            "proxy_adds_independent_source_root": False,
            "mirror_adds_independent_source_root": False,
            "source_root_count_if_admitted": 1,
            "authority_remains": "Wilson / AJSL / UChicago / JSTOR",
        },
        "targets": rows,
        "diagnostic_summary": {
            "strong_candidate_count": len(strong),
            "strong_candidate_ids": [r["id"] for r in strong_sorted],
            "preferred_candidate_id": chosen["id"] if chosen else None,
            "preferred_chain_class": chosen["chain_class"] if chosen else None,
            "can_enter_separate_transport_admission_review": bool(chosen),
            "br03_retrieval_pass": False,
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False,
        },
        "laws": [
            "RENDERING_PROXY != SOURCE_AUTHORITY",
            "PROXY_OUTPUT != INDEPENDENT_WITNESS",
            "PROXY_OVER_MIRROR_ADDS_ZERO_SOURCE_ROOTS",
            "HASHABLE_FULL_LOCUS_AND_BOUNDARY_GEOMETRY_REQUIRED",
            "DIAGNOSTIC_PROXY_PASS != BR03_RETRIEVAL_PASS",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_READER_PROXY_PROBE_V0_15=COMPLETE")
    print(f"STRONG_CANDIDATES={len(strong)}")
    print("STRONG_IDS=" + (",".join(r["id"] for r in strong_sorted) if strong_sorted else "NONE"))
    print("PREFERRED=" + (chosen["id"] if chosen else "NONE"))
    print("TRANSPORT_ADMISSION_REVIEW_ELIGIBLE=" + str(bool(chosen)).lower())
    print("BR03_RETRIEVAL_PASS=false")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
