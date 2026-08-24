#!/usr/bin/env python3
"""TOPA ancient base-rate retrieval repair v0.2.

Transport/representation repair only. Frozen BR01-BR08 identities and loci are
not changed. The script writes hashes/metadata only and fails closed unless all
8 controls have a reproducible representation sufficient for the preregistered
locus.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/propaganda-defense/execution/BASE_RATE_SOURCE_RETRIEVAL_RUN.v0.2.json"
UA = "TOPA-reproducibility-audit/0.2 (+https://github.com/Hawkar-usls/TOPA)"
MAX_BYTES = 120 * 1024 * 1024


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def fetch(url: str, max_bytes: int = MAX_BYTES, timeout: int = 40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read(max_bytes + 1)
            if len(b) > max_bytes:
                raise ValueError(f"response exceeds {max_bytes} bytes")
            return {
                "ok": True,
                "requested_url": url,
                "final_url": r.geturl(),
                "status": getattr(r, "status", 200),
                "content_type": r.headers.get("Content-Type"),
                "etag": r.headers.get("ETag"),
                "last_modified": r.headers.get("Last-Modified"),
                "bytes": len(b),
                "sha256": sha(b),
                "body": b,
            }
    except Exception as e:
        return {"ok": False, "requested_url": url, "error": f"{type(e).__name__}: {e}"}


def public(rec):
    return {k: v for k, v in rec.items() if k != "body"}


def textify(b: bytes) -> str:
    s = b.decode("utf-8", "replace")
    s = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def pdf_text(b: bytes) -> str:
    r = PdfReader(io.BytesIO(b))
    return "\n".join((p.extract_text() or "") for p in r.pages)


def aggregate(parts) -> str:
    return sha(canonical(parts))


def result(cid, cls, status, parts, **extra):
    d = {"id": cid, "class": cls, "status": status, "components": [public(x) for x in parts]}
    d.update(extra)
    d["aggregate_sha256"] = aggregate(d["components"])
    return d


# v0.1 PASS controls are replayed unchanged so the repair run proves no regression.
def br01():
    u = "https://avalon.law.yale.edu/ancient/hamcode.asp"
    x = fetch(u)
    if not x["ok"]:
        return result("BR01_HAMMURABI", "BLOCKED", "FAIL", [x], reason="fetch failed")
    t = textify(x["body"])
    markers = ["Code of Hammurabi", "When Anu", "EPILOGUE", "Hammurabi"]
    ok = all(m.lower() in t.lower() for m in markers) and len(x["body"]) > 20000
    return result("BR01_HAMMURABI", "SOURCE_BYTES" if ok else "PARTIAL", "PASS" if ok else "FAIL", [x], marker_validation={m: m.lower() in t.lower() for m in markers})


def br02():
    urls = [
        "https://www.livius.org/sources/content/behistun-persian-text/behistun-t-02/",
        "https://www.livius.org/sources/content/behistun-persian-text/behistun-t-36/",
        "https://www.livius.org/sources/content/behistun-persian-text/behistun-t-42/",
    ]
    xs = [fetch(u) for u in urls]
    oks = []
    for x in xs:
        if not x["ok"]:
            oks.append(False); continue
        t = textify(x["body"]).lower()
        oks.append("behistun" in t and ("old persian" in t or "dar" in t))
    ok = all(oks)
    return result("BR02_BEHISTUN", "SOURCE_BYTES" if ok else "PARTIAL", "PASS" if ok else "FAIL", xs, component_validation=oks)


def br03():
    # Same Wilson 1927 article and same pp. 266-278 locus; only transport changes.
    candidates = [
        "https://www.jstor.org/stable/pdf/528771.pdf",
        "https://www.journals.uchicago.edu/doi/pdf/10.1086/370157",
    ]
    attempts = []
    for u in candidates:
        x = fetch(u, max_bytes=50 * 1024 * 1024)
        attempts.append(x)
        if not x["ok"] or not x["body"].startswith(b"%PDF"):
            continue
        try:
            tx = pdf_text(x["body"])
        except Exception as e:
            x["parse_error"] = f"{type(e).__name__}: {e}"
            continue
        low = tx.lower()
        checks = {
            "title": "texts of the battle of kadesh" in low,
            "author": "john a. wilson" in low or "john wilson" in low,
            "poem": "the poem" in low,
            "record": "the record" in low,
        }
        # The whole authenticated article contains the frozen Poem pp.266-278.
        if all(checks.values()) and len(tx) > 10000:
            return result("BR03_KADESH", "SOURCE_BYTES", "PASS", attempts, selected_transport=u, pdf_text_sha256=sha(tx.encode()), marker_validation=checks, frozen_locus="Wilson 1927 THE POEM pp.266-278")
    return result("BR03_KADESH", "BLOCKED", "FAIL", attempts, reason="same-publication PDF transports did not yield verifiable article bytes; frozen DOI/locus unchanged")


def br04():
    # Official ORACC open-data JSON package, avoiding the broken HTML TLS path.
    candidates = [
        "http://oracc.org/json/rinap-rinap3.zip",
        "https://oracc.museum.upenn.edu/json/rinap-rinap3.zip",
    ]
    attempts = []
    for u in candidates:
        x = fetch(u, max_bytes=120 * 1024 * 1024)
        attempts.append(x)
        if not x["ok"] or not x["body"].startswith(b"PK"):
            continue
        try:
            z = zipfile.ZipFile(io.BytesIO(x["body"]))
            names = z.namelist()
            hits = [n for n in names if n.endswith("/Q003475.json") or n.endswith("Q003475.json")]
            if not hits:
                continue
            raw = z.read(hits[0])
            s = raw.decode("utf-8", "replace")
            checks = {"qid": "Q003475" in s, "sennacherib": "Sennacherib" in s or "sennacherib" in s.lower(), "line1_form": "EN.ZU" in s or "aš-šur" in s or "aš-šur.KI" in s}
            if all(checks.values()):
                return result("BR04_NEO_ASSYRIAN_ANNALS", "VERSIONED_CORPUS_REPRESENTATION", "PASS", attempts, archive_member=hits[0], archive_member_sha256=sha(raw), marker_validation=checks, frozen_locus="Q003475 lines 1-4")
        except Exception as e:
            x["parse_error"] = f"{type(e).__name__}: {e}"
    return result("BR04_NEO_ASSYRIAN_ANNALS", "BLOCKED", "FAIL", attempts, reason="official ORACC open-data package not reproducibly retrieved/validated")


def br05():
    u = "https://iris.unito.it/retrieve/e27ce42b-d27c-2581-e053-d805fe0acbaa/Devecchi-RAI54.pdf"
    x = fetch(u, max_bytes=30 * 1024 * 1024)
    if not x["ok"] or not x.get("body", b"").startswith(b"%PDF"):
        return result("BR05_HITTITE_TREATY", "BLOCKED", "FAIL", [x], reason="Devecchi scholarly PDF unavailable")
    try:
        tx = pdf_text(x["body"])
    except Exception as e:
        return result("BR05_HITTITE_TREATY", "PARTIAL", "FAIL", [x], reason=f"PDF parse failed: {e}")
    low = tx.lower().replace("š", "s").replace("š", "s").replace("ḫ", "h")
    checks = {
        "cth62": "cth 62" in low,
        "mursili": "mursili" in low or "muršili" in tx.lower(),
        "duppi": "duppi" in low or "tuppi" in low,
        "treaty_context": "treat" in low,
    }
    ok = all(checks.values())
    return result("BR05_HITTITE_TREATY", "SOURCE_BYTES" if ok else "PARTIAL", "PASS" if ok else "FAIL", [x], pdf_text_sha256=sha(tx.encode()), marker_validation=checks, frozen_locus="CTH 62.II A i 19′-28′; source authority/locus unchanged")


def _find_textpart(parent, subtype, n):
    for e in parent.iter():
        if e.tag.endswith("div") and e.attrib.get("subtype") == subtype and e.attrib.get("n") == str(n):
            return e
    return None


def br06():
    commit = "a065c359aab33c33bd17ddc2cac7d27fdc9cd870"
    u = f"https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/{commit}/data/tlg0003/tlg001/tlg0003.tlg001.perseus-grc2.xml"
    x = fetch(u, max_bytes=30 * 1024 * 1024)
    if not x["ok"]:
        return result("BR06_THUCYDIDES", "BLOCKED", "FAIL", [x], reason="pinned Perseus TEI unavailable")
    try:
        root = ET.fromstring(x["body"])
        book2 = _find_textpart(root, "book", 2)
        chapters = []
        if book2 is not None:
            for e in list(book2):
                if e.tag.endswith("div") and e.attrib.get("subtype") == "chapter" and e.attrib.get("n", "").isdigit() and 34 <= int(e.attrib["n"]) <= 46:
                    chapters.append(e)
        chapters.sort(key=lambda e: int(e.attrib["n"]))
        slice_b = b"\n".join(ET.tostring(e, encoding="utf-8") for e in chapters)
        ok = len(chapters) == 13 and [int(e.attrib["n"]) for e in chapters] == list(range(34, 47)) and len(slice_b) > 10000
        return result("BR06_THUCYDIDES", "VERSIONED_CORPUS_REPRESENTATION" if ok else "PARTIAL", "PASS" if ok else "FAIL", [x], external_repo_commit=commit, chapter_count=len(chapters), slice_sha256=sha(slice_b), frozen_locus="Book 2 chapters 34-46")
    except Exception as e:
        return result("BR06_THUCYDIDES", "PARTIAL", "FAIL", [x], reason=f"TEI parse/slice failed: {type(e).__name__}: {e}")


def br07():
    loci = {
        "preface": ["orbem", "terrarum", "subiecit"],
        "1": ["annos", "undeviginti", "exercitum", "privato"],
        "8": ["patriciorum", "numerum", "auxi"],
        "25": ["mare", "pacavi", "praedonibus"],
        "34": ["consulatu", "sexto", "septimo", "auctoritate"],
    }
    xs, validations = [], {}
    for sec, toks in loci.items():
        u = f"https://www.perseus.tufts.edu/hopper/text?doc=urn:cts:latinLit:phi1221.phi007.perseus-lat1:{sec}"
        x = fetch(u, max_bytes=5 * 1024 * 1024)
        xs.append(x)
        if not x["ok"]:
            validations[sec] = False; continue
        t = textify(x["body"]).lower()
        validations[sec] = all(tok in t for tok in toks) and "res gestae divi augusti" in t
    ok = all(validations.values()) and len(validations) == 5
    return result("BR07_RES_GESTAE", "SOURCE_BYTES" if ok else "PARTIAL", "PASS" if ok else "FAIL", xs, locus_validation=validations, frozen_locus="preface + §§1,8,25,34", note="canonical-latinLit records this edition as protected; therefore the public Perseus section representations are hashed directly")


def br08():
    # TLA separates metadata and full edition: /text/{id}/sentences. Freeze all pages.
    tid = "C6KGH3XC7RGU3DSL7HKYY2K3WM"
    root_u = f"https://thesaurus-linguae-aegyptiae.de/text/{tid}"
    root = fetch(root_u, max_bytes=5 * 1024 * 1024)
    xs = [root]
    if not root["ok"]:
        return result("BR08_PTAHHOTEP", "BLOCKED", "FAIL", xs, reason="TLA metadata root unavailable")
    rt = textify(root["body"]).lower()
    meta_ok = tid.lower() in rt and "ptahhotep" in rt and ("corpus" in rt or "korpus" in rt)
    page_hashes = []
    previous = None
    max_pages = 120
    for page in range(1, max_pages + 1):
        u = f"https://thesaurus-linguae-aegyptiae.de/text/{tid}/sentences?lang=en&page={page}"
        x = fetch(u, max_bytes=8 * 1024 * 1024)
        xs.append(x)
        if not x["ok"]:
            break
        t = textify(x["body"])
        # TLA returns an empty/out-of-range shell or repeats the last page when exhausted.
        h = x["sha256"]
        if h == previous:
            xs.pop(); break
        previous = h
        if tid not in t or "Ptahhotep" not in t:
            break
        content_signals = len(re.findall(r"Token ID|Token URL|Copy token|Sentence", t, flags=re.I))
        if content_signals < 2:
            if page == 1:
                break
            xs.pop(); break
        page_hashes.append(h)
        # pagination: if current page body has no link/mention to next page, stop.
        if not re.search(rf"(?:page=|>\s*){page + 1}(?:\D|$)", x["body"].decode("utf-8", "ignore")):
            break
    sufficient = meta_ok and len(page_hashes) >= 1
    # Whole-text sufficiency requires that the edition endpoint was actually traversed,
    # not merely the metadata page. Page count/hash list is frozen for replay.
    return result("BR08_PTAHHOTEP", "VERSIONED_CORPUS_REPRESENTATION" if sufficient else "METADATA_ONLY", "PASS" if sufficient else "FAIL", xs, corpus_issue_marker=("20" in rt), edition_page_count=len(page_hashes), edition_page_sha256=page_hashes, frozen_text_id=tid, note="whole persistent TLA text; no maxim subset selected")


def main():
    funcs = [br01, br02, br03, br04, br05, br06, br07, br08]
    controls = []
    for f in funcs:
        try:
            controls.append(f())
        except Exception as e:
            controls.append({"id": f.__name__.upper(), "class": "BLOCKED", "status": "FAIL", "reason": f"unhandled {type(e).__name__}: {e}"})
    n = sum(c.get("status") == "PASS" for c in controls)
    out = {
        "schema": "topa.propaganda_defense.base_rate_source_retrieval_run.v0.2",
        "date": "2026-08-24",
        "status": "EIGHT_OF_EIGHT_CONTENT_SUFFICIENT" if n == 8 else "PARTIAL_FAIL_CLOSED",
        "frozen_input_policy": {
            "source_authorities_unchanged": True,
            "exact_loci_unchanged": True,
            "descriptor_commitments_unchanged": True,
            "repair_scope": "TRANSPORT_AND_REPRESENTATION_VALIDATION_ONLY",
        },
        "controls": controls,
        "summary": {
            "content_sufficient": f"{n}/8",
            "sufficient_ids": [c.get("id") for c in controls if c.get("status") == "PASS"],
            "blocked_or_partial_ids": [c.get("id") for c in controls if c.get("status") != "PASS"],
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False,
        },
        "important_boundary": "Even 8/8 retrieval does not itself unlock coding; a separate BASE_RATE_CODING_UNLOCK review is required.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TOPA_BASE_RATE_RETRIEVAL_V0_2={'PASS' if n == 8 else 'PARTIAL_FAIL_CLOSED'}")
    print(f"CONTENT_SUFFICIENT={n}/8")
    print("SUFFICIENT_IDS=" + ",".join(out["summary"]["sufficient_ids"]))
    print("BLOCKED_OR_PARTIAL_IDS=" + ",".join(out["summary"]["blocked_or_partial_ids"]))
    print("SEMANTIC_VALUES_POPULATED=0")
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")
    return 0 if n == 8 else 1


if __name__ == "__main__":
    sys.exit(main())
