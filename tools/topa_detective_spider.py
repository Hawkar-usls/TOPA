#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "integrations/janus-distributed-ai-swarm/topa_epistemic_router.py"
SPIDER = ROOT / "tools/topa_spider_v2.py"
PROTOCOL = ROOT / "protocols/TOPA_DETECTIVE_SPIDER_ACTIVATION_v1.0.json"

PROFILES = {
    "DETECTIVE": {"topa_core": True, "spider": True},
    "TOPA_CORE_ONLY": {"topa_core": True, "spider": False},
    "SPIDER_STANDALONE": {"topa_core": False, "spider": True},
}


def run(cmd: list[str]) -> dict:
    cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": cmd,
        "returncode": cp.returncode,
        "stdout": cp.stdout.strip(),
        "stderr": cp.stderr.strip(),
        "pass": cp.returncode == 0,
    }


def resolve(mode: str) -> dict:
    p = PROFILES[mode]
    return {
        "schema": "hawkar.topa.detective_spider.activation_receipt.v1",
        "status": "READY",
        "mode": mode,
        "default_mode": "DETECTIVE",
        "activated": {
            "topa_core": p["topa_core"],
            "spider": p["spider"],
        },
        "identity": "TOPA_DETECTIVE_SPIDER" if mode == "DETECTIVE" else mode,
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "laws": [
            "TOPA_DETECTIVE_DEFAULT_INCLUDES_SPIDER",
            "TOPA_CORE_IS_NOT_THE_SPIDER_ENGINE",
            "SPIDER_CAN_RUN_WITHOUT_TOPA_CORE",
            "TOPA_CORE_CAN_RUN_WITHOUT_SPIDER_WHEN_EXPLICITLY_REQUESTED",
            "GRAPH_EDGE_IS_NOT_CAUSATION",
            "REPLAY_IS_NOT_NEW_EVIDENCE",
        ],
    }


def self_test(mode: str) -> dict:
    receipt = resolve(mode)
    checks = []
    if receipt["activated"]["topa_core"]:
        if not ROUTER.exists():
            checks.append({"component": "TOPA_CORE", "pass": False, "error": f"missing {ROUTER}"})
        else:
            r = run([sys.executable, str(ROUTER)])
            r["component"] = "TOPA_CORE"
            checks.append(r)
    if receipt["activated"]["spider"]:
        if not SPIDER.exists():
            checks.append({"component": "SPIDER", "pass": False, "error": f"missing {SPIDER}"})
        else:
            r = run([sys.executable, str(SPIDER), "self-test"])
            r["component"] = "SPIDER"
            checks.append(r)
    receipt["checks"] = checks
    receipt["status"] = "PASS" if checks and all(c.get("pass") for c in checks) else "FAIL"
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Resolve TOPA Detective Spider capability profiles. Default mode activates TOPA core + Spider."
    )
    ap.add_argument(
        "--mode",
        choices=sorted(PROFILES),
        default="DETECTIVE",
        help="DETECTIVE is the default: TOPA core + Spider. Other modes explicitly separate them.",
    )
    ap.add_argument("--self-test", action="store_true", help="Run self-tests for all components activated by the selected mode.")
    args = ap.parse_args()

    receipt = self_test(args.mode) if args.self_test else resolve(args.mode)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] in {"READY", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
