#!/usr/bin/env python3
"""TOPA SPIDER v2.2 — v2.1 plus transport/provider confound firewall.

The first broad runs exposed two non-scientific graph confounds:
1) collection-wide tags could masquerade as relationships;
2) rare transport/status tags (e.g. FAILED_FETCH) and provider names could
   become 'informative' merely because they were rare.

V2.2 keeps v2.1's IDF-weighted relationship engine but removes provider
identity and archive-transport/status tags from substantive relationship
scoring. They remain provenance fields on the records.
"""
from __future__ import annotations

import json
import sys

import topa_spider_v21 as base

_ORIGINAL_TAGSET = base.tagset
NON_RELATIONAL_META_TAGS = {
    "failed_fetch", "fetch_error", "link", "landing_page", "bulk_metadata",
    "declassified", "foia", "pointer", "pointer_only", "archive", "archival",
    "source", "metadata", "collection", "provider", "download", "official",
}


def filtered_tagset(record):
    tags = set(_ORIGINAL_TAGSET(record))
    provider = str(record.get("provider") or "").strip().lower()
    if provider:
        tags.discard(provider)
    return {t for t in tags if t not in NON_RELATIONAL_META_TAGS}


# Monkey-patch the v2.1 module globals used by its pair scorer, IDF calculator,
# graph builder and self tests. This preserves a single implementation of the
# mathematical engine while tightening only the epistemic tag boundary.
base.tagset = filtered_tagset


def self_test_v22():
    seeds = [
        {"provider":"CIA","archive_id":"s1","title":"Timing model","text":"reverse information timing experiment","source_url":"https://cia/s1","relation_tags":["CIA","DECLASSIFIED","anomalous cognition"]},
        {"provider":"NARA","archive_id":"s2","title":"Ukraine radar report","text":"Ukraine radar aerial observation 1983","source_url":"https://nara/s2","relation_tags":["NARA","UAP","Ukraine"]},
    ]
    candidates = [
        {"provider":"CIA","archive_id":"status-only","title":"failed request","text":"","source_url":"https://cia/fail","relation_tags":["CIA","FAILED_FETCH","DECLASSIFIED"]},
        {"provider":"NARA","archive_id":"provider-only","title":"routine inventory","text":"routine personnel inventory","source_url":"https://nara/routine","relation_tags":["NARA","UAP"]},
        {"provider":"NARA","archive_id":"real","title":"Ukraine radar incident 1983","text":"Ukraine radar aerial observation 1983","source_url":"https://nara/real","relation_tags":["NARA","UAP","Ukraine"]},
        {"provider":"NSA","archive_id":"lineage","title":"child resource","text":"transport text irrelevant","source_url":"https://nsa/child","parent_url":"https://cia/s1","relation_tags":["NSA","FOIA","LINK"]},
    ]
    pulled, receipt = base.selective_pull(
        seeds, candidates, threshold=0.20, semantic_only_threshold=0.35,
        max_pull=10, rounds=2
    )
    ids = {r["archive_id"] for r in pulled}
    assert "real" in ids
    assert "lineage" in ids
    assert "status-only" not in ids
    assert "provider-only" not in ids
    nodes, edges = base.build_graph(seeds + pulled, 0.05, 5)
    graph = base.graph_receipt(nodes, edges, seeds + pulled)
    assert graph["status"] == "PASS"
    return {
        "schema":"hawkar.topa.spider.self_test.v2.2",
        "status":"PASS",
        "provider_identity_not_relation":True,
        "transport_status_not_relation":True,
        "collection_idf_control":True,
        "explicit_lineage_preserved":True,
        "substantive_relation_preserved":True,
        "no_fixed_topic_center":True,
    }


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "self-test":
        print(json.dumps(self_test_v22(), ensure_ascii=False, indent=2))
        return 0
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
