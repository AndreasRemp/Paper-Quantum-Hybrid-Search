"""Classical lookahead stage (paper Section 3.2, "Classical stage").

Bounded breadth-first expansion to a fixed depth L, with reverse-move pruning
(a move that immediately undoes the previous move is never taken) and
shortest-path deduplication (a state already reached at an equal or shorter
depth along another branch is not re-queued). Only leaves at exactly depth L
are scored and returned as candidates. This matches the paper's Section 4.3
worked example (14 candidates at L=4 from state "425087316").
"""

from collections import deque

from puzzle import GOAL, manhattan_distance, neighbors

REVERSE = {"U": "D", "D": "U", "L": "R", "R": "L"}


class Candidate:
    __slots__ = ("f", "h", "path", "leaf")

    def __init__(self, f: int, h: int, path: str, leaf: str):
        self.f = f
        self.h = h
        self.path = path
        self.leaf = leaf

    def sort_key(self):
        return (self.f, self.h, self.path)

    def __repr__(self):
        return f"Candidate(f={self.f}, h={self.h}, path={self.path!r}, leaf={self.leaf!r})"


def lookahead_candidates(state: str, depth: int, beam_k: int, goal: str = GOAL):
    """Expand `state` to `depth` moves and return up to `beam_k` sorted Candidates."""
    queue = deque([(state, "", None)])
    best_depth_seen = {state: 0}
    leaves = []

    while queue:
        current, path, last_move = queue.popleft()
        current_depth = len(path)

        if current_depth == depth:
            h = manhattan_distance(current, goal)
            g = current_depth
            leaves.append(Candidate(f=g + h, h=h, path=path, leaf=current))
            continue

        for move, nxt in neighbors(current):
            if last_move is not None and move == REVERSE[last_move]:
                continue
            next_depth = current_depth + 1
            if nxt in best_depth_seen and best_depth_seen[nxt] <= next_depth:
                continue
            best_depth_seen[nxt] = next_depth
            queue.append((nxt, path + move, move))

    leaves.sort(key=Candidate.sort_key)
    return leaves[:beam_k]
