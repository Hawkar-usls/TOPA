#!/usr/bin/env python3
"""TOPA SPIDER v2.3 — archive-universe IDF normalization.

V2.2 connected the full TOPA repository memory to SPIDER. A live run exposed a
new confound: a tag common inside the archive (e.g. the broad subject tag UAP)
can appear rare relative to hundreds of unrelated TOPA repository documents.
That makes the archive-wide subject label look more informative than it is.

V2.3 computes relationship-tag IDF on the archive/provider universe only.
TOPA repository memory remains semantic discovery context, but cannot alter the
baseline frequency of archive metadata tags.
"""
from __future__ import annotations

import collections
import json
import math
import sys

import topa_spider_v22 as v22

base = v22.base
_ORIGINAL_TAG_IDF = base.tag_idf


def archive_universe_tag_idf(records):
    rows = list(records)
    archive_rows = [r for r in rows if str(r.get("provider") or "") != "TOPA_REPO"]
    universe = archive_rows if archive_rows else rows
    n = max(1, len(universe))
    df = collections.Counter()
    for r in universe:
        for t in base.tagset(r):
            df[t] += 1
    return {t: math.log((1 + n) / (1 + c)) for t, c in df.items()}


base.tag_idf = archive_universe_tag_idf


def self_test_v23():
    repo_seeds = [
        {"provider":"TOPA_REPO","archive_id":f"repo-{i}","title":f"unrelated memory {i}","text":"mathematics method null control","source_url":f"repo://{i}","relation_tags":["MATHEMATICS"]}
        for i in range(40)
    ]
    repo_seeds.append({
        "provider":"TOPA_REPO","archive_id":"repo-ukraine","title":"Ukraine radar investigation",
        "text":"Ukraine radar aerial observation 1983","source_url":"repo://ukraine",
        "relation_tags":["Ukraine","HUNT"]
    })
    archive_seed = {
        "provider":"FBI","archive_id":"landing","title":"UAP archive landing",
        "text":"UAP archival index","source_url":"https://fbi/landing","relation_tags":["FBI","UAP","LANDING_PAGE"]
    }
    candidates = [
        {"provider":"NARA","archive_id":f"generic-{i}","title":f"generic UAP record {i}",
         "text":"routine administrative item","source_url":f"https://nara/g{i}","relation_tags":["NARA","UAP"]}
        for i in range(20)
    ]
    candidates.append({
        "provider":"NARA","archive_id":"ukraine-1983","title":"Ukraine radar aerial observation 1983",
        "text":"Ukraine radar aerial observation 1983","source_url":"https://nara/ua","relation_tags":["NARA","UAP","Ukraine"]
    })
    pulled, receipt = base.selective_pull(
        repo_seeds + [archive_seed], candidates,
        threshold=0.24, semantic_only_threshold=0.42, max_pull=100, rounds=2
    )
    ids = {r["archive_id"] for r in pulled}
    assert "ukraine-1983" in ids
    assert not any(x.startswith("generic-") for x in ids)
    weights = archive_universe_tag_idf(repo_seeds + [archive_seed] + candidates)
    assert weights.get("uap", 999) < weights.get("ukraine", 0)
    return {
        "schema":"hawkar.topa.spider.self_test.v2.3",
        "status":"PASS",
        "archive_universe_idf":True,
        "repo_memory_cannot_make_archive_wide_tag_rare":True,
        "rare_archive_feature_preserved":True,
        "no_fixed_topic_center":True
    }


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "self-test":
        print(json.dumps(self_test_v23(), ensure_ascii=False, indent=2))
        return 0
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
