#!/usr/bin/env python3
"""BR03 Kadesh HathiTrust bounded scan-sequence probe v0.5.

Diagnostic transport work only. The frozen Wilson 1927 locus is unchanged.
Operational boundary interpretation is explicit: Poem content occupies printed
pp.266-277; printed p.278 is retained only as the exclusion boundary because
THE RECORD begins there.

No source text is persisted. Only response hashes, lengths and marker booleans.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import re
import urllib.request
from pathlib import Path

OUT = Path("research/propaganda-defense/execution/KADESH_HATHI_SCAN_PROBE.v0.5.json")
HTID = "mdp.39015024059043"  # exact v.43 1926-1927 full-view candidate
SEQ_START = 260
SEQ_END = 305
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str, max_bytes=6 * 1024 * 1024):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            b = r.read(max_bytes + 1)
            truncated = len(b) > max_bytes
            if truncated:
                b = b[:max_bytes]
            return {
                "ok": True,
                "status": getattr(r, "status", 200),
                "final_url": r.geturl(),
                "content_type": r.headers.get("Content-Type"),
                "bytes": len(b),
                "sha256": sha(b),
                "truncated": truncated,
                "body": b,
            }
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def plain(b: bytes) -> str:
    s = b.decode("utf-8", "replace")
    s = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def probe_seq(seq: int):
    urls = {
        "html": f"https://babel.hathitrust.org/cgi/imgsrv/html?id={HTID};seq={seq}",
        "pt": f"https://babel.hathitrust.org/cgi/pt?id={HTID};seq={seq};view=1up",
    }
    rec = {"seq": seq, "representations": {}}
    combined = ""
    for name, url in urls.items():
        x = fetch(url)
        pub = {k: v for k, v in x.items() if k != "body"}
        text = plain(x.get("body", b"")) if x.get("ok") and "html" in (x.get("content_type") or "").lower() else ""
        pub["text_chars"] = len(text)
        pub["text_sha256"] = sha(text.encode()) if text else None
        rec["representations"][name] = pub
        combined += " " + text
    low = combined.lower()
    rec["markers"] = {
        "article_title": "texts of the battle of kadesh" in low,
        "john_wilson": "john a. wilson" in low or "john wilson" in low,
        "the_poem": "the poem" in low,
        "the_record": "the record" in low,
        "printed_266": bool(re.search(r"(?:^|\D)266(?:\D|$)", combined)),
        "printed_277": bool(re.search(r"(?:^|\D)277(?:\D|$)", combined)),
        "printed_278": bool(re.search(r"(?:^|\D)278(?:\D|$)", combined)),
    }
    return rec


def main():
    seqs = list(range(SEQ_START, SEQ_END + 1))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(probe_seq, seqs))
    rows.sort(key=lambda r: r["seq"])

    title_seqs = [r["seq"] for r in rows if r["markers"]["article_title"] or r["markers"]["john_wilson"]]
    poem_seqs = [r["seq"] for r in rows if r["markers"]["the_poem"]]
    record_seqs = [r["seq"] for r in rows if r["markers"]["the_record"]]
    p266_seqs = [r["seq"] for r in rows if r["markers"]["printed_266"]]
    p278_seqs = [r["seq"] for r in rows if r["markers"]["printed_278"]]
    html_ok = sum(1 for r in rows if r["representations"]["html"].get("ok"))
    pt_ok = sum(1 for r in rows if r["representations"]["pt"].get("ok"))

    candidates = []
    starts = sorted(set(title_seqs + p266_seqs))
    boundaries = sorted(set(record_seqs + p278_seqs))
    for start in starts:
        for boundary in boundaries:
            # Printed 266 -> printed 278 is a +12 scan-page delta if one scan per printed page.
            if boundary - start == 12:
                content_rows = [r for r in rows if start <= r["seq"] < boundary]
                boundary_row = next((r for r in rows if r["seq"] == boundary), None)
                all_content_retrieved = len(content_rows) == 12 and all(
                    r["representations"]["html"].get("ok") or r["representations"]["pt"].get("ok")
                    for r in content_rows
                )
                marker_support = any(r["markers"]["the_poem"] for r in content_rows)
                boundary_support = bool(boundary_row and boundary_row["markers"]["the_record"])
                candidates.append({
                    "start_seq": start,
                    "boundary_seq": boundary,
                    "content_seq_count": len(content_rows),
                    "all_content_retrieved": all_content_retrieved,
                    "poem_marker_inside_content": marker_support,
                    "record_marker_on_boundary": boundary_support,
                    "content_page_hashes": [
                        {
                            "seq": r["seq"],
                            "html_sha256": r["representations"]["html"].get("sha256"),
                            "pt_sha256": r["representations"]["pt"].get("sha256"),
                        }
                        for r in content_rows
                    ],
                    "boundary_hashes": {
                        "html_sha256": boundary_row["representations"]["html"].get("sha256") if boundary_row else None,
                        "pt_sha256": boundary_row["representations"]["pt"].get("sha256") if boundary_row else None,
                    }
                })

    sufficient = [c for c in candidates if c["all_content_retrieved"] and c["poem_marker_inside_content"] and c["record_marker_on_boundary"]]
    image_anchors = []
    if not sufficient:
        # Availability-only fallback for a few frozen-window anchors. No OCR and no admission.
        for seq in (266, 272, 278, 284, 290):
            u = f"https://babel.hathitrust.org/cgi/imgsrv/image?id={HTID};seq={seq};size=1200;rotation=0"
            x = fetch(u, max_bytes=12 * 1024 * 1024)
            image_anchors.append({"seq": seq, **{k: v for k, v in x.items() if k != "body"}, "image_magic": bool(x.get("ok") and (x.get("content_type") or "").lower().startswith("image/"))})

    out = {
        "schema": "topa.propaganda_defense.kadesh_hathi_scan_probe.v0.5",
        "date": "2026-08-24",
        "status": "DIAGNOSTIC_ONLY",
        "frozen": {
            "authority": "John A. Wilson, The Texts of the Battle of Kadesh, AJSL 43.4 (1927)",
            "doi": "10.1086/370157",
            "locus": "THE POEM, journal pp.266-278; Record excluded",
            "operational_boundary": "Poem content pp.266-277; p.278 retained only as THE RECORD exclusion boundary",
            "changed": False
        },
        "hathitrust": {
            "htid": HTID,
            "catalog_state": "v.43 1926-1927; Full view",
            "preregistered_seq_window": [SEQ_START, SEQ_END],
            "html_ok_count": html_ok,
            "pt_ok_count": pt_ok,
            "title_seqs": title_seqs,
            "poem_seqs": poem_seqs,
            "record_seqs": record_seqs,
            "printed_266_seqs": p266_seqs,
            "printed_278_seqs": p278_seqs,
            "candidate_boundaries": candidates,
            "sufficient_candidates": sufficient,
            "rows": rows,
            "image_availability_anchors_if_needed": image_anchors
        },
        "summary": {
            "content_sufficient": bool(sufficient),
            "semantic_values_populated": 0,
            "base_rate_coding_permission": False,
            "score_permission": False,
            "legal_next": "AUTHORITATIVE_RETRIEVAL_V0_3_REPLAY" if sufficient else "PRESERVE_PARTIAL_AND_LOCALIZE_NEXT_TRANSPORT_ONLY"
        },
        "laws": [
            "BOUNDARY_PAGE_IS_NOT_CONTENT_PAGE",
            "IMAGE_AVAILABILITY != OCR_CONTENT",
            "CATALOG_FULL_VIEW != RETRIEVED_LOCUS",
            "TRANSPORT_REPAIR != LOCUS_CHANGE",
            "NO_CODING_UNLOCK_FROM_DIAGNOSTIC"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_KADESH_HATHI_SCAN_PROBE_V0_5=COMPLETE")
    print(f"HATHI_HTML_OK={html_ok}/{len(rows)}")
    print(f"HATHI_PT_OK={pt_ok}/{len(rows)}")
    print("TITLE_SEQS=" + (",".join(map(str, title_seqs)) if title_seqs else "NONE"))
    print("POEM_SEQS=" + (",".join(map(str, poem_seqs)) if poem_seqs else "NONE"))
    print("RECORD_SEQS=" + (",".join(map(str, record_seqs)) if record_seqs else "NONE"))
    print("SUFFICIENT_CANDIDATES=" + str(len(sufficient)))
    print("BASE_RATE_CODING_PERMISSION=false")
    print("SCORE_PERMISSION=false")


if __name__ == "__main__":
    main()
