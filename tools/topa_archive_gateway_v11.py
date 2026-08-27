#!/usr/bin/env python3
"""TOPA Archive Gateway v1.1 — provider hygiene layer.

The first live SPIDER searches revealed that the FBI Vault landing harvester
accepted generic Vault navigation links because they shared the vault.fbi.gov
host. V1.1 keeps only the UFO landing itself and descendants of /UFO/.

This wrapper preserves the v1 gateway provider behavior for NARA/CIA/NSA and
adds a fail-closed FBI collection boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
from pathlib import Path

import topa_archive_gateway as base


def canon(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def is_fbi_ufo_resource(record):
    if str(record.get("provider") or "").upper() != "FBI":
        return True
    url = str(record.get("source_url") or "")
    if url.rstrip("/") == base.FBI_UFO.rstrip("/"):
        return True
    parsed = urllib.parse.urlparse(url)
    return parsed.hostname == "vault.fbi.gov" and parsed.path.lower().startswith("/ufo/")


def ingest(providers, limit, expand_nara):
    rows, receipt = base.ingest(providers, limit, expand_nara)
    before = len(rows)
    rows = [r for r in rows if is_fbi_ufo_resource(r)]
    rows.sort(key=lambda r:(r.get("provider",""), r.get("archive_id",""), r.get("source_url","")))
    receipt = dict(receipt)
    receipt["schema"] = "hawkar.topa.archive_gateway.receipt.v1.1"
    receipt["records_before_provider_hygiene"] = before
    receipt["records"] = len(rows)
    receipt["fbi_navigation_records_rejected"] = before - len(rows)
    receipt["provider_hygiene"] = {
        "FBI":"KEEP_LANDING_AND_PATH_PREFIX_/UFO/_ONLY",
        "law":"SAME_HOST_IS_NOT_COLLECTION_MEMBERSHIP"
    }
    receipt["record_stream_sha256"] = hashlib.sha256("".join(canon(r)+"\n" for r in rows).encode("utf-8")).hexdigest()
    return rows, receipt


def self_test():
    rows = [
        {"provider":"FBI","source_url":"https://vault.fbi.gov/UFO"},
        {"provider":"FBI","source_url":"https://vault.fbi.gov/UFO/UFO%20Part%2001/view"},
        {"provider":"FBI","source_url":"https://vault.fbi.gov/search"},
        {"provider":"FBI","source_url":"https://vault.fbi.gov/about-vault"},
        {"provider":"NARA","source_url":"https://catalog.archives.gov/x"},
    ]
    kept = [r for r in rows if is_fbi_ufo_resource(r)]
    urls = {r["source_url"] for r in kept}
    assert "https://vault.fbi.gov/UFO" in urls
    assert "https://vault.fbi.gov/UFO/UFO%20Part%2001/view" in urls
    assert "https://vault.fbi.gov/search" not in urls
    assert "https://vault.fbi.gov/about-vault" not in urls
    assert "https://catalog.archives.gov/x" in urls
    return {"schema":"hawkar.topa.archive_gateway.self_test.v1.1","status":"PASS","fbi_collection_boundary":True,"same_host_not_enough":True}


def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);sp.add_parser("self-test")
    q=sp.add_parser("ingest");q.add_argument("--providers",default="nara,cia,nsa,fbi");q.add_argument("--limit",type=int,default=25);q.add_argument("--expand-nara",action="store_true");q.add_argument("--out",required=True);q.add_argument("--receipt",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test":
        print(json.dumps(self_test(),ensure_ascii=False,indent=2));return 0
    rows,receipt=ingest([x.strip().lower() for x in a.providers.split(",") if x.strip()],a.limit,a.expand_nara)
    base.write_jsonl(Path(a.out),rows)
    Path(a.receipt).parent.mkdir(parents=True,exist_ok=True)
    Path(a.receipt).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if rows else 1


if __name__=="__main__":
    raise SystemExit(main())
