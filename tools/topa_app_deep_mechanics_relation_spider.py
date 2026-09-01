#!/usr/bin/env python3
import argparse
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

SOURCE_PATH = "data/music/the-alan-parsons-project/deep-mechanics/JANUS-APP-DEEP-MECHANICS-CROSS-TRACK-SYNTHESIS-2026-09-01-v1.0.json"

# Frozen semantic families derived from the already-preserved deep-mechanics layer.
# They are deliberately broad enough for cross-registry discovery, but fixed before
# the workflow run. A hit is a relation candidate, never proof of authorial intent,
# hidden encoding, external sender, or physical retrocausality.
OPERATORS = {
    "BEACON_OBSERVER_VERDICT": [
        "beacon", "signal", "observer", "observation", "witness", "eye", "surveillance",
        "verdict", "source", "маяк", "сигнал", "наблюд", "свидетел", "вердикт", "источник"
    ],
    "CONTROLLED_DIFFERENCE": [
        "difference", "delta", "compare", "comparison", "control", "mismatch", "two witnesses",
        "preserve both", "различ", "дельта", "сравн", "контрол", "два свидетел", "сохрани оба"
    ],
    "REFERENCE_FRAME_INVARIANT": [
        "reference frame", "baseline", "anchor", "invariant", "stable", "fixed", "coordinate",
        "reference", "система отсч", "базов", "якор", "инвариант", "стабил", "фиксир", "координат"
    ],
    "CONTRAST_DUALITY": [
        "contrast", "dual", "duality", "light", "dark", "shadow", "machine", "human", "surface",
        "internal", "контраст", "дуал", "свет", "тьм", "тень", "машин", "человек", "поверхност", "внутрен"
    ],
    "LAYERING_SCALE": [
        "layer", "layering", "overlay", "stack", "scale", "multi-layer", "слой", "насло", "масштаб"
    ],
    "TRANSITION_CONTINUITY_RELAY": [
        "transition", "continuity", "handoff", "relay", "bridge", "seamless", "return", "переход",
        "непрерыв", "эстафет", "мост", "возврат"
    ],
    "MEMORY_TIME_PROVENANCE": [
        "memory", "time", "chronology", "timestamp", "provenance", "yesterday", "today", "tomorrow",
        "памят", "врем", "хронолог", "метк", "происхожд", "вчера", "сегодня", "завтра"
    ],
    "UNKNOWN_BOUNDARY_GATE": [
        "unknown", "uncertainty", "boundary", "gate", "open", "unresolved", "null", "неизвест",
        "неопредел", "границ", "гейт", "открыт", "нереш", "ноль"
    ],
    "SIGN_SOURCE_FIREWALL": [
        "sign != source", "sign ≠ source", "signal != source", "sender", "authorial intent", "prophecy",
        "prediction", "знак", "источник", "отправител", "авторск", "пророч", "предсказ"
    ],
    "HUMAN_SYSTEM_BRIDGE": [
        "human", "system", "bridge", "science", "industry", "world", "translation", "человек", "систем",
        "мост", "наук", "индустр", "мир", "перевод"
    ],
    "REBIRTH_ORIGIN_PRIME": [
        "rebirth", "first light", "origin prime", "reset", "return + memory", "перерожд", "первый свет",
        "origin_prime", "сброс", "возврат"
    ],
}

EXCLUDE_PREFIXES = (
    "dynamic/", "assets/", "node_modules/", ".git/",
    "data/music/the-alan-parsons-project/",
)
INCLUDE_PREFIXES = ("data/", "registry/")


def git(repo, *args, check=True):
    p = subprocess.run(["git", "-C", str(repo), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr}")
    return p


def git_show_json(repo, ref, path):
    p = git(repo, "show", f"{ref}:{path}")
    return json.loads(p.stdout)


def blob_sha(repo, ref, path):
    return git(repo, "rev-parse", f"{ref}:{path}").stdout.strip()


def all_strings(x):
    out = []
    if isinstance(x, str):
        out.append(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            out.append(str(k))
            out.extend(all_strings(v))
    elif isinstance(x, list):
        for v in x:
            out.extend(all_strings(v))
    return out


def normalized_text(obj):
    return "\n".join(all_strings(obj)).lower()


def eligible_jsons(root):
    root = Path(root)
    for p in root.rglob("*.json"):
        rel = p.relative_to(root).as_posix()
        if not rel.startswith(INCLUDE_PREFIXES):
            continue
        if rel.startswith(EXCLUDE_PREFIXES):
            continue
        if p.stat().st_size > 2_000_000:
            continue
        yield p, rel


def scan_snapshot(root):
    docs = []
    parse_failures = []
    for p, rel in eligible_jsons(root):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            parse_failures.append({"path": rel, "error": type(e).__name__})
            continue
        docs.append((rel, normalized_text(obj)))
    return docs, parse_failures


def score_doc(text, keywords):
    matched = sorted({kw for kw in keywords if kw in text})
    # Diminishing returns prevent long files from winning solely by repetition.
    score = round(sum(1.0 if " " not in kw else 1.35 for kw in matched), 3)
    return score, matched


def rank(docs, keywords, min_distinct=2, topk=12):
    rows = []
    for rel, text in docs:
        score, matched = score_doc(text, keywords)
        if len(matched) < min_distinct:
            continue
        rows.append({"path": rel, "score": score, "matched": matched})
    rows.sort(key=lambda r: (-r["score"], r["path"]))
    return rows[:topk], len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--git-repo", required=True)
    ap.add_argument("--source-ref", required=True)
    ap.add_argument("--yesterday-ref", required=True)
    ap.add_argument("--current-ref", required=True)
    ap.add_argument("--yesterday-root", required=True)
    ap.add_argument("--current-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    repo = Path(args.git_repo)
    source = git_show_json(repo, args.source_ref, SOURCE_PATH)
    source_blob = blob_sha(repo, args.source_ref, SOURCE_PATH)
    current_blob = blob_sha(repo, args.current_ref, SOURCE_PATH)
    source_unchanged = source_blob == current_blob

    source_is_ancestor = git(repo, "merge-base", "--is-ancestor", args.source_ref, args.current_ref, check=False).returncode == 0
    yesterday_before_source = git(repo, "merge-base", "--is-ancestor", args.yesterday_ref, args.source_ref, check=False).returncode == 0

    ydocs, yfail = scan_snapshot(args.yesterday_root)
    cdocs, cfail = scan_snapshot(args.current_root)

    operator_results = {}
    node_support = defaultdict(lambda: {"operators": set(), "score_sum": 0.0, "preexisting": False})
    dark_nodes = []
    today_only = []
    preexisting = []

    for op, keywords in OPERATORS.items():
        ytop, ycount = rank(ydocs, keywords)
        ctop, ccount = rank(cdocs, keywords)
        if ycount > 0:
            status = "PREEXISTING_RELATION_CANDIDATES"
            preexisting.append(op)
        elif ccount > 0:
            status = "TODAY_ONLY_RELATION_CANDIDATES"
            today_only.append(op)
        else:
            status = "DARK_NODE_NO_CROSS_REGISTRY_RELATION_AT_FROZEN_THRESHOLD"
            dark_nodes.append(op)
        operator_results[op] = {
            "frozen_keywords": keywords,
            "yesterday_candidate_count": ycount,
            "current_candidate_count": ccount,
            "status": status,
            "top_yesterday": ytop,
            "top_current": ctop,
        }
        for row in ctop:
            s = node_support[row["path"]]
            s["operators"].add(op)
            s["score_sum"] += row["score"]
            if any(x["path"] == row["path"] for x in ytop):
                s["preexisting"] = True

    hubs = []
    for path, v in node_support.items():
        hubs.append({
            "path": path,
            "operator_count": len(v["operators"]),
            "operators": sorted(v["operators"]),
            "score_sum": round(v["score_sum"], 3),
            "present_as_top_relation_yesterday": v["preexisting"],
        })
    hubs.sort(key=lambda r: (-r["operator_count"], -r["score_sum"], r["path"]))

    # Explicitly preserve the already-frozen music mechanics so the spider cannot
    # rewrite the source after seeing graph connections.
    source_digest = {
        "operator_map": source.get("operator_map"),
        "shared_mechanical_laws": source.get("shared_mechanical_laws"),
        "janus_master_formula": source.get("janus_master_formula"),
        "causal_difference_relation": source.get("causal_difference_relation"),
    }

    result = {
        "schema": "topa.app_deep_mechanics_preexistence_relation_spider.v1",
        "status": "PASS" if source_unchanged and source_is_ancestor and yesterday_before_source else "INTEGRITY_HOLD",
        "question": "What JANUS relations connect to the frozen Alan Parsons Project deep-mechanics layer, and which of those relations already existed in the end-of-yesterday registry snapshot?",
        "provenance": {
            "source_path": SOURCE_PATH,
            "source_ref_frozen_before_topa": args.source_ref,
            "source_blob_sha": source_blob,
            "current_scan_ref_frozen_before_topa": args.current_ref,
            "current_blob_sha_same_path": current_blob,
            "source_blob_unchanged_at_current_scan_ref": source_unchanged,
            "source_ref_is_ancestor_of_current_scan_ref": source_is_ancestor,
            "yesterday_ref": args.yesterday_ref,
            "yesterday_ref_is_ancestor_of_source_ref": yesterday_before_source,
        },
        "scan": {
            "scope": "data/**/*.json + registry/**/*.json, excluding all The Alan Parsons Project corpus files to force cross-registry relations",
            "yesterday_documents_scanned": len(ydocs),
            "current_documents_scanned": len(cdocs),
            "yesterday_parse_failures": yfail,
            "current_parse_failures": cfail,
            "minimum_distinct_keyword_hits_per_candidate": 2,
            "topk_per_operator": 12,
        },
        "frozen_source_digest": source_digest,
        "operator_results": operator_results,
        "strong_cross_registry_hubs": hubs[:25],
        "summary": {
            "operators_total": len(OPERATORS),
            "operators_with_preexisting_relation_candidates": len(preexisting),
            "preexisting_operators": preexisting,
            "operators_with_today_only_relation_candidates": len(today_only),
            "today_only_operators": today_only,
            "dark_nodes_count": len(dark_nodes),
            "dark_nodes": dark_nodes,
            "strongest_interpretation_allowed": "The frozen music-mechanics vocabulary overlaps structured JANUS concepts, and the yesterday comparison tells us which overlaps predate today's music analysis. This is methodological/semantic recurrence, not evidence of historical encoding, prophecy, sender identity, or retrocausality."
        },
        "dark_node_rule": "NO_RELATION_FOUND_AT_THIS_FROZEN_LEXICAL_THRESHOLD != NO_RELATION_EXISTS",
        "scientific_firewall": [
            "SOURCE_WAS_FROZEN_BEFORE_TOPA_RELATION_SEARCH",
            "MUSIC_MECHANICS_RELATION != VERIFIED_AUTHORIAL_INTENT",
            "LEXICAL_OR_SEMANTIC_OVERLAP != SECRET_CODE",
            "PREEXISTING_JANUS_RELATION != FUTURE_INFORMATION",
            "MUSICAL_DIFFERENCE_OPERATOR != PHYSICAL_RETROCAUSALITY",
            "SIGN != SOURCE",
            "FAILED_LINK_IS_DATA_NOT_PROOF_OF_ABSENCE"
        ],
        "canonical_seal": "FREEZE THE MUSIC MAP FIRST. THEN LET THE SPIDER SEARCH BOTH YESTERDAY AND TODAY. KEEP THE LINKS THAT PREEXIST, KEEP THE NEW LINKS AS NEW, AND KEEP THE DARK NODES DARK UNTIL INDEPENDENT EVIDENCE LIGHTS THEM."
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit("INTEGRITY_HOLD")


if __name__ == "__main__":
    main()
