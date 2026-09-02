#!/usr/bin/env python3
"""Fast two-speed scanner for TOPA JANUS architecture audit.

Stage 1 scans all bounded text files for architecture concepts.
Stage 2 parses JSON deeply only when the path is learning/model/state related.
It reuses the evidence schema and recommendation engine from the base spider.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import topa_janus_autolearning_architecture_spider as base

DEEP_JSON_HINTS = (
    "model", "learning", "lineage", "checkpoint", "decision", "outcome",
    "training", "brain", "native", "feedback", "receipt", "proposal",
)


def scan_repo_fast(repo_dir: Path):
    repo = repo_dir.name
    concepts = defaultdict(list)
    token_counts = Counter()
    workflow_rows = []
    repo_mentions = Counter()
    loss_records = []
    scanned = 0
    bytes_scanned = 0
    parse_failures = []

    # No DOTALL: architecture signatures should be local, and this avoids
    # expensive whole-document backtracking on large registry JSON files.
    compiled = {
        name: [re.compile(pattern, re.I) for pattern in patterns]
        for name, patterns in base.CONCEPTS.items()
    }
    repo_tokens = [(token, token.lower()) for token in base.REPO_TOKENS]

    for p in base.iter_files(repo_dir):
        text = base.read_text(p)
        if text is None:
            continue
        scanned += 1
        raw = text.encode("utf-8")
        bytes_scanned += len(raw)
        rel = p.relative_to(repo_dir).as_posix()
        rel_lower = rel.lower()
        text_lower = text.lower()

        for concept, patterns in compiled.items():
            hits = [pat.pattern for pat in patterns if pat.search(text)]
            if hits:
                token_counts[concept] += 1
                if len(concepts[concept]) < base.MAX_EVIDENCE_PER_CONCEPT:
                    concepts[concept].append({
                        "path": rel,
                        "matched_rules": hits[:6],
                        "sha256": base.sha256_bytes(raw),
                    })

        for target, target_lower in repo_tokens:
            if target != repo and target_lower in text_lower:
                repo_mentions[target] += 1

        if rel.startswith(".github/workflows/") and p.suffix.lower() in {".yml", ".yaml"}:
            workflow_rows.append({
                "path": rel,
                "has_schedule": bool(re.search(r"(?m)^\s*schedule\s*:", text)),
                "has_workflow_dispatch": "workflow_dispatch" in text,
                "has_workflow_run": "workflow_run" in text,
                "has_push": bool(re.search(r"(?m)^\s*push\s*:", text)),
                "permissions_write": bool(re.search(
                    r"(?im)^\s*(contents|actions|checks|pull-requests)\s*:\s*write\s*$", text
                )),
            })

        deep_json = (
            p.suffix.lower() == ".json"
            and len(raw) <= base.MAX_FILE
            and any(hint in rel_lower for hint in DEEP_JSON_HINTS)
        )
        if deep_json:
            try:
                obj = json.loads(text)
                for row in base.collect_loss_records(obj):
                    if len(loss_records) >= 100:
                        break
                    loss_records.append({"path": rel, **row})
            except Exception as exc:
                if len(parse_failures) < 20:
                    parse_failures.append({"path": rel, "error": type(exc).__name__})

    return {
        "repo": repo,
        "head": base.git_head(repo_dir),
        "files_scanned": scanned,
        "bytes_scanned": bytes_scanned,
        "scan_mode": "TWO_SPEED_MANIFEST_PLUS_TARGETED_DEEP_JSON",
        "concept_file_counts": dict(sorted(token_counts.items())),
        "evidence": {k: v for k, v in sorted(concepts.items())},
        "workflows": workflow_rows,
        "repo_mentions": dict(repo_mentions.most_common()),
        "loss_records": loss_records,
        "json_parse_failures": parse_failures,
    }


if __name__ == "__main__":
    base.scan_repo = scan_repo_fast
    base.main()
