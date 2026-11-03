"""Reference classical solver: A* with the Manhattan distance heuristic.

Used only to report the optimal solution length of each benchmark instance, so
the hybrid solver's path lengths can be compared with the optimum. The
Manhattan distance is admissible and consistent, so A* returns a shortest path.
"""

import heapq

from puzzle import GOAL, manhattan_distance, neighbors


def optimal_length(initial: str, goal: str = GOAL) -> int:
    """Length (number of blank moves) of a shortest solution from `initial`."""
    frontier = [(manhattan_distance(initial, goal), 0, initial)]
    best_g = {initial: 0}
    while frontier:
        _, g, state = heapq.heappop(frontier)
        if state == goal:
            return g
        if g > best_g[state]:
            continue
        for _, nxt in neighbors(state):
            ng = g + 1
            if ng < best_g.get(nxt, 1 << 30):
                best_g[nxt] = ng
                heapq.heappush(frontier, (ng + manhattan_distance(nxt, goal), ng, nxt))
    raise ValueError("goal unreachable")
