"""8-puzzle state representation: solvability, moves, and the Manhattan distance heuristic.

States are 9-character strings over "0".."8" (row-major, "0" = blank), matching
the paper's notation (e.g. "425087316").
"""

GOAL = "123456780"


def is_solvable(state: str) -> bool:
    tiles = [int(ch) for ch in state if ch != "0"]
    inversions = sum(
        1
        for i in range(len(tiles))
        for j in range(i + 1, len(tiles))
        if tiles[i] > tiles[j]
    )
    return inversions % 2 == 0


def neighbors(state: str):
    """Yield (move, next_state) pairs. Moves are named by the direction the blank moves."""
    blank = state.index("0")
    row, col = divmod(blank, 3)

    def swap(i: int, j: int) -> str:
        chars = list(state)
        chars[i], chars[j] = chars[j], chars[i]
        return "".join(chars)

    if row > 0:
        yield "U", swap(blank, blank - 3)
    if row < 2:
        yield "D", swap(blank, blank + 3)
    if col > 0:
        yield "L", swap(blank, blank - 1)
    if col < 2:
        yield "R", swap(blank, blank + 1)


def manhattan_distance(state: str, goal: str = GOAL) -> int:
    goal_pos = {ch: i for i, ch in enumerate(goal)}
    total = 0
    for i, ch in enumerate(state):
        if ch == "0":
            continue
        gi = goal_pos[ch]
        r1, c1 = divmod(i, 3)
        r2, c2 = divmod(gi, 3)
        total += abs(r1 - r2) + abs(c1 - c2)
    return total
