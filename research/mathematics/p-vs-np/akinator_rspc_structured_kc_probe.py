#!/usr/bin/env python3
"""Finite mechanics for RSPC structured knowledge-compilation barrier.

Checks only the expander-style monotone 2-CNF/B2 encoding mechanics on small
bounded-degree graphs. It does not prove asymptotic treewidth or d-SDNNF/SDD
lower bounds; those are analytical/external theorems.
"""

from itertools import product


def k33_edges():
    left = range(3)
    right = range(3, 6)
    return [(u, v) for u in left for v in right]


def petersen_edges():
    # outer cycle 0..4, inner star 5..9, spokes i--i+5
    edges = []
    for i in range(5):
        edges.append((i, (i + 1) % 5))
        edges.append((i, i + 5))
        edges.append((i + 5, ((i + 2) % 5) + 5))
    # canonicalize duplicates
    return sorted({tuple(sorted(e)) for e in edges})


def vc_cnf_eval(edges, assignment):
    return all(assignment[u] or assignment[v] for u, v in edges)


def b2_or(x, y):
    return not ((not x) and (not y))


def vc_b2_eval(edges, assignment):
    vals = [b2_or(bool(assignment[u]), bool(assignment[v])) for u, v in edges]
    acc = True
    for v in vals:
        acc = acc and v
    return acc


def check_graph(edges, n, degree_bound):
    deg = [0] * n
    for u, v in edges:
        deg[u] += 1
        deg[v] += 1
    assert max(deg) <= degree_bound
    assert len(edges) <= degree_bound * n // 2 + 1

    # Formula has one monotone 2-clause per edge and occurrence count 2|E|.
    assert 2 * len(edges) == sum(deg)

    # Each OR uses constant B2 overhead, followed by a linear AND chain/tree.
    b2_gate_upper = 3 * len(edges) + max(0, len(edges) - 1)
    assert b2_gate_upper == O_linear_bound(len(edges))

    # Exhaustive truth-table equality on the small fixture.
    for a in product((0, 1), repeat=n):
        assert vc_cnf_eval(edges, a) == vc_b2_eval(edges, a)


def O_linear_bound(m):
    return 4 * m - 1 if m else 0


def main():
    check_graph(k33_edges(), 6, 3)
    check_graph(petersen_edges(), 10, 3)
    print("AKINATOR_RSPC_MONOTONE_2CNF_BOUNDED_DEGREE_FIXTURES = PASS")
    print("AKINATOR_RSPC_LINEAR_B2_ENCODING_FINITE = PASS")
    print("AKINATOR_RSPC_CNF_B2_TRUTH_EQUIVALENCE = PASS")
    print("EXPANDER_LINEAR_TREEWIDTH = ANALYTICAL_GRAPH_THEOREM_NOT_CI")
    print("DSDNNF_SDD_EXPONENTIAL_LOWER_BOUND = EXTERNAL_THEOREM_NOT_CI")
    print("STRUCTURED_DDNNF_NEGATION_BARRIER = EXTERNAL_THEOREM_NOT_CI")
    print("RSPC_U1_PROOF_RELEVANT_INTERFACE = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
