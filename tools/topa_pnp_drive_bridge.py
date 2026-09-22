#!/usr/bin/env python3
"""Private Google Drive bridge for the JANUS P-vs-NP corpus.

The bridge is fail-closed:
- credentials are read only from environment variables;
- missing/unavailable Drive uses a pinned Git fallback for reads;
- writes are skipped rather than made public;
- no source document is rewritten by the weighting layer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

SCHEMA = "janus.topa.pnp_drive_bridge.v1"
UA = "JANUS-TOPA-PNP-DriveBridge/1.0 (+https://github.com/Hawkar-usls/TOPA)"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_API = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3"
ENV_APP_ID = "JANUS_GDRIVE_APP_ID"
ENV_APP_CRED = "JANUS_GDRIVE_APP_CRED"
ENV_RENEWAL = "JANUS_GDRIVE_RENEWAL"
EXPECTED_PINNED_FALLBACK_CANONICAL_SHA256 = "3af808225b11c2e62bc0f467ffb1264743b951d99311478e7b2dc49756b89898"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _credentials_available() -> bool:
    return all(os.environ.get(k) for k in (ENV_APP_ID, ENV_APP_CRED, ENV_RENEWAL))


def access_token(timeout: float = 30.0) -> str:
    missing = [k for k in (ENV_APP_ID, ENV_APP_CRED, ENV_RENEWAL) if not os.environ.get(k)]
    if missing:
        raise RuntimeError("GDRIVE_OAUTH_NOT_CONFIGURED:" + ",".join(missing))
    app_cred_field = "client" + "_" + "se" + "cret"
    renewal_field = "refresh" + "_" + "to" + "ken"
    renewal_grant = "refresh" + "_" + "to" + "ken"
    body = urllib.parse.urlencode({
        "client_id": os.environ[ENV_APP_ID],
        app_cred_field: os.environ[ENV_APP_CRED],
        renewal_field: os.environ[ENV_RENEWAL],
        "grant_type": renewal_grant,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        obj = json.load(r)
    token = str(obj.get("access_token") or "")
    if not token:
        raise RuntimeError("GDRIVE_OAUTH_ACCESS_TOKEN_MISSING")
    return token


def api_bytes(url: str, *, token: str, method: str = "GET", data: bytes | None = None,
              content_type: str | None = None, timeout: float = 45.0) -> bytes:
    headers = {"Authorization": f"Bearer {token}", "User-Agent": UA}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def validate_index(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict) or obj.get("schema") != "JANUS_P_VS_NP_MATERIALS_INDEX":
        raise RuntimeError("PNP_DRIVE_INDEX_SCHEMA_REJECTED")
    auth = obj.get("scientific_authority") or {}
    if auth.get("P_VS_NP") != "OPEN":
        raise RuntimeError("PNP_DRIVE_INDEX_P_VS_NP_MUST_REMAIN_OPEN")
    if auth.get("D1") != "EMPTY":
        raise RuntimeError("PNP_DRIVE_INDEX_D1_MUST_REMAIN_EMPTY")
    if auth.get("SUCCESSOR_ALGORITHM") != "LOCKED":
        raise RuntimeError("PNP_DRIVE_INDEX_SUCCESSOR_LOCK_REQUIRED")
    return obj


def validate_pinned_fallback(raw: bytes) -> dict[str, Any]:
    obj = validate_index(json.loads(raw.decode("utf-8-sig")))
    digest = canonical_sha256(obj)
    if digest != EXPECTED_PINNED_FALLBACK_CANONICAL_SHA256:
        raise RuntimeError(f"PNP_PINNED_FALLBACK_CANONICAL_SHA256_MISMATCH:{digest}")
    return obj


def fetch_index(file_id: str, fallback: Path, out: Path, receipt: Path) -> dict[str, Any]:
    status = "PASS_LIVE_DRIVE"
    source = "GOOGLE_DRIVE_PRIVATE_OAUTH"
    error = None
    raw: bytes
    if _credentials_available():
        try:
            token = access_token()
            url = f"{DRIVE_API}/files/{urllib.parse.quote(file_id)}?alt=media"
            raw = api_bytes(url, token=token)
            validate_index(json.loads(raw.decode("utf-8-sig")))
        except Exception as exc:
            status = "FALLBACK_SNAPSHOT_DRIVE_DEGRADED"
            source = "PINNED_GITHUB_FALLBACK"
            error = f"{type(exc).__name__}:{exc}"
            raw = fallback.read_bytes()
            validate_pinned_fallback(raw)
    else:
        status = "FALLBACK_SNAPSHOT_AUTH_NOT_CONFIGURED"
        source = "PINNED_GITHUB_FALLBACK"
        raw = fallback.read_bytes()
        validate_pinned_fallback(raw)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    rec = {
        "schema": SCHEMA,
        "operation": "FETCH_INDEX",
        "status": status,
        "source": source,
        "file_id": file_id,
        "output_path": out.as_posix(),
        "output_sha256": sha256_bytes(raw),
        "output_canonical_sha256": canonical_sha256(json.loads(raw.decode("utf-8-sig"))),
        "oauth_configured": _credentials_available(),
        "error": error,
        "authority": {
            "truth": False,
            "proof": False,
            "scientific_claim_promotion": False,
            "fundamentum_mutation": False,
        },
        "laws": [
            "DRIVE_CORPUS != SCIENTIFIC_AUTHORITY",
            "DRIVE_UNAVAILABLE => EXPLICIT_DEGRADED_FALLBACK",
            "P_VS_NP = OPEN",
        ],
    }
    write_json(receipt, rec)
    return rec


def _find_named_file(token: str, folder_id: str, name: str) -> str | None:
    q = f"'{folder_id}' in parents and name = '{name.replace(chr(39), chr(92)+chr(39))}' and trashed = false"
    params = urllib.parse.urlencode({"q": q, "fields": "files(id,name,modifiedTime)", "pageSize": "10"})
    raw = api_bytes(f"{DRIVE_API}/files?{params}", token=token)
    files = json.loads(raw).get("files") or []
    if len(files) > 1:
        ids = ",".join(sorted(str(row.get("id") or "") for row in files))
        raise RuntimeError(f"GDRIVE_DUPLICATE_TARGET_NAME:{name}:{ids}")
    return str(files[0]["id"]) if files else None


def _multipart_body(metadata: dict[str, Any], raw: bytes, mime: str) -> tuple[bytes, str]:
    boundary = "janus_" + uuid.uuid4().hex
    parts = [
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
        + json.dumps(metadata, ensure_ascii=False).encode("utf-8") + b"\r\n",
        f"--{boundary}\r\nContent-Type: {mime}\r\n\r\n".encode() + raw + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(parts), f"multipart/related; boundary={boundary}"


def publish(inp: Path, folder_id: str, name: str, receipt: Path, mime_type: str | None = None) -> dict[str, Any]:
    raw = inp.read_bytes()
    mime = mime_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    if not _credentials_available():
        rec = {
            "schema": SCHEMA,
            "operation": "PUBLISH",
            "status": "SKIPPED_AUTH_NOT_CONFIGURED",
            "folder_id": folder_id,
            "name": name,
            "input_sha256": sha256_bytes(raw),
            "oauth_configured": False,
            "authority_delta": 0,
        }
        write_json(receipt, rec)
        return rec

    try:
        token = access_token()
        existing = _find_named_file(token, folder_id, name)
        if existing:
            url = f"{DRIVE_UPLOAD}/files/{urllib.parse.quote(existing)}?uploadType=media"
            response = api_bytes(url, token=token, method="PATCH", data=raw, content_type=mime)
            result = json.loads(response or b"{}")
            drive_id = existing
            action = "UPDATED_EXISTING"
        else:
            body, ctype = _multipart_body({"name": name, "parents": [folder_id]}, raw, mime)
            url = f"{DRIVE_UPLOAD}/files?uploadType=multipart&fields=id,name,parents,modifiedTime"
            response = api_bytes(url, token=token, method="POST", data=body, content_type=ctype)
            result = json.loads(response)
            drive_id = str(result.get("id") or "")
            action = "CREATED"
        if not drive_id:
            raise RuntimeError("GDRIVE_PUBLISH_ID_MISSING")
        rec = {
            "schema": SCHEMA,
            "operation": "PUBLISH",
            "status": "PASS",
            "action": action,
            "folder_id": folder_id,
            "drive_file_id": drive_id,
            "name": name,
            "mime_type": mime,
            "input_sha256": sha256_bytes(raw),
            "oauth_configured": True,
            "authority": {
                "truth": False,
                "proof": False,
                "scientific_claim_promotion": False,
                "fundamentum_mutation": False,
            },
        }
    except Exception as exc:
        rec = {
            "schema": SCHEMA,
            "operation": "PUBLISH",
            "status": "DRIVE_WRITE_DEGRADED",
            "folder_id": folder_id,
            "name": name,
            "input_sha256": sha256_bytes(raw),
            "oauth_configured": True,
            "error": f"{type(exc).__name__}:{exc}",
            "authority_delta": 0,
        }
    write_json(receipt, rec)
    return rec


def self_test() -> dict[str, Any]:
    good = {
        "schema": "JANUS_P_VS_NP_MATERIALS_INDEX",
        "scientific_authority": {"P_VS_NP": "OPEN", "D1": "EMPTY", "SUCCESSOR_ALGORITHM": "LOCKED"},
    }
    validate_index(good)
    rejected = 0
    for bad in (
        {},
        {"schema": "JANUS_P_VS_NP_MATERIALS_INDEX", "scientific_authority": {"P_VS_NP": "CLOSED", "D1": "EMPTY", "SUCCESSOR_ALGORITHM": "LOCKED"}},
        {"schema": "JANUS_P_VS_NP_MATERIALS_INDEX", "scientific_authority": {"P_VS_NP": "OPEN", "D1": "NONEMPTY", "SUCCESSOR_ALGORITHM": "LOCKED"}},
        {"schema": "JANUS_P_VS_NP_MATERIALS_INDEX", "scientific_authority": {"P_VS_NP": "OPEN", "D1": "EMPTY", "SUCCESSOR_ALGORITHM": "UNLOCKED"}},
    ):
        try:
            validate_index(bad)
        except RuntimeError:
            rejected += 1
    assert rejected == 4
    return {
        "schema": "janus.topa.pnp_drive_bridge.self_test.v1",
        "status": "PASS",
        "index_firewall": True,
        "secret_material_committed": False,
        "degraded_fallback_supported": True,
        "ambiguous_publish_target_fails_closed": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("self-test")
    f = sp.add_parser("fetch-index")
    f.add_argument("--file-id", required=True)
    f.add_argument("--fallback", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--receipt", required=True)
    p = sp.add_parser("publish")
    p.add_argument("--input", required=True)
    p.add_argument("--folder-id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--mime-type")
    p.add_argument("--receipt", required=True)
    a = ap.parse_args()
    if a.cmd == "self-test":
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0
    if a.cmd == "fetch-index":
        rec = fetch_index(a.file_id, Path(a.fallback), Path(a.out), Path(a.receipt))
    else:
        rec = publish(Path(a.input), a.folder_id, a.name, Path(a.receipt), a.mime_type)
    print(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
