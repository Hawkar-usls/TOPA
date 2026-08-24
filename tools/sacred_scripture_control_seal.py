#!/usr/bin/env python3
"""Fail-closed source/slice sealer for TOPA Sacred Scriptures matched controls.

Reads the pre-scoring control freeze, downloads the exact public source bytes,
extracts only the preregistered visible-text locus, and stores hashes/provenance.
It never computes research feature scores and never mirrors source text to repo.
"""
from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import re
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "TOPA-control-seal/0.1 (+https://github.com/Hawkar-usls/TOPA)"
EXPECTED_SLOTS = [f"C{i:02d}" for i in range(1, 9)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, timeout: int = 120) -> tuple[bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        content_type = r.headers.get("Content-Type")
    if not raw:
        raise RuntimeError(f"empty response: {url}")
    return raw, content_type


class VisibleTextParser(html.parser.HTMLParser):
    BLOCK = {
        "address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt",
        "figcaption", "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6",
        "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
        "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return
        if not self.skip_depth and tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            if self.skip_depth:
                self.skip_depth -= 1
            return
        if not self.skip_depth and tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def canonical_flow(s: str) -> str:
    s = unicodedata.normalize("NFC", s.replace("\r\n", "\n").replace("\r", "\n"))
    # A flow-normalized visible-text substrate avoids dependence on HTML tag layout
    # while preserving every visible token and punctuation mark in order.
    return re.sub(r"\s+", " ", s).strip()


def visible_from_html(raw: bytes) -> str:
    # Gutenberg pages declare multiple historical encodings. HTMLParser works on
    # Unicode, so try declared/common encodings without silently dropping bytes.
    decoded = None
    for enc in ("utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"):
        try:
            decoded = raw.decode(enc, errors="strict")
            break
        except UnicodeDecodeError:
            continue
    if decoded is None:
        raise RuntimeError("source HTML could not be decoded losslessly with allowed encodings")
    p = VisibleTextParser()
    p.feed(decoded)
    p.close()
    return canonical_flow(p.text())


def extract_slice(flow: str, start_marker: str, end_marker: str) -> tuple[bytes, dict]:
    start = canonical_flow(start_marker)
    end = canonical_flow(end_marker)
    hits_start = [m.start() for m in re.finditer(re.escape(start), flow)]
    if not hits_start:
        raise RuntimeError(f"start marker not found: {start[:120]}")
    # Prefer a start whose subsequent end marker exists; this handles repeated
    # table-of-contents headings without adding analyst discretion.
    chosen = None
    end_pos = None
    for pos in hits_start:
        ep = flow.find(end, pos + len(start))
        if ep >= 0:
            chosen, end_pos = pos, ep
            break
    if chosen is None or end_pos is None:
        raise RuntimeError(f"end marker not found after any start: {end[:120]}")
    if end_pos <= chosen:
        raise RuntimeError("invalid locus ordering")
    locus = flow[chosen:end_pos].strip()
    if len(locus) < 80:
        raise RuntimeError(f"implausibly short visible-text locus: {len(locus)} chars")
    b = (unicodedata.normalize("NFC", locus) + "\n").encode("utf-8")
    return b, {
        "start_occurrences_in_source": len(hits_start),
        "selected_start_offset_flow_chars": chosen,
        "selected_end_offset_flow_chars": end_pos,
        "canonical_start_marker": start,
        "canonical_end_marker": end,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", default="research/sacred-scriptures/CONTROL_CANDIDATE_FREEZE.v0.1.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    freeze_path = Path(args.freeze)
    freeze_raw = freeze_path.read_bytes()
    freeze = json.loads(freeze_raw.decode("utf-8"))
    controls = freeze.get("controls", [])
    slots = [x.get("slot") for x in controls]
    if slots != EXPECTED_SLOTS:
        raise SystemExit(f"control freeze slot/order mismatch: {slots!r}")

    sealed: list[dict] = []
    errors: list[dict] = []
    for c in controls:
        slot = c["slot"]
        try:
            raw, content_type = fetch(c["source_url"])
            # Reject obvious non-HTML transport substitutions.
            head = raw[:4096].lower()
            if b"<html" not in head and b"<!doctype html" not in head:
                raise RuntimeError("download did not look like HTML")
            flow = visible_from_html(raw)
            locus_bytes, extraction = extract_slice(flow, c["start_marker"], c["end_marker"])
            receipt = {k: v for k, v in c.items() if k not in {"start_marker", "end_marker"}}
            receipt.update({
                "source_download_bytes": len(raw),
                "source_sha256": sha256(raw),
                "source_content_type": content_type,
                "slice_bytes": len(locus_bytes),
                "slice_sha256": sha256(locus_bytes),
                "slice_seal_type": "NFC_UTF8_FLOW_NORMALIZED_VISIBLE_TEXT_SHA256",
                "normalization": "HTML visible text only; script/style/noscript removed; NFC; all Unicode whitespace collapsed to one ASCII space; final LF",
                "extraction_receipt": extraction,
                "status": "SEALED",
            })
            sealed.append(receipt)
            print(f"CONTROL_SEAL_{slot}=PASS")
        except Exception as exc:
            errors.append({"slot": slot, "error": f"{type(exc).__name__}: {exc}"})
            print(f"CONTROL_SEAL_{slot}=FAIL: {exc}")

    by_slot = {x["slot"]: x for x in sealed}
    ok = all(s in by_slot for s in EXPECTED_SLOTS) and not errors
    out = {
        "schema": "topa.sacred_scriptures.control_seal_run.v0.1",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EIGHT_OF_EIGHT_REAL_CONTROLS_SEALED" if ok else "CONTROL_SEAL_FAILURE",
        "control_freeze_path": str(freeze_path),
        "control_freeze_sha256": sha256(freeze_raw),
        "required_slots": EXPECTED_SLOTS,
        "controls": [by_slot[s] for s in EXPECTED_SLOTS if s in by_slot],
        "sealed_count": len(by_slot),
        "required_count": 8,
        "errors": errors,
        "rights_policy": "Receipts store source identity, rights state and hashes only; downloaded source texts are not mirrored by this artifact.",
        "double_coding_permission_from_real_controls": ok,
        "score_permission": False,
        "epistemic_effect": "CONTROL_PROVENANCE_AND_IMMUTABILITY_ONLY_NO_RESEARCH_RESULT_CREDIT",
    }
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TOPA_REAL_CONTROLS={'PASS' if ok else 'FAIL'}")
    print(f"CONTROL_SEAL_COUNT={len(by_slot)}/8")
    print(f"RECEIPT={p}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
