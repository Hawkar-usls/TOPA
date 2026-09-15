#!/usr/bin/env python3
"""Diagnostic-only Google Books result-shape probe for frozen BR03 Kadesh.

No snippet text is persisted. The probe records JSON structure and page-reference
metadata only. It cannot unlock retrieval, coding, or SCORE.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_GOOGLE_SHAPE_PROBE.v0.4.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
VOL = "2l5uKJXiO70C"
QUERIES = [
    "The Texts of the Battle of Kadesh",
    "John A. Wilson",
    "THE POEM",
    "THE RECORD",
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/plain,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            b = r.read(8 * 1024 * 1024)
            ct = r.headers.get("Content-Type") or ""
            m = re.search(r"charset=([^;\s]+)", ct, re.I)
            enc = m.group(1).strip('"\'') if m else "utf-8"
            try:
                s = b.decode(enc, "replace")
            except LookupError:
                s = b.decode("utf-8", "replace")
            return {"ok": True, "status": getattr(r, "status", 200), "content_type": ct, "bytes": len(b), "sha256": sha(b), "text": s}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def typename(x):
    if isinstance(x, dict): return "object"
    if isinstance(x, list): return "array"
    if x is None: return "null"
    if isinstance(x, bool): return "bool"
    if isinstance(x, int): return "int"
    if isinstance(x, float): return "float"
    return "string"


def shape(node, path="$", depth=0, max_depth=7):
    out = []
    if depth > max_depth:
        return out
    if isinstance(node, dict):
        out.append({"path": path, "type": "object", "keys": sorted(str(k) for k in node.keys())})
        for k, v in node.items():
            out.extend(shape(v, f"{path}.{k}", depth + 1, max_depth))
    elif isinstance(node, list):
        out.append({"path": path, "type": "array", "length": len(node)})
        # Inspect first few items structurally only; no scalar values copied.
        for i, v in enumerate(node[:5]):
            out.extend(shape(v, f"{path}[{i}]", depth + 1, max_depth))
    return out


def find_page_dicts(node, path="$", out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        keys = set(node.keys())
        if keys & {"page_id", "page_number", "page_url"}:
            snippet = node.get("snippet_text")
            out.append({
                "path": path,
                "page_id": node.get("page_id"),
                "page_number": node.get("page_number"),
                "page_url": node.get("page_url"),
                "snippet_sha256": sha(str(snippet).encode("utf-8")) if snippet is not None else None,
                "keys": sorted(str(k) for k in node.keys()),
            })
        for k, v in node.items():
            find_page_dicts(v, f"{path}.{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            find_page_dicts(v, f"{path}[{i}]", out)
    return out


def main():
    queries = {}
    all_refs = []
    for q in QUERIES:
        url = "https://www.google.com/books?" + urllib.parse.urlencode({"id": VOL, "jscmd": "SearchWithinVolume2", "q": q})
        x = fetch(url)
        rec = {k: v for k, v in x.items() if k != "text"}
        if x.get("ok"):
            try:
                obj = json.loads(x["text"])
                rec["top_level_type"] = typename(obj)
                rec["top_level_keys"] = sorted(obj.keys()) if isinstance(obj, dict) else None
                rec["shape"] = shape(obj)
                refs = find_page_dicts(obj)
                rec["page_ref_count"] = len(refs)
                rec["page_refs"] = refs
                for r in refs:
                    rr = {"query": q, **r}
                    all_refs.append(rr)
            except Exception as e:
                rec["parse_error"] = f"{type(e).__name__}: {e}"
        queries[q] = rec

    # De-duplicate page refs without assuming page-number semantics.
    uniq = []
    seen = set()
    for r in all_refs:
        key = (r.get("page_id"), r.get("page_number"), r.get("page_url"))
        if key not in seen:
            seen.add(key)
            uniq.append({k: r.get(k) for k in ("page_id", "page_number", "page_url")})

    out = {
        "schema": "topa.propaganda_defense.kadesh_google_shape_probe.v0.4",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson, The Texts of the Battle of Kadesh, AJSL 43.4 (1927)",
            "doi": "10.1086/370157",
            "locus": "THE POEM, journal pp.266-278; Record excluded",
            "changed": False
        },
        "google_books_volume_id": VOL,
        "queries": queries,
        "unique_page_refs": uniq,
        "summary": {
            "unique_page_ref_count": len(uniq),
            "has_page_ids": any(x.get("page_id") for x in uniq),
            "has_page_numbers": any(x.get("page_number") is not None for x in uniq),
            "has_page_urls": any(x.get("page_url") for x in uniq),
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False,
            "next_gate": "BOUNDED_SAME_VOLUME_PAGE_REPRESENTATION_PROBE_ONLY_IF_PAGE_REFS_EXIST"
        },
        "laws": [
            "JSON_SHAPE != SOURCE_CONTENT",
            "SEARCH_SNIPPET != SOURCE_CONTENT",
            "PAGE_REFERENCE != RETRIEVED_PAGE",
            "TRANSPORT_REPAIR != LOCUS_CHANGE",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_GOOGLE_SHAPE_PROBE_V0_4=COMPLETE")
    print(f"UNIQUE_PAGE_REFS={len(uniq)}")
    print(f"HAS_PAGE_IDS={str(out['summary']['has_page_ids']).lower()}")
    print(f"HAS_PAGE_NUMBERS={str(out['summary']['has_page_numbers']).lower()}")
    print(f"HAS_PAGE_URLS={str(out['summary']['has_page_urls']).lower()}")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
