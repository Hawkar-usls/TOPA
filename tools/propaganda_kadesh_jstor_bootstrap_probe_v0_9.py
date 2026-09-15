#!/usr/bin/env python3
"""Diagnostic-only JSTOR bootstrap graph probe for frozen BR03 Kadesh.

Reads the publicly accessible 3038-byte client shell for stable 528771, extracts
same-origin asset/link references, then inspects a bounded set of JSTOR JS/JSON
assets for route strings related to stable/pdf/xml/download. No article/source
text is persisted and no arbitrary endpoint guessing is performed.
"""
from __future__ import annotations

import hashlib
import json
import re
import ssl
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_JSTOR_BOOTSTRAP_PROBE.v0.9.json")
ROOT = "https://www.jstor.org"
LANDING = f"{ROOT}/stable/528771"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
MAX_ASSETS = 20


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def opener():
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar()),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )


def fetch(op, url: str, max_bytes=8 * 1024 * 1024, accept="*/*"):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.8",
        "Referer": LANDING,
    })
    try:
        with op.open(req, timeout=40) as r:
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


def absolutize(ref: str) -> str | None:
    if not ref or ref.startswith(("data:", "javascript:", "mailto:")):
        return None
    u = urllib.parse.urljoin(LANDING, ref)
    try:
        p = urllib.parse.urlparse(u)
    except Exception:
        return None
    if p.scheme != "https" or p.netloc not in {"www.jstor.org", "jstor.org"}:
        return None
    return u


def shell_refs(text: str):
    refs = []
    for pat in [r'''(?:src|href)=["']([^"']+)["']''', r'''content=["'](https?://[^"']+)["']''']:
        for m in re.finditer(pat, text, re.I):
            u = absolutize(m.group(1))
            if u and u not in refs:
                refs.append(u)
    # Raw path literals often appear in hydration/bootstrap scripts.
    for m in re.finditer(r'''["']((?:/[^"']{1,300})(?:528771|pdf|xml|download)[^"']*)["']''', text, re.I):
        u = absolutize(m.group(1))
        if u and u not in refs:
            refs.append(u)
    return refs


def interesting_strings(text: str):
    # Return route-like strings only, never prose/article content.
    out = []
    patterns = [
        r'''https://www\.jstor\.org/[A-Za-z0-9_?&=./:%+\-]{1,400}''',
        r'''/[A-Za-z0-9_?&=./:%+\-]{1,300}(?:528771|stable|pdf|xml|download)[A-Za-z0-9_?&=./:%+\-]{0,200}''',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            s = m.group(0).rstrip("'\"`),;}")
            low = s.lower()
            if any(k in low for k in ("528771", "/pdf", "xml", "download", "/stable/")) and s not in out:
                out.append(s)
                if len(out) >= 100:
                    return out
    return out


def main():
    op = opener()
    land = fetch(op, LANDING, max_bytes=2 * 1024 * 1024, accept="text/html,application/xhtml+xml")
    text = land.get("body", b"").decode("utf-8", "replace") if land.get("ok") else ""
    refs = shell_refs(text)

    assets = []
    candidate_routes = []
    for u in refs:
        low = u.lower()
        if any(x in low for x in (".js", ".json", "_next", "static", "manifest", "build")):
            if len(assets) >= MAX_ASSETS:
                break
            x = fetch(op, u, max_bytes=8 * 1024 * 1024, accept="application/javascript,text/javascript,application/json,text/plain,*/*")
            rec = pub(x)
            if x.get("ok"):
                body_text = x["body"].decode("utf-8", "replace")
                rec["interesting_route_strings"] = interesting_strings(body_text)
                for s in rec["interesting_route_strings"]:
                    au = absolutize(s)
                    if au and au not in candidate_routes:
                        candidate_routes.append(au)
            assets.append(rec)

    # Also inspect route-like strings directly in shell.
    for s in interesting_strings(text):
        au = absolutize(s)
        if au and au not in candidate_routes:
            candidate_routes.append(au)

    # Bound the follow-up: only discovered same-origin routes, never invented suffixes.
    route_results = []
    for u in candidate_routes[:30]:
        if not any(k in u.lower() for k in ("528771", "/pdf", "xml", "download")):
            continue
        x = fetch(op, u, max_bytes=40 * 1024 * 1024, accept="application/pdf,application/xml,text/xml,application/json,text/html;q=0.8,*/*;q=0.5")
        b = x.get("body", b"")
        route_results.append({
            **pub(x),
            "pdf_magic": bool(b.startswith(b"%PDF")),
            "xml_magic": bool(re.match(br"\s*<\?xml|\s*<article|\s*<body", b[:200], re.I)),
            "html_shell_same_sha": x.get("sha256") == "32ed63159c77e21ee19ca1b9aa3213ccf0218eb59539560b132a8e68ef0e18ea",
        })

    usable = [r for r in route_results if r.get("pdf_magic") or r.get("xml_magic")]
    out = {
        "schema": "topa.propaganda_defense.kadesh_jstor_bootstrap_probe.v0.9",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson, The Texts of the Battle of Kadesh, AJSL 43.4 (1927)",
            "doi": "10.1086/370157",
            "jstor_stable_id": "528771",
            "locus": "THE POEM, journal pp.266-278; Record excluded",
            "changed": False
        },
        "landing": pub(land),
        "same_origin_refs": refs,
        "inspected_assets": assets,
        "discovered_candidate_routes": candidate_routes,
        "candidate_route_results": route_results,
        "summary": {
            "same_origin_ref_count": len(refs),
            "asset_count_inspected": len(assets),
            "discovered_candidate_route_count": len(candidate_routes),
            "usable_pdf_or_xml_route_count": len(usable),
            "can_justify_next_content_probe": bool(usable),
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False
        },
        "laws": [
            "DISCOVERED_ROUTE_ONLY_NO_ENDPOINT_GUESSING",
            "BOOTSTRAP_ASSET != SOURCE_CONTENT",
            "PDF_OR_XML_MAGIC_REQUIRED_BEFORE_CONTENT_INSPECTION",
            "TRANSPORT_REPAIR != LOCUS_CHANGE",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_JSTOR_BOOTSTRAP_PROBE_V0_9=COMPLETE")
    print(f"SAME_ORIGIN_REFS={len(refs)}")
    print(f"ASSETS_INSPECTED={len(assets)}")
    print(f"CANDIDATE_ROUTES={len(candidate_routes)}")
    print(f"USABLE_PDF_XML_ROUTES={len(usable)}")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
