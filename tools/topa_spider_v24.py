#!/usr/bin/env python3
"""TOPA SPIDER v2.4 — archive tag prevalence ceiling.

V2.3 normalized tag frequencies to the archive universe. The next live run
showed that a broad archive subject label can still contribute if it appears in
most, but not all, archive candidates. V2.4 therefore gives zero substantive
relationship weight to tags present in more than 20% of the current archive
universe. Such tags remain searchable/provenance context; they cannot pull a
record by themselves.
"""
from __future__ import annotations

import collections
import json
import math
import sys

import topa_spider_v23 as v23

base = v23.base
MAX_SUBSTANTIVE_ARCHIVE_TAG_PREVALENCE = 0.20


def prevalence_capped_archive_tag_idf(records):
    rows = list(records)
    archive_rows = [r for r in rows if str(r.get("provider") or "") != "TOPA_REPO"]
    universe = archive_rows if archive_rows else rows
    n = max(1, len(universe))
    df = collections.Counter()
    for r in universe:
        for t in base.tagset(r):
            df[t] += 1
    out = {}
    for t, c in df.items():
        prevalence = c / n
        out[t] = 0.0 if prevalence > MAX_SUBSTANTIVE_ARCHIVE_TAG_PREVALENCE else math.log((1 + n) / (1 + c))
    return out


base.tag_idf = prevalence_capped_archive_tag_idf


def self_test_v24():
    seeds = [
        {"provider":"TOPA_REPO","archive_id":"repo-uap","title":"historical UAP investigation","text":"UAP radar methods","source_url":"repo://uap","relation_tags":["HUNT"]},
        {"provider":"TOPA_REPO","archive_id":"repo-ua","title":"Ukraine radar investigation","text":"Ukraine radar aerial observation 1983","source_url":"repo://ua","relation_tags":["Ukraine"]},
        {"provider":"FBI","archive_id":"landing","title":"UAP landing","text":"UAP index","source_url":"https://fbi/uap","relation_tags":["UAP","LANDING_PAGE","FBI"]},
    ]
    candidates=[]
    for i in range(30):
        candidates.append({"provider":"NARA","archive_id":f"generic-{i}","title":f"generic UAP record {i}","text":"routine administrative material","source_url":f"https://nara/{i}","relation_tags":["NARA","UAP"]})
    candidates.append({"provider":"NARA","archive_id":"ukraine","title":"Ukraine radar aerial observation 1983","text":"Ukraine radar aerial observation 1983","source_url":"https://nara/ua","relation_tags":["NARA","UAP","Ukraine"]})
    weights=prevalence_capped_archive_tag_idf(seeds+candidates)
    assert weights.get("uap",999)==0.0
    assert weights.get("ukraine",0)>0
    pulled,receipt=base.selective_pull(seeds,candidates,threshold=0.24,semantic_only_threshold=0.42,max_pull=100,rounds=2)
    ids={r["archive_id"] for r in pulled}
    assert "ukraine" in ids
    assert not any(x.startswith("generic-") for x in ids)
    return {
        "schema":"hawkar.topa.spider.self_test.v2.4",
        "status":"PASS",
        "archive_tag_prevalence_ceiling":MAX_SUBSTANTIVE_ARCHIVE_TAG_PREVALENCE,
        "archive_wide_subject_tag_zero_weight":True,
        "rare_relation_tag_preserved":True,
        "no_fixed_topic_center":True
    }


def main():
    if len(sys.argv)>=2 and sys.argv[1]=="self-test":
        print(json.dumps(self_test_v24(),ensure_ascii=False,indent=2));return 0
    return base.main()


if __name__=="__main__":
    raise SystemExit(main())
