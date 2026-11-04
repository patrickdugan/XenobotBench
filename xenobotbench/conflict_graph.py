"""Digital-only goal-preserving abstraction challenge with exact rational scoring.

No biological interfaces, organism design, laboratory actions, network requests,
or remote model calls. This is a calibration oracle for QO-03's graph reduction.
"""
from fractions import Fraction as Q
from itertools import combinations


def graph_case(n, edges):
    if type(n) is not int or n < 1:
        raise ValueError("positive number of vertices required")
    canonical = set()
    for pair in edges:
        if len(pair) != 2:
            raise ValueError("each edge must have two endpoints")
        u, v = pair
        if (type(u) is not int or type(v) is not int or
                not 0 <= u < n or not 0 <= v < n or u == v):
            raise ValueError("invalid graph edge")
        canonical.add(tuple(sorted((u, v))))
    return {
        "kind": "synthetic_graph_hit_hold",
        "vertices": n,
        "edges": tuple(sorted(canonical)),
        "goal": n,
        "state_bits": 2,
        "tv_threshold": "1/4",
    }


def _rate(action_edge, state):
    u, v = action_edge
    return Q(0) if state == u else Q(1) if state == v else Q(1, 2)


def score_partition(case, labels):
    """Evaluate macrostate labels on every edge-indexed hit/hold action.

    labels: n transient labels followed by goal label, all 0..3.
    The error is the exact minimax one-step total-variation defect.
    """
    n = case["vertices"]
    if len(labels) != n+1 or any(type(c) is not int or c not in range(4)
                                 for c in labels):
        return {"accepted": False, "reason": "invalid two-bit assignment"}
    goal_label = labels[n]
    if goal_label in labels[:n]:
        return {"accepted": False, "reason": "goal readout is not exact"}
    radius = Q(0)
    for action in case["edges"]:
        groups = {}
        for s in range(n):
            groups.setdefault(labels[s], []).append(_rate(action, s))
        radius = max(radius,
                     max(((max(v)-min(v))/2 for v in groups.values()),
                         default=Q(0)))
    return {
        "accepted": radius <= Q(1, 4),
        "tv_defect": str(radius),
        "goal_exact": True,
        "state_bits": 2,
    }


def brute_three_color_oracle(case):
    """Independent exact graph search for tiny public development cases."""
    n = case["vertices"]
    edges = case["edges"]
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    colors = [None] * n
    def search(i):
        if i == n:
            return tuple(colors)
        for c in range(3):
            if any(colors[j] == c for j in neighbors[i] if j < i):
                continue
            colors[i] = c
            r = search(i + 1)
            if r is not None:
                return r
        colors[i] = None
        return None
    found = search(0)
    if found is None:
        return None
    candidate = found + (3,)
    assert score_partition(case, candidate)["accepted"]
    return candidate


def all_four_vertex_cases():
    """64 labelled simple graphs; public harness development material."""
    vertices = range(4)
    possible = tuple(combinations(vertices, 2))
    for mask in range(1 << len(possible)):
        yield graph_case(4, (e for i, e in enumerate(possible)
                              if mask & (1 << i)))
