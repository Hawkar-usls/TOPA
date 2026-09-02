#!/usr/bin/env python3
"""Git-indexed TOPA scanner for JANUS automatic-learning architecture.

Uses git's index/search engine for broad evidence discovery and opens only matched
files for hashing/deep JSON inspection. This keeps org-wide scheduled scans bounded.
"""
from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import topa_janus_autolearning_architecture_spider as base

TERMS = {
    "MODEL_TRAINING": ["train", "checkpoint", "eval_loss", "incumbent", "optimizer"],
    "DECISION": ["JANUS_LATEST_DECISION", "decision_id", "selector", "abstain"],
    "PROPOSAL": ["proposal_sha", "proposal_id", "exact_base", "exact-base", "patch_branch"],
    "VERIFICATION": ["VERIFY_PASS", "VERIFY_FAIL", "verifier", "target-local", "tamper"],
    "OUTCOME_FEEDBACK": ["outcome", "feedback", "training_eligible", "REJECTED_PROVENANCE", "bounded prior"],
    "DURABLE_MEMORY": ["self-memory", "self_memory", "durable", "lineage", "receipt", "persist"],
    "SCHEDULE": ["schedule:", "cron:", "github.event_name", "workflow_run"],
    "OBSERVABILITY": ["observability", "telemetry", "reflection", "artifact"],
    "PROVENANCE": ["provenance", "sha256", "parent_commit", "content_hash", "first_seen"],
    "AUTHORITY_FIREWALL": ["authority", "autonomous_merge", "main_mutated", "credentialless", "permissions:"],
    "RELAY_OUTBOX": ["outbox", "relay", "credentialless pull", "mailbox"],
    "RESEARCH_CONTEXT": ["research_context", "Fundamentum", "Demi_Head", "TOPA", "research spine"],
    "SCOUT_FRESHNESS": ["scout", "freshness", "stale", "exact_base", "target_head"],
    "GIT_LIFE": ["ALIVE_BOUNDED", "GIT_LIFE", "Git-Life", "natural schedule", "schedule witness"],
    "GENESIS_NEXUS": ["NEXUS", "Genesis", "training experiment", "read/inspect", "read-inspect"],
    "RISK_ABSTENTION": ["risk_lane", "abstain", "UNKNOWN_", "SILENCE", "fail-closed"],
}

TEXT_GLOBS = ["*.py", "*.yml", "*.yaml", "*.json", "*.md", "*.sh", "*.js", "*.ts", "*.tsx", "*.html", "*.txt"]
DEEP_JSON_TERMS = ["eval_loss", "candidate_eval_loss", "incumbent_eval_loss", "best_eval_loss"]


def run(repo: Path, args: list[str], ok=(0,)) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if p.returncode not in ok:
        raise RuntimeError(f"git {' '.join(args)} rc={p.returncode}: {p.stderr[:300]}")
    return p.stdout


def tracked_text_files(repo: Path) -> list[str]:
    rows = run(repo, ["ls-files", "-z"]).split("\0")
    out = []
    for rel in rows:
        if not rel:
            continue
        p = Path(rel)
        if p.suffix.lower() not in base.TEXT_SUFFIXES:
            continue
        if any(part in base.EXCLUDE_PARTS for part in p.parts):
            continue
        out.append(rel)
    return out


def grep_paths(repo: Path, terms: list[str]) -> list[str]:
    args = ["grep", "-I", "-i", "-l"]
    for term in terms:
        args += ["-e", term]
    args += ["--", *TEXT_GLOBS]
    out = run(repo, args, ok=(0, 1))
    return sorted({line.strip() for line in out.splitlines() if line.strip()})


def evidence_row(repo: Path, rel: str, terms: list[str]):
    p = repo / rel
    try:
        raw = p.read_bytes()
    except OSError:
        return {"path": rel, "matched_terms": [], "sha256": None}
    if len(raw) > base.MAX_FILE:
        return {"path": rel, "matched_terms": [], "sha256": base.sha256_bytes(raw), "oversize_for_text_evidence": True}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = ""
    lower = text.lower()
    hits = [t for t in terms if t.lower() in lower]
    return {"path": rel, "matched_terms": hits[:8], "sha256": base.sha256_bytes(raw)}


def scan_repo_indexed(repo_dir: Path):
    repo_name = repo_dir.name
    tracked = tracked_text_files(repo_dir)
    evidence = defaultdict(list)
    counts = Counter()

    for concept, terms in TERMS.items():
        paths = grep_paths(repo_dir, terms)
        counts[concept] = len(paths)
        for rel in paths[:base.MAX_EVIDENCE_PER_CONCEPT]:
            evidence[concept].append(evidence_row(repo_dir, rel, terms))

    workflows = []
    for rel in tracked:
        if not rel.startswith(".github/workflows/") or Path(rel).suffix.lower() not in {".yml", ".yaml"}:
            continue
        try:
            text = (repo_dir / rel).read_text(encoding="utf-8")
        except Exception:
            continue
        low = text.lower()
        workflows.append({
            "path": rel,
            "has_schedule": "schedule:" in low and "cron:" in low,
            "has_workflow_dispatch": "workflow_dispatch" in low,
            "has_workflow_run": "workflow_run" in low,
            "has_push": "push:" in low,
            "permissions_write": any(x in low for x in ["contents: write", "actions: write", "checks: write", "pull-requests: write"]),
        })

    loss_paths = grep_paths(repo_dir, DEEP_JSON_TERMS)
    loss_records = []
    parse_failures = []
    for rel in loss_paths[:80]:
        if not rel.lower().endswith(".json"):
            continue
        p = repo_dir / rel
        try:
            if p.stat().st_size > base.MAX_FILE:
                continue
            obj = json.loads(p.read_text(encoding="utf-8"))
            for row in base.collect_loss_records(obj):
                if len(loss_records) >= 100:
                    break
                loss_records.append({"path": rel, **row})
        except Exception as exc:
            if len(parse_failures) < 20:
                parse_failures.append({"path": rel, "error": type(exc).__name__})

    # Cross-repo links are evidence references only. Use indexed grep, not a full read.
    mentions = Counter()
    for token in sorted(base.REPO_TOKENS):
        if token == repo_name:
            continue
        paths = grep_paths(repo_dir, [token])
        if paths:
            mentions[token] = len(paths)

    byte_estimate = 0
    for rel in tracked:
        try:
            byte_estimate += (repo_dir / rel).stat().st_size
        except OSError:
            pass

    return {
        "repo": repo_name,
        "head": base.git_head(repo_dir),
        "files_scanned": len(tracked),
        "bytes_scanned": byte_estimate,
        "scan_mode": "GIT_INDEX_BROAD_SCAN_PLUS_MATCHED_FILE_DEEP_READ",
        "concept_file_counts": dict(sorted(counts.items())),
        "evidence": {k: v for k, v in sorted(evidence.items())},
        "workflows": workflows,
        "repo_mentions": dict(mentions.most_common()),
        "loss_records": loss_records,
        "json_parse_failures": parse_failures,
    }


if __name__ == "__main__":
    base.scan_repo = scan_repo_indexed
    base.main()
