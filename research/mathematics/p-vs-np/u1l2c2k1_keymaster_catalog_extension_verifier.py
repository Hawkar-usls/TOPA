#!/usr/bin/env python3
"""U1-L2C2K1: proof-carrying Keymaster catalog extension.

Adds the already-proved U1-L2C2C1 swap-orbit quotient as an exact operator
without mutating the historical Keymaster v1 receipt.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from hashlib import sha256
import json
import sys

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "u1l2c2k_keymaster_exact_algebra_verifier.py"
spec = importlib.util.spec_from_file_location("keymaster_base", BASE_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = base
spec.loader.exec_module(base)

NEW = base.Operator(
    "SWAP_ORBIT_WEIGHT_EXISTS",
    "CNF",
    "SWAP_ORBIT_WEIGHT",
    "PAIR_SWAP_CLASSES_CERTIFIED_AND_ORBIT_PRODUCT_P_LE_N_POW_4",
    "U1L2C2C1_SWAP_ORBIT_WEIGHT_QUOTIENT_AND_EXISTS_UPDATE",
    "SWAP_TRANSPOSITION_PLUS_ORBIT_TABLE_CERT",
    "POLY_PAIR_SWAP_DISCOVERY_PLUS_O_N4_QUOTIENT_BUILD_FOR_FIXED_K4",
    "ORBIT_WEIGHT_REVERSE_WITNESS_LIFT",
)
SELF = base.Operator(
    "SWAP_ORBIT_WEIGHT_EXISTS_CLOSED",
    "SWAP_ORBIT_WEIGHT",
    "SWAP_ORBIT_WEIGHT",
    "NONEMPTY_BLOCK_COORDINATE",
    "Q_PRIME_W_EQ_Q_W_OR_Q_W_PLUS_EJ",
    "ORBIT_WEIGHT_EXISTS_CERT",
    "POLY_IN_EXPLICIT_ORBIT_TABLE_SIZE",
    "ORBIT_WEIGHT_REVERSE_WITNESS_LIFT",
)


def main():
    catalog = tuple(base.ACTIVE_CATALOG) + (NEW, SELF)
    summary = base.validate_catalog(catalog)
    assert summary["active_exact_operator_count"] == 14
    assert "SWAP_ORBIT_WEIGHT_EXISTS" in summary["active_operator_ids"]
    assert "SWAP_ORBIT_WEIGHT_EXISTS_CLOSED" in summary["active_operator_ids"]

    bridge = base.typecheck_compose(NEW, SELF)
    assert bridge["admitted"] is True
    self_comp = base.typecheck_compose(SELF, SELF)
    assert self_comp["admitted"] is True

    bad = base.Operator(
        "BAD_ORBIT_SCORE", "CNF", "SWAP_ORBIT_WEIGHT", "SCORE_HIGH", "NONE",
        "NONE", "NONE", "NONE", authority="HEURISTIC_ROUTER",
        forbidden_dependencies=("SCORE", "TOP_K")
    )
    ok, reason = bad.admitted()
    assert not ok and reason == "REFUSE_NONEXACT_SELECTION_AUTHORITY"

    result = {
        "schema": "JANUS_U1L2C2K1_KEYMASTER_CATALOG_EXTENSION_RESULT",
        "status": "PASS_EXACT_CATALOG_EXTENSION",
        "claim_ceiling": "P_VS_NP_OPEN",
        "base_exact_operator_count": len(base.ACTIVE_CATALOG),
        "extended_exact_operator_count": len(catalog),
        "new_operator": NEW.operator_id,
        "new_closed_update_operator": SELF.operator_id,
        "composition_CNf_to_orbit_then_exists": bridge,
        "orbit_self_composition": self_comp,
        "heuristic_injection": {"admitted": ok, "reason": reason},
        "frontier_product_bound": "FRONTIER_LE_M_TIMES_MIN_J_PRODUCT_I_NE_J_BI_PLUS_1",
        "remaining_universal_debt": [
            "POLYNOMIAL_CANONICAL_TRANSITION_STATE_COUNT_FOR_ARBITRARY_CNF",
            "POLYNOMIAL_CUMULATIVE_COST_COORDINATE_BOUNDS",
            "EXACT_QUOTIENT_FOR_ASYMMETRIC_CNF_BEYOND_SWAP_ORBITS",
            "P_VS_NP"
        ]
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("U1L2C2K1_RESULT_SHA256=" + sha256(packed).hexdigest())

if __name__ == "__main__":
    main()
