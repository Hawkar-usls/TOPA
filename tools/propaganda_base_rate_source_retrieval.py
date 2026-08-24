#!/usr/bin/env python3
"""Retrieve/hash frozen ancient base-rate source representations without mirroring them.

Outputs only receipts/hashes/metadata. Source bodies are kept in memory and never written
into the repository. A successful HTTP request is not enough: each control must satisfy
content markers appropriate to the frozen representation before it can be classified
TEXT_CONTENT_SUFFICIENT.
"""
from __future__ import annotations

import hashlib
import json
import re
import ssl
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "research" / "propaganda-defense"
OUT = R / "execution" / "BASE_RATE_SOURCE_RETRIEVAL_RUN.v0.1.json"
UA = "TOPA-Research-Receipt/0.1 (+https://github.com/Hawkar-usls/TOPA)"
TIMEOUT = 35
MAX_BYTES = 30 * 1024 * 1024


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw)


def fetch(url: str, *, max_bytes: int = MAX_BYTES) -> dict:
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    t0 = time.time()
    try:
        with urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as resp:
            data = resp.read(max_bytes + 1)
            truncated = len(data) > max_bytes
            if truncated:
                data = data[:max_bytes]
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return {
                "ok": True,
                "requested_url": url,
                "final_url": resp.geturl(),
                "status": getattr(resp, "status", 200),
                "content_type": headers.get("content-type"),
                "etag": headers.get("etag"),
                "last_modified": headers.get("last-modified"),
                "content_length_header": headers.get("content-length"),
                "bytes": len(data),
                "sha256": sha256(data),
                "truncated": truncated,
                "elapsed_ms": int((time.time() - t0) * 1000),
                "_data": data,
            }
    except HTTPError as e:
        return {"ok": False, "requested_url": url, "status": e.code, "error": f"HTTPError: {e}", "elapsed_ms": int((time.time()-t0)*1000)}
    except (URLError, TimeoutError, ssl.SSLError, OSError) as e:
        return {"ok": False, "requested_url": url, "status": None, "error": f"{type(e).__name__}: {e}", "elapsed_ms": int((time.time()-t0)*1000)}


def public_receipt(x: dict) -> dict:
    return {k: v for k, v in x.items() if k != "_data"}


def text_of(x: dict) -> str:
    if not x.get("ok"):
        return ""
    data = x.get("_data", b"")
    return data.decode("utf-8", errors="ignore")


def marker_check(text: str, groups: list[list[str]]) -> dict:
    """Every group needs at least one marker present (case-insensitive)."""
    low = text.lower()
    checks = []
    ok = True
    for group in groups:
        hit = next((m for m in group if m.lower() in low), None)
        checks.append({"any_of": group, "hit": hit})
        ok &= hit is not None
    return {"pass": bool(ok), "checks": checks}


def aggregate(components: list[dict]) -> str:
    return canonical_hash([
        {"requested_url": c.get("requested_url"), "final_url": c.get("final_url"), "sha256": c.get("sha256"), "bytes": c.get("bytes"), "ok": c.get("ok")}
        for c in components
    ])


def generic_multi(control_id: str, urls: list[str], marker_groups: list[list[str]], *, require_all=True, role="SOURCE_BYTES") -> dict:
    comps = [fetch(u) for u in urls]
    text = "\n".join(text_of(c) for c in comps)
    markers = marker_check(text, marker_groups)
    http_ok = all(c.get("ok") and not c.get("truncated") for c in comps) if require_all else any(c.get("ok") and not c.get("truncated") for c in comps)
    sufficient = http_ok and markers["pass"]
    return {
        "id": control_id,
        "representation_class": role if sufficient else ("PARTIAL" if any(c.get("ok") for c in comps) else "BLOCKED"),
        "content_sufficient_for_frozen_locus": sufficient,
        "components": [public_receipt(c) for c in comps],
        "aggregate_sha256": aggregate(comps),
        "marker_validation": markers,
    }


def br03_kadesh() -> dict:
    # Predeclared same-publication representations. PDF is preferred; HTML may only be metadata.
    pdf = fetch("https://www.journals.uchicago.edu/doi/pdf/10.1086/370157")
    pdf_ok = pdf.get("ok") and not pdf.get("truncated") and pdf.get("bytes", 0) > 20_000 and b"%PDF" in pdf.get("_data", b"")[:16]
    html = fetch("https://www.journals.uchicago.edu/doi/10.1086/370157")
    html_markers = marker_check(text_of(html), [["The Texts of the Battle of Kadesh"], ["THE POEM", "The Poem"], ["266", "Pages: 266"]])
    html_fullish = html.get("ok") and html_markers["pass"] and len(text_of(html)) > 20_000
    sufficient = bool(pdf_ok or html_fullish)
    chosen = "publisher_pdf" if pdf_ok else ("publisher_html_fulltext" if html_fullish else None)
    return {
        "id": "BR03_KADESH",
        "representation_class": "SOURCE_BYTES" if sufficient else ("METADATA_ONLY" if html.get("ok") else "BLOCKED"),
        "content_sufficient_for_frozen_locus": sufficient,
        "chosen_representation": chosen,
        "components": [public_receipt(pdf), public_receipt(html)],
        "aggregate_sha256": aggregate([pdf, html]),
        "html_marker_validation": html_markers,
        "frozen_locus": "Wilson 1927 THE POEM, pp. 266-278; Record excluded",
    }


def br05_hittite() -> dict:
    catalog = fetch("https://www.hethport.uni-wuerzburg.de/hetkonk/hetkonk_abfrage.php?c=62")
    pdf = fetch("https://iris.unito.it/retrieve/e27ce42b-d27c-2581-e053-d805fe0acbaa/Devecchi-RAI54.pdf")
    cat_m = marker_check(text_of(catalog), [["CTH 62", "62"], ["Duppi", "Duppi-Te"], ["KBo 5.9", "KUB 3.14", "KUB III 14"]])
    pdf_ok = pdf.get("ok") and not pdf.get("truncated") and pdf.get("bytes", 0) > 20_000 and b"%PDF" in pdf.get("_data", b"")[:16]
    sufficient = bool(catalog.get("ok") and cat_m["pass"] and pdf_ok)
    return {
        "id": "BR05_HITTITE_TREATY",
        "representation_class": "SOURCE_BYTES" if sufficient else ("PARTIAL" if catalog.get("ok") or pdf.get("ok") else "BLOCKED"),
        "content_sufficient_for_frozen_locus": sufficient,
        "components": [public_receipt(catalog), public_receipt(pdf)],
        "aggregate_sha256": aggregate([catalog, pdf]),
        "catalog_marker_validation": cat_m,
        "frozen_locus": "CTH 62.II A i 19′-28′",
    }


def scaife_thucydides() -> dict:
    # Hash all chapter-level SSR representations 2.34-2.46, with Greek left and English right.
    comps = []
    chapters = list(range(34, 47))
    for ch in chapters:
        urn = f"urn:cts:greekLit:tlg0003.tlg001.perseus-grc2:2.{ch}"
        u = "https://scaife.perseus.org/reader/" + quote(urn, safe="") + "/?right=1st1K-eng1"
        comps.append(fetch(u, max_bytes=4 * 1024 * 1024))
    bodies = [text_of(c) for c in comps]
    success_count = sum(1 for c in comps if c.get("ok") and not c.get("truncated"))
    # Every chapter page should contain a CTS/Thucydides signal. The aggregate should contain Greek letters.
    per_page_marker = all(("tlg0003" in t and ("Thucydides" in t or "Ἱστορίαι" in t)) for t in bodies if t)
    greek_present = any(re.search(r"[\u0370-\u03ff]", t) for t in bodies)
    sufficient = success_count == len(chapters) and per_page_marker and greek_present
    return {
        "id": "BR06_THUCYDIDES",
        "representation_class": "VERSIONED_CORPUS_REPRESENTATION" if sufficient else ("PARTIAL" if success_count else "BLOCKED"),
        "content_sufficient_for_frozen_locus": sufficient,
        "chapters": [f"2.{x}" for x in chapters],
        "component_count": len(comps),
        "successful_components": success_count,
        "components": [public_receipt(c) for c in comps],
        "aggregate_sha256": aggregate(comps),
        "validation": {"per_page_work_marker": per_page_marker, "greek_script_present": greek_present},
    }


def perseus_res_gestae() -> dict:
    sections = ["preface", "1", "8", "25", "34"]
    comps = []
    for s in sections:
        urn = f"urn:cts:latinLit:phi1221.phi007.perseus-lat1:{s}"
        u = "https://www.perseus.tufts.edu/hopper/text?doc=" + quote(urn, safe="")
        comps.append(fetch(u, max_bytes=4 * 1024 * 1024))
    texts = [text_of(c) for c in comps]
    success_count = sum(1 for c in comps if c.get("ok") and not c.get("truncated"))
    markers = [
        "Rerum gestarum divi Augusti",
        "Annos undeviginti natus",
        "multa exempla maiorum",
        "Iuravit in mea verba tota Italia",
        "per consensum universorum",
    ]
    marker_hits = [m for m in markers if any(m.lower() in t.lower() for t in texts)]
    sufficient = success_count == len(sections) and len(marker_hits) == len(markers)
    return {
        "id": "BR07_RES_GESTAE",
        "representation_class": "VERSIONED_CORPUS_REPRESENTATION" if sufficient else ("PARTIAL" if success_count else "BLOCKED"),
        "content_sufficient_for_frozen_locus": sufficient,
        "sections": sections,
        "components": [public_receipt(c) for c in comps],
        "aggregate_sha256": aggregate(comps),
        "validation": {"required_markers": markers, "marker_hits": marker_hits},
    }


def tla_ptahhotep() -> dict:
    root_url = "https://thesaurus-linguae-aegyptiae.de/text/C6KGH3XC7RGU3DSL7HKYY2K3WM"
    root = fetch(root_url, max_bytes=8 * 1024 * 1024)
    text = text_of(root)
    meta = marker_check(text, [["C6KGH3XC7RGU3DSL7HKYY2K3WM"], ["Die Lehre des Ptahhotep"], ["Corpus edition 20", "Corpus edition"], ["Peter Dils"]])
    # Detect whether server-side representation exposes enough token/sentence links to reconstruct content.
    token_ids = sorted(set(re.findall(r"/sentence/token/([A-Za-z0-9_-]{12,})", text)))
    sample_receipts = []
    # Fetch at most the first and last 5 discovered token pages; this is validation, not the source body.
    for tok in (token_ids[:5] + token_ids[-5:] if len(token_ids) > 5 else token_ids):
        sample_receipts.append(fetch(f"https://thesaurus-linguae-aegyptiae.de/sentence/token/{tok}", max_bytes=2 * 1024 * 1024))
    # Whole-text coding needs a versioned representation of the whole text, not merely metadata/sample tokens.
    enough_token_links = len(token_ids) >= 20
    sufficient = bool(root.get("ok") and meta["pass"] and enough_token_links)
    return {
        "id": "BR08_PTAHHOTEP",
        "representation_class": "VERSIONED_CORPUS_REPRESENTATION" if sufficient else ("METADATA_ONLY" if root.get("ok") and meta["pass"] else "BLOCKED"),
        "content_sufficient_for_frozen_locus": sufficient,
        "components": [public_receipt(root)] + [public_receipt(x) for x in sample_receipts],
        "aggregate_sha256": aggregate([root] + sample_receipts),
        "metadata_validation": meta,
        "token_links_discovered_in_root_representation": len(token_ids),
        "token_sample_ids": token_ids[:5] + token_ids[-5:] if len(token_ids) > 5 else token_ids,
        "boundary": "Metadata-only remains insufficient for whole persistent Text ID coding.",
    }


def main() -> int:
    results = []
    results.append(generic_multi(
        "BR01_HAMMURABI",
        ["https://avalon.law.yale.edu/ancient/hamcode.asp"],
        [["The Code of Hammurabi"], ["Translated by L. W. King", "L. W. King"], ["CODE OF LAWS"], ["THE EPILOGUE"]],
    ))
    results.append(generic_multi(
        "BR02_BEHISTUN",
        [
            "https://www.livius.org/sources/content/behistun-persian-text/behistun-t-02/",
            "https://www.livius.org/sources/content/behistun-persian-text/behistun-t-36/",
            "https://www.livius.org/sources/content/behistun-persian-text/behistun-t-42/",
        ],
        [["Column i, lines 9-17", "lines 9-17"], ["Column iv, lines 31-39", "lines 31-39"], ["Column iv, lines 87-92", "lines 87-92"], ["Dârayavauš", "Darius"]],
    ))
    results.append(br03_kadesh())
    results.append(generic_multi(
        "BR04_NEO_ASSYRIAN_ANNALS",
        ["https://oracc.museum.upenn.edu/rinap/rinap3/Q003475/html"],
        [["Sennacherib", "Sîn-aḫḫē-erība"], ["Q003475", "Sennacherib 001", "1–4", "1-4"]],
        role="VERSIONED_CORPUS_REPRESENTATION",
    ))
    results.append(br05_hittite())
    results.append(scaife_thucydides())
    results.append(perseus_res_gestae())
    results.append(tla_ptahhotep())

    sufficient = [r["id"] for r in results if r.get("content_sufficient_for_frozen_locus")]
    blocked = [r["id"] for r in results if not r.get("content_sufficient_for_frozen_locus")]
    receipt = {
        "schema": "topa.propaganda_defense.base_rate_source_retrieval_run.v0.1",
        "date": "2026-08-24",
        "status": "EIGHT_OF_EIGHT_RETRIEVAL_CONTENT_SUFFICIENT" if len(sufficient) == 8 else "PARTIAL_FAIL_CLOSED",
        "policy": {
            "source_bodies_persisted": False,
            "descriptor_hash_is_source_hash": False,
            "http_200_alone_is_sufficient": False,
            "silent_source_substitution": False,
            "semantic_feature_values_generated": False,
        },
        "results": results,
        "summary": {
            "content_sufficient": len(sufficient),
            "required": 8,
            "sufficient_ids": sufficient,
            "blocked_or_partial_ids": blocked,
            "semantic_values_populated": 0,
            "base_rate_coding_permission_candidate": len(sufficient) == 8,
            "score_permission": False,
        },
        "epistemic_effect": "RETRIEVAL_AND_REPRODUCIBILITY_RECEIPT_ONLY_NO_MANIPULATION_CLASSIFICATION",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_BASE_RATE_RETRIEVAL_RUN=" + receipt["status"])
    print(f"CONTENT_SUFFICIENT={len(sufficient)}/8")
    print("SUFFICIENT_IDS=" + ",".join(sufficient))
    print("BLOCKED_OR_PARTIAL_IDS=" + ",".join(blocked))
    print("SEMANTIC_VALUES_POPULATED=0")
    print("SCORE_PERMISSION=false")
    # Fail closed when anything is insufficient, while still leaving receipt for upload.
    return 0 if len(sufficient) == 8 else 2


if __name__ == "__main__":
    sys.exit(main())
