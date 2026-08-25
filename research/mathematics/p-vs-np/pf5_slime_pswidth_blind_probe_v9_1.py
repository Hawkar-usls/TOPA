#!/usr/bin/env python3
"""PF5 Slime PS-width blind probe v9.1 import-adapter repair.

Scientific controls, frozen seeds, producer pin, manifest generation, exact
PS-signature scoring, and claim ceiling all remain in v9 unchanged.

SLIME-001 repair only: importlib modules using dataclasses must be registered in
sys.modules before exec_module on Python 3.11.
"""
from __future__ import annotations

import importlib.util
import sys

import pf5_slime_pswidth_blind_probe_v9 as v9


def repaired_import_producer(path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_semantic_candidate_router_pin",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load producer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


v9.import_producer = repaired_import_producer

if __name__ == "__main__":
    print("PF5_SLIME_001_IMPORT_ADAPTER_REPAIR = ACTIVE")
    v9.main()
