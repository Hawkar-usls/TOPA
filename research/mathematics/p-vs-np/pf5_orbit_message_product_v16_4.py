#!/usr/bin/env python3
"""PF5 orbit-count x semantic-message product v16.4.

Restricted constructive whole-order quotient for raw CNFs consisting of exact
copies of one full-support signed OR clause. Signed incidence discovers the
positive/negative variable swap orbits; duplicate clauses discover the clause
orbit. The semantic message carries only whether each projected OR side is
active. Small cases are checked against the independent exact PS/Bellman audit;
large cases are symbolic only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pf5_certified_swap_orbit_discovery_v16_3 as v16_3
import pf5_slime_exact_optimality_gap_v11 as v11
import pf5_whole_order_prefix_state_quotient_v16 as v16

Q = 2


def signed_duplicate_or(p, q, m):
    if p + q < 1 or m < 1:
        raise ValueError("nonempty family required")
    clause = tuple(list(range(1, p + 1)) + [-v for v in range(p + 1, p + q + 1)])
    return tuple(clause for _ in range(m))


def recognize(cnf):
    vg, scans = v16_3.signed_incidence_groups(cnf)
    cg = v16_3.duplicate_clause_groups(cnf)
    ok, replay = v16_3.verify_variable_group_transpositions_fix_clauses(cnf, vg)
    if not ok:
        raise AssertionError("swap replay failed")
    variables = v16_3.variables_of(cnf)
    if not cnf or not variables:
        return False, "EMPTY", vg, cg, scans + replay
    if len(cg) != 1 or any(c != cnf[0] for c in cnf):
        return False, "CLAUSES_NOT_IDENTICAL", vg, cg, scans + replay
    clause = cnf[0]
    if len(clause) != len(variables) or {abs(x) for x in clause} != set(variables):
        return False, "NOT_FULL_SUPPORT", vg, cg, scans + replay
    if any(sum(abs(l) == v for l in clause) != 1 for v in variables):
        return False, "VARIABLE_NOT_EXACTLY_ONCE", vg, cg, scans + replay
    # Equal signed-incidence groups must coincide with sign classes on this family.
    signs = {}
    for v in variables:
        signs[v] = 1 if v in clause else -1
    for group in vg:
        if len({signs[v] for v in group["variables"]}) != 1:
            return False, "SIGN_ORBIT_MISMATCH", vg, cg, scans + replay
    return True, "SIGNED_DUPLICATE_FULL_SUPPORT_OR", vg, cg, scans + replay


def group_sizes(vg):
    sizes = []
    for group in vg:
        sizes.append((group["variables"], group["size"]))
    sizes.sort(key=lambda row: (min(row[0]), row[1]))
    return [size for _, size in sizes]


def state_ranges(sizes, m):
    if len(sizes) == 1:
        a = sizes[0]
        for i in range(a + 1):
            for j in range(m + 1):
                yield (i, j)
    elif len(sizes) == 2:
        a, b = sizes
        for i in range(a + 1):
            for k in range(b + 1):
                for j in range(m + 1):
                    yield (i, k, j)
    else:
        raise ValueError("admitted family should have at most two sign orbits")


def unpack(state, sizes):
    if len(sizes) == 1:
        i, j = state
        return [i], j
    i, k, j = state
    return [i, k], j


def cost(state, sizes, m, endpoints_zero=True):
    counts, j = unpack(state, sizes)
    total = sum(counts)
    n = sum(sizes)
    if endpoints_zero and total == 0 and j == 0:
        return 0
    if endpoints_zero and total == n and j == m:
        return 0
    left = 2 if total > 0 and j < m else 1
    right = 2 if total < n and j > 0 else 1
    return max(left, right)


def actions(state, sizes, m):
    counts, j = unpack(state, sizes)
    out = []
    for g, (count, size) in enumerate(zip(counts, sizes)):
        if count < size:
            nxt_counts = list(counts); nxt_counts[g] += 1
            nxt = tuple(nxt_counts + [j]) if len(sizes) == 2 else (nxt_counts[0], j)
            out.append((f"VAR_GROUP_{g}", nxt))
    if j < m:
        nxt = tuple(counts + [j + 1]) if len(sizes) == 2 else (counts[0], j + 1)
        out.append(("CLAUSE", nxt))
    return out


def symbolic_bellman(sizes, m):
    states = list(state_ranges(sizes, m))
    states.sort(key=lambda s: sum(unpack(s, sizes)[0]) + unpack(s, sizes)[1], reverse=True)
    terminal = tuple(sizes + [m]) if len(sizes) == 2 else (sizes[0], m)
    start = tuple([0] * len(sizes) + [0]) if len(sizes) == 2 else (0, 0)
    future = {terminal: 0}; best = {terminal: None}; checks = 0; message_updates = 0
    for state in states:
        if state == terminal:
            continue
        candidates = []
        for action, nxt in actions(state, sizes, m):
            c = cost(nxt, sizes, m, True); message_updates += 1
            value = max(c, future[nxt]); checks += 1
            candidates.append((value, action, nxt))
        value, action, nxt = min(candidates, key=lambda x: (x[0], x[1]))
        future[state] = value; best[state] = (action, nxt)
    singleton = []
    if sum(sizes):
        st = ([1] + [0] * (len(sizes)-1))
        st = tuple(st + [0]) if len(sizes)==2 else (1,0)
        singleton.append(cost(st, sizes, m, False))
    if m:
        st = tuple([0] * len(sizes) + [1]) if len(sizes)==2 else (0,1)
        singleton.append(cost(st, sizes, m, False))
    return {"future": future, "best": best, "start": start, "terminal": terminal,
            "optimum": max(max(singleton, default=0), future[start]),
            "states": len(states), "transition_checks": checks, "message_updates": message_updates}


def lift(best, start, terminal, groups, m):
    remaining_vars = [list(g["variables"]) for g in groups]
    remaining_clauses = list(range(m)); state = start; order = []; checks = 0
    while state != terminal:
        action, nxt = best[state]
        if action == "CLAUSE":
            order.append(f"c:{remaining_clauses.pop(0)}")
        else:
            g = int(action.rsplit("_",1)[1])
            order.append(f"v:{remaining_vars[g].pop(0)}")
        state = nxt; checks += 1
    return order, checks


def solve(formula):
    cnf = v16_3.canonical_cnf(formula)
    admitted, reason, vg, cg, discovery_ops = recognize(cnf)
    if not admitted:
        return {"status":"OPEN_COST_LANGUAGE","reason":reason,"discovery_ops":discovery_ops}
    sizes = group_sizes(vg); m = len(cnf)
    state_product = (m+1)
    for size in sizes: state_product *= size+1
    L = v16_3.source_size_L(cnf)
    if state_product > L**Q:
        return {"status":"OPEN_PRODUCT_BUDGET","reason":"STATE_PRODUCT_GT_L2","state_product":state_product,"L":L,"discovery_ops":discovery_ops}
    sym = symbolic_bellman(sizes,m)
    order, lift_checks = lift(sym["best"], sym["start"], sym["terminal"], vg, m)
    return {"status":"CLOSED_POLY_ORBIT_MESSAGE_PRODUCT","reason":reason,"groups":vg,"sizes":sizes,"m":m,
            "state_product":state_product,"L":L,"optimum":sym["optimum"],"transition_checks":sym["transition_checks"],
            "message_updates":sym["message_updates"],"order":order,"lift_checks":lift_checks,"discovery_ops":discovery_ops}


def small_verify(p,q,m):
    formula=signed_duplicate_or(p,q,m); result=solve(formula)
    if result["status"]!="CLOSED_POLY_ORBIT_MESSAGE_PRODUCT": raise AssertionError(result)
    leaves=[f"v:{v}" for v in range(1,p+q+1)]+[f"c:{j}" for j in range(m)]
    index={x:i for i,x in enumerate(leaves)}
    cuts,ledger=v11.exact_cut_cache(formula,leaves)
    future,best_bit,raw_checks=v16.exact_future_bellman(leaves,cuts)
    singleton=max(cuts[1<<i] for i in range(len(leaves)))
    raw=max(singleton,future[0])
    width=v11.order_width_from_cache(result["order"],index,cuts)
    if not (raw==result["optimum"]==width): raise AssertionError((p,q,m,raw,result,width))
    return {"p":p,"q":q,"m":m,"raw_optimum":raw,"symbolic_optimum":result["optimum"],"lifted_width":width,
            "state_product":result["state_product"],"discovery_ops":result["discovery_ops"],"raw_cut_ledger":ledger,"raw_bellman_checks":raw_checks}


def run():
    small=[]
    for p,q,m in [(1,1,1),(2,1,2),(1,2,2),(2,2,2),(3,1,2),(1,3,2),(2,2,3),(3,2,2)]:
        small.append(small_verify(p,q,m))
    large=[]
    for p,q,m in [(8,8,16),(16,16,32),(32,32,32),(64,64,16)]:
        r=solve(signed_duplicate_or(p,q,m));
        if r["status"]!="CLOSED_POLY_ORBIT_MESSAGE_PRODUCT": raise AssertionError(r)
        large.append({"p":p,"q":q,"m":m,"state_product":r["state_product"],"L":r["L"],"optimum":r["optimum"],
                      "transition_checks":r["transition_checks"],"message_updates":r["message_updates"],"discovery_ops":r["discovery_ops"],
                      "lift_checks":r["lift_checks"],"raw_subset_enumeration_used":False,
                      "order_sha256":hashlib.sha256(json.dumps(r["order"],separators=(',',':')).encode()).hexdigest()})
    base=list(signed_duplicate_or(3,3,4)); pert=list(base[-1]); pert[-1]=-pert[-1]; base[-1]=tuple(pert)
    negatives=[solve(tuple(base)), solve(((1,2,3),(1,2),(1,2,3)))]
    if any(r["status"].startswith("CLOSED") for r in negatives): raise AssertionError(negatives)
    result={"artifact_id":"PF5-ORBIT-MESSAGE-PRODUCT-V16.4","status":"RESTRICTED_CONSTRUCTIVE_ORBIT_MESSAGE_PRODUCT_PASS",
            "api_input":"RAW_CNF_ONLY_NO_FAMILY_TAG","fixed_q":Q,"admitted_language":"SIGNED_DUPLICATE_FULL_SUPPORT_OR",
            "small_exact_controls":small,"large_symbolic_only_controls":large,
            "negative_controls":[{"status":r["status"],"reason":r["reason"]} for r in negatives],
            "theorem":{"orbit_action_state_discovered_from_signed_incidence":True,"semantic_message_exact_cost_decoder":True,
                       "product_transition_closed":True,"future_congruence_from_swap_symmetry_plus_exact_message":True,
                       "concrete_action_lift":True,"reachable_product_polynomial_on_admitted_family":True,
                       "general_product_theorem_requires_polynomial_orbit_message_product_and_discovery":True},
            "epistemic_firewall":{"large_controls_no_raw_subset_enumeration":True,"no_sat_or_exact_pswidth_or_bellman_oracle_in_discovery":True,
                                  "negative_controls_open":True,"universal_message_language_not_proved":True},
            "next_gate":"DISCOVER_RICHER_SEMANTIC_MESSAGES_THAT_COMPOSE_WITH_CERTIFIED_ORBITS",
            "universal_polynomial_prefix_quotient":"OPEN","p_vs_np":"OPEN"}
    payload=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result["result_sha256"]=hashlib.sha256(payload).hexdigest(); return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json-out',type=Path); a=ap.parse_args(); r=run()
    if a.json_out:a.json_out.write_text(json.dumps(r,indent=2,sort_keys=True),encoding='utf-8')
    print('PF5_ORBIT_MESSAGE_PRODUCT_V16_4 =',r['status'])
    print('LARGE =',[(x['p'],x['q'],x['m'],x['state_product'],x['optimum']) for x in r['large_symbolic_only_controls']])
    print('NEGATIVE =',r['negative_controls']); print('P_VS_NP = OPEN'); print('RESULT_SHA256 =',r['result_sha256'])
if __name__=='__main__': main()
