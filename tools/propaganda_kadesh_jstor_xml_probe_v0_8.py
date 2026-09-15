#!/usr/bin/env python3
"""Diagnostic-only official JSTOR XML probe for frozen BR03 Kadesh.

Uses the XML route exposed by JSTOR's own issue page for stable object 528771.
No article text is persisted. Only source-byte hashes, XML structure counts,
page-marker metadata and content marker booleans are written.
"""
from __future__ import annotations

import hashlib
import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_JSTOR_XML_PROBE.v0.8.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str, max_bytes=30 * 1024 * 1024):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/xml,text/xml,application/xhtml+xml,text/html;q=0.8,*/*;q=0.5",
        "Accept-Language": "en-US,en;q=0.8",
        "Referer": "https://www.jstor.org/stable/i223075",
    })
    try:
        with urllib.request.urlopen(req, timeout=45, context=ssl.create_default_context()) as r:
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


def lname(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def inspect_xml(b: bytes):
    # Reject obvious HTML shell before attempting XML interpretation.
    head = b[:500].lower()
    if b"<html" in head or b"<!doctype html" in head:
        return {"xml_ok": False, "classification": "HTML_SHELL"}
    try:
        root = ET.fromstring(b)
    except Exception as e:
        return {"xml_ok": False, "classification": "XML_PARSE_FAIL", "error": f"{type(e).__name__}: {e}"}

    elems = list(root.iter())
    tag_counts = {}
    page_breaks = []
    for el in elems:
        n = lname(el.tag)
        tag_counts[n] = tag_counts.get(n, 0) + 1
        if n.lower() in {"pb", "page", "page-start", "pagebreak", "page-break"}:
            page_breaks.append({"tag": n, "attrs": {k: v for k, v in el.attrib.items() if k.lower() in {"n", "id", "page", "seq", "label"}}})

    text = " ".join(t.strip() for t in root.itertext() if t and t.strip())
    norm = re.sub(r"\s+", " ", text).strip()
    low = norm.lower()
    title = "texts of the battle of kadesh" in low
    author = "john a. wilson" in low or "john a wilson" in low or "johna. wilson" in low
    f266 = bool(re.search(r"(?:^|\D)266(?:\D|$)", norm))
    l287 = bool(re.search(r"(?:^|\D)287(?:\D|$)", norm))
    council = "council urges peace" in low
    record = "the record" in low
    poem = "the poem" in low
    body_tags = tag_counts.get("body", 0)
    paragraph_count = tag_counts.get("p", 0)
    substantial = len(norm) >= 15000 and paragraph_count >= 20
    identity_ok = title and author and f266 and l287
    content_ok = substantial and council and record and (poem or "amons aid" in low or "amons aid invoked" in low)

    # Page-boundary readiness: either explicit page elements/attrs include 266/278,
    # or textual journal page headers provide both numbers. Full-locus extraction is
    # deferred to authoritative replay; diagnostic only establishes reconstructibility.
    pb_text = json.dumps(page_breaks, ensure_ascii=False)
    page_266_signal = "266" in pb_text or f266
    page_278_signal = "278" in pb_text or bool(re.search(r"(?:^|\D)278(?:\D|$)", norm))
    sufficient = identity_ok and content_ok and page_266_signal and page_278_signal

    return {
        "xml_ok": True,
        "root_tag": lname(root.tag),
        "element_count": len(elems),
        "tag_counts": tag_counts,
        "page_break_count": len(page_breaks),
        "page_breaks": page_breaks[:100],
        "normalized_text_chars": len(norm),
        "normalized_text_sha256": sha(norm.encode("utf-8")),
        "markers": {
            "article_title": title,
            "john_wilson": author,
            "page_266": f266,
            "page_278": page_278_signal,
            "page_287": l287,
            "the_poem": poem,
            "council_urges_peace": council,
            "the_record": record,
        },
        "substantial_article_body": substantial,
        "identity_ok": identity_ok,
        "content_and_boundary_reconstructible": sufficient,
    }


def main():
    urls = [
        "https://www.jstor.org/doi/xml/10.2307/528771",
        "https://www.jstor.org/stable/xml/528771.xml",
        "https://www.jstor.org/stable/xml/528771",
    ]
    attempts = []
    chosen = None
    for url in urls:
        x = fetch(url)
        rec = pub(x)
        if x.get("ok"):
            ins = inspect_xml(x["body"])
            rec["inspection"] = ins
            if ins.get("content_and_boundary_reconstructible") and chosen is None:
                chosen = {
                    "requested_url": url,
                    "final_url": x.get("final_url"),
                    "bytes": x.get("bytes"),
                    "source_sha256": x.get("sha256"),
                    "inspection": ins,
                }
        attempts.append(rec)

    out = {
        "schema": "topa.propaganda_defense.kadesh_jstor_xml_probe.v0.8",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson, The Texts of the Battle of Kadesh, AJSL 43.4 (1927)",
            "doi": "10.1086/370157",
            "jstor_stable_id": "528771",
            "locus": "THE POEM, journal pp.266-278; Record excluded",
            "operational_boundary": "Poem content pp.266-277; p.278 is THE RECORD exclusion boundary",
            "changed": False
        },
        "attempts": attempts,
        "chosen_candidate": chosen,
        "admission": {
            "diagnostic_can_justify_authoritative_retrieval_repair": bool(chosen),
            "br03_retrieval_pass": False,
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False
        },
        "laws": [
            "JSTOR_XML_LINK_IS_SAME_SOURCE_ROOT_NOT_NEW_WITNESS",
            "METADATA_ONLY_XML != ARTICLE_CONTENT",
            "HTML_SHELL != XML",
            "DIAGNOSTIC_RECONSTRUCTIBLE != AUTHORITATIVE_RETRIEVAL_PASS",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_JSTOR_XML_PROBE_V0_8=COMPLETE")
    print("XML_CONTENT_CANDIDATE_FOUND=" + str(bool(chosen)).lower())
    if chosen:
        ins = chosen["inspection"]
        print(f"SOURCE_BYTES={chosen['bytes']}")
        print(f"SOURCE_SHA256={chosen['source_sha256']}")
        print(f"TEXT_CHARS={ins['normalized_text_chars']}")
        print(f"PAGE_BREAKS={ins['page_break_count']}")
        print(f"TITLE_AUTHOR={str(ins['identity_ok']).lower()}")
        print(f"BOUNDARY_RECONSTRUCTIBLE={str(ins['content_and_boundary_reconstructible']).lower()}")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
