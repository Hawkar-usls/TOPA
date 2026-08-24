#!/usr/bin/env python3
"""Networked source-seal runner for TOPA Flood calibration.

Run in CI. It stores hashes/receipts, not mirrored source texts.
For machine-readable sources it also hashes the exact frozen text slice.
For the Akkadian critical-edition PDF it hashes immutable PDF bytes and binds
each frozen line-locus descriptor into a distinct slice seal.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "TOPA-source-seal/0.1 (+https://github.com/Hawkar-usls/TOPA)"
WASSERMAN_URL = "https://www.peeters-leuven.be/download_OA.php?id=9789042941748&name=The+Flood%3A+The+Akkadian+Sources"
TANZIL_URL = ("https://tanzil.net/pub/download/index.php?"
              "quranType=uthmani&outType=txt-2&agree=true&marks=true&"
              "sajdah=true&rub=true&stanween=true")
GRETIL_URL = "https://gretil.sub.uni-goettingen.de/gretil/1_sanskr/1_veda/2_bra/satapath/sb_01_u.htm"
BHSA_FULL_SHA = "b112c161cfd21eae403d51a2733740d8743460e7"
BHSA_RAW_BASE = f"https://raw.githubusercontent.com/ETCBC/bhsa/{BHSA_FULL_SHA}/tf/2021"
BHSA_CORE_FILES = ["otype.tf", "oslots.tf", "otext.tf", "book.tf", "chapter.tf", "verse.tf"]

def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def fetch(url: str, timeout=90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if not data:
        raise RuntimeError(f"empty response: {url}")
    return data

def binding(source_sha: str, locus: str) -> str:
    payload = b"TOPA-SLICE-BINDING-V1\0" + source_sha.encode() + b"\0" + locus.encode("utf-8")
    return h(payload)

def nfc_lf(s: str) -> bytes:
    s = unicodedata.normalize("NFC", s.replace("\r\n", "\n").replace("\r", "\n"))
    return s.encode("utf-8")

def seal_akkadian():
    pdf = fetch(WASSERMAN_URL)
    if not pdf.startswith(b"%PDF"):
        raise RuntimeError("Wasserman source did not return a PDF")
    source_sha = h(pdf)
    source_bytes = len(pdf)
    shared = {
        "source": "Nathan Wasserman, The Flood: The Akkadian Sources, OBO 290 (2020)",
        "source_url": WASSERMAN_URL,
        "source_media_type": "application/pdf",
        "source_bytes": source_bytes,
        "source_sha256": source_sha,
        "seal_note": "Exact critical-edition line loci are cryptographically bound to the immutable full PDF hash; no PDF text extraction is treated as primary text.",
    }
    atr_locus = "Atra-hasis C1:i:20'-35'|C1:ii:52\"-55\"|C1:iii:5'-27'|C1:iv:24'-27'|C1:v:30\"-38\""
    gil_locus = "Gilgamesh Tablet XI:8-203|8-20|21-44|45-91|92-139|140-156|157-203"
    return [
        {"id":"F01_ATRAHASIS", **shared, "frozen_locus_descriptor":atr_locus,
         "slice_seal_type":"SOURCE_SHA256_PLUS_EXACT_LOCUS_BINDING",
         "slice_sha256":binding(source_sha, atr_locus), "content_slice_sha256":None,
         "content_slice_reason":"PDF critical edition retained as immutable source; exact line ranges remain the locus authority.",
         "status":"SEALED"},
        {"id":"F02_GILGAMESH_XI", **shared, "frozen_locus_descriptor":gil_locus,
         "slice_seal_type":"SOURCE_SHA256_PLUS_EXACT_LOCUS_BINDING",
         "slice_sha256":binding(source_sha, gil_locus), "content_slice_sha256":None,
         "content_slice_reason":"PDF critical edition retained as immutable source; exact line ranges remain the locus authority.",
         "status":"SEALED"},
    ]

def bhsa_required_files_from_otext(otext_bytes: bytes):
    """Derive exact feature dependencies declared by frozen otext.tf formats."""
    text = otext_bytes.decode("utf-8")
    features = set()
    for expr in re.findall(r"\{([^}]+)\}", text):
        for feature in expr.split("/"):
            feature = feature.strip()
            if feature:
                features.add(f"{feature}.tf")
    return sorted(set(BHSA_CORE_FILES) | features)

def prepare_bhsa_tf(bhsa_dir: Path | None):
    """Return exact BHSA 2021 TF directory, transport metadata and fetched files.

    CI fetches only exact files at the full frozen commit. Feature dependencies
    are derived from that commit's own otext.tf so Text-Fabric cannot silently
    depend on an unsealed auxiliary feature.
    """
    if bhsa_dir is not None:
        import subprocess
        root = bhsa_dir.resolve()
        if not root.exists():
            raise RuntimeError(f"BHSA checkout missing: {root}")
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        if head != BHSA_FULL_SHA:
            raise RuntimeError(f"BHSA wrong commit: {head}")
        tfdir = (root / "tf" / "2021").resolve()
        files = bhsa_required_files_from_otext((tfdir / "otext.tf").read_bytes())
        return tfdir, "GIT_CHECKOUT_FULL_COMMIT", head, files

    tfdir = Path(".source-cache/bhsa-raw/tf/2021").resolve()
    tfdir.mkdir(parents=True, exist_ok=True)

    # Bootstrap from immutable otext.tf, then derive every format dependency.
    bootstrap = {}
    for name in BHSA_CORE_FILES:
        data = fetch(f"{BHSA_RAW_BASE}/{name}")
        bootstrap[name] = data
        (tfdir / name).write_bytes(data)
    files = bhsa_required_files_from_otext(bootstrap["otext.tf"])
    for name in files:
        if name in bootstrap:
            continue
        data = fetch(f"{BHSA_RAW_BASE}/{name}")
        (tfdir / name).write_bytes(data)
    return tfdir, "RAW_GITHUB_FULL_COMMIT_FILES_OTEXT_DERIVED", BHSA_FULL_SHA, files

def seal_bhsa(bhsa_dir: Path | None):
    tfdir, transport, head, files = prepare_bhsa_tf(bhsa_dir)
    manifest = []
    for name in files:
        p = tfdir / name
        b = p.read_bytes()
        manifest.append({
            "path": f"tf/2021/{name}",
            "bytes": len(b),
            "sha256": h(b),
            "immutable_url": f"{BHSA_RAW_BASE}/{name}"
        })
    manifest_raw = "\n".join(f"{x['path']}\0{x['sha256']}" for x in manifest).encode()
    substrate_sha = h(manifest_raw)

    from tf.fabric import Fabric
    TF = Fabric(locations=str(tfdir), silent="deep")
    TF.load("g_word_utf8 trailer_utf8", silent="deep")
    api = getattr(TF, "api", None)
    if api is None:
        raise RuntimeError("Text-Fabric failed to load exact BHSA 2021 feature set")
    F, L, T = api.F, api.L, api.T
    if not hasattr(F, "g_word_utf8") or not hasattr(F, "trailer_utf8"):
        raise RuntimeError("BHSA word/trailer features unavailable after exact-file load")

    ranges = {6:(5,22), 7:(1,24), 8:(1,22), 9:(1,17)}
    rows = []
    for chapter, (v0, v1) in ranges.items():
        for verse in range(v0, v1 + 1):
            node = T.nodeFromSection(("Genesis", chapter, verse))
            if node is None:
                raise RuntimeError(f"BHSA missing Genesis {chapter}:{verse}")
            words = L.d(node, otype="word")
            text = "".join((F.g_word_utf8.v(w) or "") + (F.trailer_utf8.v(w) or "") for w in words).strip()
            rows.append(f"{chapter}:{verse}\t{text}")
    slice_bytes = nfc_lf("\n".join(rows) + "\n")
    return {
        "id":"F03_GENESIS_6_9", "source":"ETCBC BHSA Text-Fabric 2021",
        "source_repository":"ETCBC/bhsa", "source_commit":head,
        "source_transport":transport,
        "source_dependency_policy":"All Text-Fabric format dependencies are derived from frozen otext.tf and individually SHA-256 sealed.",
        "source_substrate_manifest":manifest, "source_substrate_sha256":substrate_sha,
        "frozen_locus_descriptor":"Genesis 6:5-9:17",
        "slice_seal_type":"NFC_UTF8_TEXT_SLICE_SHA256", "slice_bytes":len(slice_bytes),
        "slice_sha256":h(slice_bytes), "verse_count":len(rows),
        "normalization":"NFC; LF; each row chapter:verse<TAB>g_word_utf8+trailer_utf8",
        "status":"SEALED"}

def seal_tanzil():
    raw = fetch(TANZIL_URL)
    text = raw.decode("utf-8-sig")
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\s*11\|(\d+)\|(.*)$", line)
        if m and 25 <= int(m.group(1)) <= 49:
            rows.append((int(m.group(1)), m.group(2)))
    if len(rows) != 25 or [x[0] for x in rows] != list(range(25,50)):
        raise RuntimeError(f"Tanzil Q11:25-49 parse failed; got {len(rows)} verses")
    canonical = nfc_lf("\n".join(f"11|{a}|{t}" for a,t in rows) + "\n")
    return {
        "id":"F04_QURAN_NOAH", "source":"Tanzil Uthmani Quran Text v1.1",
        "source_url":TANZIL_URL,
        "export_options":{"quranType":"uthmani","outType":"txt-2","marks":True,"sajdah":True,"rub":True,"stanween":True,"tatweel_below_superscript_alef":False},
        "source_download_bytes":len(raw), "source_download_sha256":h(raw),
        "frozen_locus_descriptor":"Q 11:25-49",
        "slice_seal_type":"NFC_UTF8_VERBATIM_VERSE_ROWS_SHA256", "slice_bytes":len(canonical),
        "slice_sha256":h(canonical), "verse_count":25,
        "normalization":"NFC only for hashing; verbatim verse characters otherwise preserved; LF rows",
        "status":"SEALED"}

def seal_gretil():
    raw = fetch(GRETIL_URL)
    text = raw.decode("utf-8", errors="strict")
    import html
    plain = html.unescape(re.sub(r"<[^>]+>", "", text))
    start_marker = "1.8.1.[1]"
    end_marker = "1.8.1.[11]"
    start = plain.find(start_marker)
    end = plain.find(end_marker, start + len(start_marker)) if start >= 0 else -1
    if start < 0 or end <= start:
        raise RuntimeError("GRETIL ŚB 1.8.1.[1]-[10] visible-text markers not found")
    slice_bytes = nfc_lf(plain[start:end].strip() + "\n")
    return {
        "id":"F05_SATAPATHA_MANU", "source":"GRETIL Satapatha-Brahmana, Madhyamdina, Book 1",
        "source_url":GRETIL_URL, "source_download_bytes":len(raw), "source_download_sha256":h(raw),
        "frozen_locus_descriptor":"Śatapatha-Brāhmaṇa 1.8.1.[1]-[10]",
        "slice_seal_type":"NFC_UTF8_VISIBLE_TEXT_SHA256", "slice_bytes":len(slice_bytes),
        "slice_sha256":h(slice_bytes),
        "normalization":"HTML tags removed; entities unescaped; visible marker 1.8.1.[1] through before 1.8.1.[11]; NFC; LF",
        "source_note":"GRETIL itself contains a mechanically corrupted visible number for paragraph 3 (1.8.1[[.]]3); it is preserved verbatim inside the frozen slice rather than repaired.",
        "status":"SEALED"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bhsa-dir", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    bhsa_dir = Path(args.bhsa_dir) if args.bhsa_dir else None
    sources, errors = [], []
    for name, fn in [("AKKADIAN", seal_akkadian), ("BHSA", lambda:seal_bhsa(bhsa_dir)), ("TANZIL", seal_tanzil), ("GRETIL", seal_gretil)]:
        try:
            r = fn(); sources.extend(r if isinstance(r, list) else [r]); print(f"SOURCE_SEAL_{name}=PASS")
        except Exception as exc:
            errors.append({"stage":name,"error":f"{type(exc).__name__}: {exc}"}); print(f"SOURCE_SEAL_{name}=FAIL: {exc}")
    by_id = {s["id"]:s for s in sources}
    required = ["F01_ATRAHASIS","F02_GILGAMESH_XI","F03_GENESIS_6_9","F04_QURAN_NOAH","F05_SATAPATHA_MANU"]
    all_sealed = all(x in by_id and by_id[x].get("status")=="SEALED" for x in required) and not errors
    out = {
        "schema":"topa.sacred_scriptures.source_seal_run.v0.1",
        "executed_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"FIVE_OF_FIVE_SEALED" if all_sealed else "SOURCE_SEAL_FAILURE",
        "required_source_ids":required, "sources":[by_id[x] for x in required if x in by_id],
        "sealed_count":sum(x in by_id and by_id[x].get("status")=="SEALED" for x in required),
        "required_count":5, "errors":errors,
        "rights_policy":"Receipt stores hashes/provenance only; no source text is mirrored by this artifact.",
        "blind_packet_permission_from_sources":all_sealed, "score_permission":False}
    p=Path(args.out); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"TOPA_SOURCE_SEALS={'PASS' if all_sealed else 'FAIL'}")
    print(f"SOURCE_SEAL_COUNT={out['sealed_count']}/5")
    print(f"RECEIPT={p}")
    return 0 if all_sealed else 2

if __name__ == "__main__":
    raise SystemExit(main())
