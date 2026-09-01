#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

TRACKS = [
    {
        "label": "Dream Version",
        "page": "https://robertmiles.bandcamp.com/track/children-dream-version",
    },
    {
        "label": "Original Version",
        "page": "https://robertmiles.bandcamp.com/track/children-original-version",
    },
]

UA = "Mozilla/5.0 (compatible; JANUS-TOPA-hash-audit/1.0; +https://github.com/Hawkar-usls/TOPA)"


def get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def find_tralbum(page_bytes: bytes):
    text = page_bytes.decode("utf-8", errors="replace")
    candidates = []
    for pat in [r'data-tralbum="([^"]+)"', r'data-blob="([^"]+)"']:
        for m in re.finditer(pat, text):
            raw = html.unescape(m.group(1))
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            if isinstance(obj, dict) and "trackinfo" in obj:
                candidates.append(obj)
    if not candidates:
        # Last-resort extraction around a JSON object containing trackinfo.
        idx = text.find('"trackinfo"')
        if idx >= 0:
            start = text.rfind("{", 0, idx)
            for end in range(text.find("}", idx), min(len(text), idx + 200000)):
                if text[end] != "}":
                    continue
                try:
                    obj = json.loads(text[start:end+1])
                    if isinstance(obj, dict) and "trackinfo" in obj:
                        candidates.append(obj)
                        break
                except Exception:
                    pass
    if not candidates:
        raise RuntimeError("Could not locate Bandcamp trackinfo JSON")
    return max(candidates, key=lambda o: len(o.get("trackinfo") or []))


def choose_stream(tralbum, expected_label: str):
    tracks = tralbum.get("trackinfo") or []
    chosen = None
    for t in tracks:
        title = (t.get("title") or "").lower()
        if "children" in title and expected_label.lower().replace(" version", "") in title:
            chosen = t
            break
    if chosen is None and len(tracks) == 1:
        chosen = tracks[0]
    if chosen is None:
        # Track pages often flag the active item with track_num/current.
        for t in tracks:
            if "children" in (t.get("title") or "").lower():
                chosen = t
                break
    if chosen is None:
        raise RuntimeError(f"Could not choose track for {expected_label}: {[t.get('title') for t in tracks]}")
    files = chosen.get("file") or {}
    stream = files.get("mp3-128") or files.get("mp3-v0") or next(iter(files.values()), None)
    if not stream:
        raise RuntimeError(f"No public stream URL in Bandcamp trackinfo for {expected_label}")
    return chosen, stream


def sha256_file(path: Path):
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def download_to(url: str, path: Path):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "audio/mpeg,*/*"})
    h = hashlib.sha256()
    n = 0
    with urllib.request.urlopen(req, timeout=120) as r, path.open("wb") as f:
        content_type = r.headers.get("Content-Type")
        etag = r.headers.get("ETag")
        last_modified = r.headers.get("Last-Modified")
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
            n += len(chunk)
    return {
        "sha256": h.hexdigest(),
        "bytes": n,
        "content_type": content_type,
        "etag": etag,
        "last_modified": last_modified,
    }


def pcm_hash(input_path: Path):
    # Decode the public stream deterministically to 44.1 kHz stereo signed-16 PCM.
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(input_path),
        "-map_metadata", "-1", "-ac", "2", "-ar", "44100",
        "-f", "s16le", "pipe:1"
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    h = hashlib.sha256()
    n = 0
    while True:
        chunk = p.stdout.read(1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
        n += len(chunk)
    stderr = p.stderr.read().decode("utf-8", errors="replace")
    rc = p.wait()
    if rc != 0:
        return {"status": "UNAVAILABLE", "error": stderr[-1000:]}
    return {
        "status": "PASS",
        "format": "s16le_stereo_44100",
        "sha256": h.hexdigest(),
        "bytes": n,
    }


def compare_hashes(a: str, b: str):
    ba = bytes.fromhex(a)
    bb = bytes.fromhex(b)
    xor = bytes(x ^ y for x, y in zip(ba, bb))
    hamming = sum(byte.bit_count() for byte in xor)
    same_hex_positions = sum(x == y for x, y in zip(a, b))
    prefix = 0
    for x, y in zip(a, b):
        if x != y:
            break
        prefix += 1
    suffix = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        suffix += 1
    return {
        "bit_hamming_distance": hamming,
        "bit_hamming_fraction": hamming / 256.0,
        "same_hex_nibble_positions": same_hex_positions,
        "same_hex_nibble_fraction": same_hex_positions / 64.0,
        "common_prefix_hex_chars": prefix,
        "common_suffix_hex_chars": suffix,
        "xor_hex": xor.hex(),
        "expected_for_unrelated_sha256": "~128 differing bits; ~4 same hex positions on average",
        "interpretation_rule": "SHA256_AVALANCHE_MEANS_AUDIO_SIMILARITY_IS_NOT_EXPECTED_TO_CREATE_VISIBLE_HASH_SIMILARITY",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for i, spec in enumerate(TRACKS):
            page_bytes = get_bytes(spec["page"])
            page_sha = hashlib.sha256(page_bytes).hexdigest()
            tralbum = find_tralbum(page_bytes)
            track, stream_url = choose_stream(tralbum, spec["label"])
            audio_path = td / f"track-{i}.mp3"
            stream_meta = download_to(stream_url, audio_path)
            pcm = pcm_hash(audio_path)
            rows.append({
                "label": spec["label"],
                "source_page": spec["page"],
                "source_page_sha256": page_sha,
                "bandcamp_track_title": track.get("title"),
                "bandcamp_track_id": track.get("track_id") or track.get("id"),
                "duration_seconds_reported": track.get("duration"),
                "public_stream_format": "mp3-128" if (track.get("file") or {}).get("mp3-128") else "fallback_public_stream",
                "public_stream_host": urlparse(stream_url).hostname,
                "public_stream": stream_meta,
                "decoded_pcm": pcm,
            })

    mp3_cmp = compare_hashes(rows[0]["public_stream"]["sha256"], rows[1]["public_stream"]["sha256"])
    pcm_cmp = None
    if rows[0]["decoded_pcm"].get("status") == "PASS" and rows[1]["decoded_pcm"].get("status") == "PASS":
        pcm_cmp = compare_hashes(rows[0]["decoded_pcm"]["sha256"], rows[1]["decoded_pcm"]["sha256"])

    result = {
        "schema": "topa.music.sha256_two_version_audit.v1",
        "status": "PASS",
        "subject": "Robert Miles — Children",
        "versions": rows,
        "comparisons": {
            "public_bandcamp_stream_bytes": mp3_cmp,
            "decoded_pcm_s16le_stereo_44100": pcm_cmp,
        },
        "hash_scope_warning": [
            "THESE_SHA256_VALUES_IDENTIFY_THE_EXACT_PUBLIC_BANDCAMP_STREAM_BYTES_RETRIEVED_IN_THIS_RUN, NOT AN ABSTRACT SONG.",
            "A DIFFERENT MASTER, CONTAINER, TAG, ENCODER, BITRATE OR DOWNLOAD FORMAT WILL HAVE A DIFFERENT SHA256 EVEN IF IT SOUNDS THE SAME.",
            "THE PCM HASH REMOVES MP3 CONTAINER/ENCODER BYTES BUT STILL IDENTIFIES THE EXACT DECODED SAMPLE SEQUENCE AND WILL CHANGE WITH MASTERING, TRIM OR RESAMPLING.",
            "VISIBLE_PATTERNS_IN_SHA256_HEX_DO_NOT_ENCODE MUSICAL SIMILARITY; SHA256 IS DESIGNED FOR AVALANCHE BEHAVIOR."
        ],
        "canonical_seal": "HASH THE EXACT WITNESS, THEN NAME THE WITNESS. SHA256 IS AN IDENTITY CHECK FOR BYTES, NOT A MUSICAL FINGERPRINT."
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
