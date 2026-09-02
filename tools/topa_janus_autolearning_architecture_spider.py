#!/usr/bin/env python3
"""TOPA Spider: evidence-first audit of the JANUS automatic-learning architecture.

The spider is deliberately read-only. It scans fresh checkouts of JANUS repositories,
builds an evidence map, and emits bounded upgrade candidates. Presence/co-occurrence is
not treated as proof that a runtime path executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

TEXT_SUFFIXES = {".py", ".yml", ".yaml", ".json", ".md", ".sh", ".js", ".ts", ".tsx", ".html", ".txt"}
EXCLUDE_PARTS = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__", "assets"}
MAX_FILE = 1_500_000
MAX_EVIDENCE_PER_CONCEPT = 20

CONCEPTS = {
    "MODEL_TRAINING": [r"\btrain(?:ing|ed)?\b", r"checkpoint", r"eval[_ -]?loss", r"candidate.*incumbent", r"optimizer"],
    "DECISION": [r"JANUS_LATEST_DECISION", r"bounded decision", r"decision[_ -]?id", r"selector", r"abstain"],
    "PROPOSAL": [r"proposal[_ -]?(?:id|sha|hash)", r"native.*proposal", r"patch[_ -]?branch", r"exact[_ -]?base"],
    "VERIFICATION": [r"VERIFY_PASS", r"VERIFY_FAIL", r"target[-_ ]local", r"verifier", r"tamper"],
    "OUTCOME_FEEDBACK": [r"outcome", r"feedback", r"training_eligible", r"REJECTED_PROVENANCE", r"bounded prior"],
    "DURABLE_MEMORY": [r"self[-_ ]memory", r"durable", r"lineage", r"receipt", r"persist"],
    "SCHEDULE": [r"\bschedule\s*:", r"cron", r"github\.event_name", r"workflow_run"],
    "OBSERVABILITY": [r"observability", r"telemetry", r"reflection", r"artifact"],
    "PROVENANCE": [r"provenance", r"sha256", r"parent[_ -]?commit", r"content[_ -]?hash", r"first_seen"],
    "AUTHORITY_FIREWALL": [r"authority", r"autonomous[_ -]?merge", r"main[_ -]?mutated", r"credentialless", r"permissions:"],
    "RELAY_OUTBOX": [r"outbox", r"relay", r"credentialless[_ -]?pull", r"mailbox"],
    "RESEARCH_CONTEXT": [r"research_context", r"Fundamentum", r"Demi_Head", r"TOPA", r"research spine"],
    "SCOUT_FRESHNESS": [r"scout", r"freshness", r"stale", r"exact[_ -]?base", r"target[_ -]?head"],
    "GIT_LIFE": [r"ALIVE_BOUNDED", r"GIT[_ -]?LIFE", r"natural.*schedule", r"schedule.*witness"],
    "GENESIS_NEXUS": [r"NEXUS", r"Genesis", r"training experiment", r"read[/_-]?inspect"],
    "RISK_ABSTENTION": [r"risk[_ -]?lane", r"abstain", r"UNKNOWN_", r"SILENCE.*NEGATIVE", r"fail[-_ ]closed"],
}

REPO_TOKENS = {
    "Janus-Demiurge", "janus-meta-registry", "Hrain", "-Terminal-for-Janus",
    "Janus_Genesis", "Janus-Fundamentum", "Demi_Head", "TOPA", "janus-lapis",
    "janus-distributed-ai-swarm", "JANUS-MACHINE-MARKET", "Janus", "aura-oracle-tg",
    "janus-io-public", "Janus-Cosmos", "Janus-HELIOS"
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in EXCLUDE_PARTS for part in p.parts):
            continue
        try:
            if p.stat().st_size > MAX_FILE:
                continue
        except OSError:
            continue
        yield p


def read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="strict")
    except Exception:
        return None


def collect_loss_records(obj, path="$"):
    out = []
    if isinstance(obj, dict):
        keys = {str(k).lower(): k for k in obj}
        interesting = [k for k in keys if "eval_loss" in k or k in {"loss", "best_loss", "candidate_loss", "incumbent_loss"}]
        vals = {}
        for lk in interesting:
            v = obj[keys[lk]]
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals[lk] = float(v)
        if vals:
            out.append({"json_path": path, "values": vals})
        for k, v in obj.items():
            out.extend(collect_loss_records(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(collect_loss_records(v, f"{path}[{i}]"))
    return out


def scan_repo(repo_dir: Path):
    repo = repo_dir.name
    concepts = defaultdict(list)
    token_counts = Counter()
    workflow_rows = []
    repo_mentions = Counter()
    loss_records = []
    scanned = 0
    bytes_scanned = 0
    parse_failures = []

    compiled = {name: [re.compile(p, re.I | re.S) for p in pats] for name, pats in CONCEPTS.items()}

    for p in iter_files(repo_dir):
        text = read_text(p)
        if text is None:
            continue
        scanned += 1
        raw = text.encode("utf-8")
        bytes_scanned += len(raw)
        rel = p.relative_to(repo_dir).as_posix()

        for concept, patterns in compiled.items():
            hits = [pat.pattern for pat in patterns if pat.search(text)]
            if hits:
                token_counts[concept] += 1
                if len(concepts[concept]) < MAX_EVIDENCE_PER_CONCEPT:
                    concepts[concept].append({"path": rel, "matched_rules": hits[:6], "sha256": sha256_bytes(raw)})

        for target in REPO_TOKENS:
            if target != repo and target.lower() in text.lower():
                repo_mentions[target] += 1

        if rel.startswith(".github/workflows/") and p.suffix.lower() in {".yml", ".yaml"}:
            workflow_rows.append({
                "path": rel,
                "has_schedule": bool(re.search(r"(?m)^\s*schedule\s*:", text)),
                "has_workflow_dispatch": "workflow_dispatch" in text,
                "has_workflow_run": "workflow_run" in text,
                "has_push": bool(re.search(r"(?m)^\s*push\s*:", text)),
                "permissions_write": bool(re.search(r"(?im)^\s*(contents|actions|checks|pull-requests)\s*:\s*write\s*$", text)),
            })

        if p.suffix.lower() == ".json" and len(raw) <= MAX_FILE:
            try:
                obj = json.loads(text)
                for row in collect_loss_records(obj):
                    if len(loss_records) >= 100:
                        break
                    loss_records.append({"path": rel, **row})
            except Exception as e:
                if len(parse_failures) < 20:
                    parse_failures.append({"path": rel, "error": type(e).__name__})

    return {
        "repo": repo,
        "head": git_head(repo_dir),
        "files_scanned": scanned,
        "bytes_scanned": bytes_scanned,
        "concept_file_counts": dict(sorted(token_counts.items())),
        "evidence": {k: v for k, v in sorted(concepts.items())},
        "workflows": workflow_rows,
        "repo_mentions": dict(repo_mentions.most_common()),
        "loss_records": loss_records,
        "json_parse_failures": parse_failures,
    }


def present(report, concept):
    return sum(r["concept_file_counts"].get(concept, 0) for r in report["repositories"]) > 0


def evidence_paths(report, concept, limit=8):
    rows = []
    for r in report["repositories"]:
        for e in r["evidence"].get(concept, []):
            rows.append(f"{r['repo']}:{e['path']}")
            if len(rows) >= limit:
                return rows
    return rows


def recommendation(rid, title, priority, rationale, implementation, gates, evidence):
    return {
        "id": rid,
        "title": title,
        "priority": priority,
        "rationale": rationale,
        "implementation": implementation,
        "acceptance_gates": gates,
        "evidence": evidence,
    }


def build_recommendations(report):
    recs = []

    if present(report, "MODEL_TRAINING"):
        recs.append(recommendation(
            "R1_STABLE_ANCHOR_EVAL",
            "Dual evaluation: adaptive corpus + frozen anchor benchmark",
            "P0",
            "A changing training corpus makes historical eval losses non-comparable. Keep the adaptive eval, but add a frozen anchor set so a new checkpoint cannot look better only because the evaluation distribution moved.",
            [
                "Create versioned JANUS_ANCHOR_EVAL corpus with immutable sha256.",
                "Record candidate/incumbent loss on both current-corpus eval and frozen anchor eval.",
                "Promotion requires current-corpus improvement AND anchor regression <= a frozen tolerance; otherwise HOLD/ABSTAIN.",
                "Store corpus_digest, anchor_digest, tokenizer/config digest and seed with every lineage record."
            ],
            [
                "Same checkpoint evaluated twice against same anchor yields identical/within deterministic tolerance result.",
                "Artificially easier changing corpus cannot promote a checkpoint that regresses beyond anchor tolerance.",
                "Old lineage remains readable and is explicitly marked COMPARABLE or NON_COMPARABLE."
            ],
            evidence_paths(report, "MODEL_TRAINING")
        ))

    if present(report, "OUTCOME_FEEDBACK") and present(report, "VERIFICATION"):
        recs.append(recommendation(
            "R2_VERIFIER_STRATIFIED_REPLAY",
            "Verifier-stratified bounded replay memory",
            "P0",
            "Verified outcome feedback exists. Improve learning by separating outcomes by verifier/organ/risk class and sampling a bounded replay buffer, while never turning silence or rejected provenance into negative evidence.",
            [
                "Store only explicit target-local VERIFY_PASS/VERIFY_FAIL with proposal hash, verifier version, target head, diff hash and receipt hash.",
                "Maintain bounded per-verifier buckets plus recency decay; cap total effect on selector score.",
                "REJECTED_PROVENANCE, STALE_BASE, NO_RECEIPT and TIMEOUT remain non-training states.",
                "Use a holdout slice of verified outcomes only for calibration, never gradient updates."
            ],
            [
                "Replay cannot flip a hard verifier failure into admissible.",
                "Removing all training-eligible receipts reproduces baseline selector behavior.",
                "Duplicate receipt replay is idempotent and does not increase weight twice."
            ],
            evidence_paths(report, "OUTCOME_FEEDBACK") + evidence_paths(report, "VERIFICATION")
        ))

    if present(report, "DECISION") and present(report, "DURABLE_MEMORY"):
        recs.append(recommendation(
            "R3_HASH_CHAINED_DECISION_CAS",
            "Hash-chained monotonic durable decision register",
            "P0",
            "Multiple automatic workflows can observe/persist state. A monotonic decision epoch plus previous-decision hash turns logical regression into a detectable conflict rather than a silent overwrite.",
            [
                "Add decision_epoch, previous_decision_sha256, checkpoint_sha256 and source_run_id to every durable decision.",
                "Writer accepts update only if previous hash equals current durable head (compare-and-swap semantics).",
                "On conflict, preserve both candidates as evidence and schedule a reconciler; never choose by timestamp alone.",
                "Keep one canonical writer for latest pointer; other workflows publish candidate receipts only."
            ],
            [
                "Concurrent stale writer cannot lower decision_epoch or replace latest pointer.",
                "Replay of an already-accepted decision is idempotent.",
                "Broken previous hash fails closed without losing either artifact."
            ],
            evidence_paths(report, "DECISION") + evidence_paths(report, "DURABLE_MEMORY")
        ))

    if present(report, "SCOUT_FRESHNESS") and present(report, "PROPOSAL"):
        recs.append(recommendation(
            "R4_FRESHNESS_LEASE_RECOMPUTE",
            "Freshness lease with automatic scout refresh and proposal recomputation",
            "P0",
            "Exact-base is the correct safety gate, but stale organ snapshots can cause useful proposals to be born obsolete. Refresh evidence and recompute; never weaken exact-base.",
            [
                "Scout receipt records repo, observed_head, observed_at, TTL/lease and content manifest hash.",
                "Before selecting an actionable proposal, compare target current head to observed_head.",
                "If stale: emit STALE_EVIDENCE, refresh Scout, then recompute decision/proposal from the new evidence.",
                "Never retarget an old patch by rebasing it automatically."
            ],
            [
                "Head change between Scout and actuator causes refresh/recompute, not patch application.",
                "Unchanged head uses existing valid lease without unnecessary rescan.",
                "Stale evidence is not counted as VERIFY_FAIL."
            ],
            evidence_paths(report, "SCOUT_FRESHNESS") + evidence_paths(report, "PROPOSAL")
        ))

    if present(report, "GIT_LIFE") or present(report, "SCHEDULE"):
        recs.append(recommendation(
            "R5_EVENT_CLASS_RECEIPTS",
            "Event-class receipts for autonomous-life evidence",
            "P1",
            "Scheduled wake, push, workflow_run and manual dispatch are different evidence classes. Persist the trigger class cryptographically in receipts so observability or training activity can never be mistaken for natural Git-Life evidence.",
            [
                "Receipt fields: event_name, workflow_ref, run_id, run_attempt, head_sha, created_at, actor_class and receipt hash.",
                "Natural-life counter accepts only frozen qualifying schedule policy and unique run ids.",
                "Push/workflow_run/manual activity stays observable but cannot elevate ALIVE_BOUNDED.",
                "Counter update is monotonic and deduplicated."
            ],
            [
                "Manual re-run cannot increment natural schedule count.",
                "workflow_run from Native Observability cannot increment natural schedule count.",
                "Seven distinct qualifying schedule receipts are required for a 7/7 witness."
            ],
            evidence_paths(report, "GIT_LIFE") + evidence_paths(report, "SCHEDULE")
        ))

    if present(report, "RESEARCH_CONTEXT"):
        recs.append(recommendation(
            "R6_RESEARCH_EVIDENCE_LAYERS",
            "Three-tier research ingestion before training",
            "P1",
            "Research can wake the brain, but external findings should not become training truth merely because they were retrieved. Split discovery, corroboration and training eligibility.",
            [
                "Tier A DISCOVERY: raw TOPA/Demi_Head/Fundamentum records with source URL/hash/date.",
                "Tier B CORROBORATED: independent-source grouping, contradiction tracking and provenance score.",
                "Tier C TRAINING_ELIGIBLE: only claims that satisfy a frozen domain-specific gate.",
                "Native Model consumes all tiers as context but gradients/priors may use only explicitly eligible fields."
            ],
            [
                "Single-source discovery never silently becomes training evidence.",
                "Contradictory sources remain simultaneously represented.",
                "Removing Tier C eligibility removes research-derived training effect while preserving observability."
            ],
            evidence_paths(report, "RESEARCH_CONTEXT")
        ))

    if present(report, "GENESIS_NEXUS") and present(report, "AUTHORITY_FIREWALL"):
        recs.append(recommendation(
            "R7_NEXUS_READ_INSPECT_GRAPH",
            "NEXUS as an organization-wide read/inspect knowledge graph",
            "P1",
            "Genesis/NEXUS can make JANUS learn from the whole organization without granting organization-wide write authority. Treat repos as versioned read-only resources and proposals as separate capability-bounded objects.",
            [
                "Build per-repo manifests: head sha, relevant file hashes, concepts, tests/workflows and cross-repo references.",
                "NEXUS edges are evidence references, not authority edges.",
                "Any mutation remains target-local proposal -> verifier -> receipt; NEXUS itself never writes target repos.",
                "Snapshot IDs are immutable and every decision records which NEXUS snapshot informed it."
            ],
            [
                "Read/inspect expansion to a new repo does not grant contents:write anywhere.",
                "A missing/inaccessible repo becomes UNKNOWN_RESOURCE, not negative evidence.",
                "Decision can be reproduced from the recorded NEXUS snapshot manifests."
            ],
            evidence_paths(report, "GENESIS_NEXUS") + evidence_paths(report, "AUTHORITY_FIREWALL")
        ))

    recs.append(recommendation(
        "R8_SHADOW_CHALLENGER",
        "Shadow challenger before autonomous promotion",
        "P1",
        "Once the loop learns from its own verified outcomes, feedback can amplify selector bias. Run a challenger policy in shadow and compare decisions without granting it actuation authority.",
        [
            "Freeze incumbent selector version for each evaluation window.",
            "Run challenger on identical evidence snapshots and record disagreements.",
            "Promote challenger only after predeclared calibration, verifier-pass, abstention and authority metrics improve.",
            "Keep rollback checkpoint and previous selector config addressable by hash."
        ],
        [
            "Challenger cannot publish actionable proposals while shadowed.",
            "Promotion report includes disagreements and explicit regressions, not only mean score.",
            "Rollback restores prior selector/checkpoint without rewriting evidence history."
        ],
        evidence_paths(report, "MODEL_TRAINING") + evidence_paths(report, "RISK_ABSTENTION")
    ))

    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Directory containing fresh repository checkouts")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = Path(args.root)
    repos = []
    for d in sorted([p for p in root.iterdir() if p.is_dir()]):
        repos.append(scan_repo(d))

    report = {
        "schema": "topa.janus_autolearning_architecture_spider.v1",
        "status": "PASS" if repos else "FAIL",
        "mode": "READ_ONLY_EVIDENCE_AUDIT",
        "repositories": repos,
        "architecture_summary": {
            "repo_count": len(repos),
            "files_scanned": sum(r["files_scanned"] for r in repos),
            "bytes_scanned": sum(r["bytes_scanned"] for r in repos),
            "concept_repo_coverage": {
                c: sorted(r["repo"] for r in repos if r["concept_file_counts"].get(c, 0))
                for c in CONCEPTS
            },
        },
        "recommendations": [],
        "epistemic_firewall": [
            "CODE_PRESENCE != RUNTIME_EXECUTION",
            "CO_OCCURRENCE != DATAFLOW_PROOF",
            "WORKFLOW_SUCCESS != MODEL_CORRECTNESS",
            "VERIFY_PASS != GLOBAL_TRUTH",
            "SILENCE != NEGATIVE_EVIDENCE",
            "OBSERVABILITY_ACTIVITY != NATURAL_GIT_LIFE_WITNESS",
            "NEXUS_READ_INSPECT != WRITE_AUTHORITY",
            "REJECTED_PROVENANCE != NEGATIVE_TRAINING_SIGNAL",
        ],
        "canonical_seal": "LEARN FROM VERIFIED OUTCOMES, NOT FROM SELF-BELIEF. KEEP EVIDENCE FRESH, EVALUATION COMPARABLE, MEMORY MONOTONIC, AND AUTHORITY LOCAL.",
    }
    report["recommendations"] = build_recommendations(report)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    compact = {
        "status": report["status"],
        "repo_count": report["architecture_summary"]["repo_count"],
        "files_scanned": report["architecture_summary"]["files_scanned"],
        "recommendations": [{"id": r["id"], "priority": r["priority"], "title": r["title"]} for r in report["recommendations"]],
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
