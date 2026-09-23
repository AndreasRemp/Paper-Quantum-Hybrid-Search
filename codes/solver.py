"""The hybrid Grover lookahead solver -- Algorithm 1 in the paper.

Faithful reconstruction from the paper's formal description (Section 3.2 /
Algorithm 1), not a copy of the exploratory notebook code: the notebook's
`hybrid_grover_8puzzle` cell has no tabu window (an ever-growing `visited`
set instead) and never records which of quantum-selection / classical-fallback
/ forced-move produced each step, which is exactly the statistic Table 2 of
the paper reports. This module adds both, matching Algorithm 1 line-for-line.

Decision rule: Algorithm 1's pseudocode reads "Measure index register -> j"
-- a single projective measurement, not "run `shots` repetitions and take the
most frequent outcome". Taking the mode of a fixed-seed multi-shot circuit
makes the decision at a given (state, marked-set) configuration deterministic,
which lets the solver settle into self-reinforcing cycles a finite tabu window
cannot break (confirmed experimentally: increasing tau from 20 to 80 did not
resolve stalling on an affected instance). Each step here instead performs a
single-shot measurement with a step-advancing seed (still fully deterministic
and reproducible given `seed_sim`, since it derives from `seed_sim` and the
step counter). The paper's multi-shot histograms (Figures 2 and the second
worked example) remain multi-shot -- they are diagnostic snapshots of the
distribution at that step, not the decision itself; see `first_step_payload`.
"""

from collections import deque
from dataclasses import dataclass, field

from lookahead import lookahead_candidates
from puzzle import GOAL, is_solvable, manhattan_distance, neighbors
from quantum_selector import grover_select, ranked_indices_from_counts


def _first_move_successor(state: str, path: str) -> str:
    move = path[0]
    return dict(neighbors(state))[move]


@dataclass
class StepRecord:
    step: int
    state: str
    h: int
    source: str | None = None  # "quantum" | "fallback" | "forced" | None (initial state)


@dataclass
class SolveResult:
    final_state: str
    solved: bool
    trace: list = field(default_factory=list)          # list[StepRecord]
    source_counts: dict = field(default_factory=dict)   # {"quantum": n, "fallback": n, "forced": n}
    first_step_payload: dict | None = None              # diagnostics for the representative step


def solve(initial: str, goal: str = GOAL, lookahead: int = 4, beam_k: int = 16,
          tabu_window: int = 20, diagnostic_shots: int = 1024, max_steps: int = 200,
          seed_sim: int = 42, seed_transpile: int = 42,
          capture_first_step: bool = True) -> SolveResult:
    if not is_solvable(initial):
        raise ValueError(f"State {initial!r} is not solvable (odd inversion count)")

    state = initial
    tabu = deque([initial], maxlen=tabu_window)
    tabu_set = set(tabu)

    trace = [StepRecord(step=0, state=state, h=manhattan_distance(state, goal))]
    source_counts = {"quantum": 0, "fallback": 0, "forced": 0}
    first_step_payload = None

    t = 0
    while state != goal and t < max_steps:
        candidates = lookahead_candidates(state, lookahead, beam_k, goal)
        if not candidates:
            break  # no legal moves; should not happen on a solvable, non-goal state

        f_min = candidates[0].f
        marked = [i for i, c in enumerate(candidates) if c.f == f_min]

        step_seed = seed_sim * 1000 + t  # deterministic but distinct per step

        decision_counts, n_bits, num_states, iters = grover_select(
            len(candidates), marked, shots=1,
            seed_sim=step_seed, seed_transpile=seed_transpile,
        )
        quantum_choice = ranked_indices_from_counts(decision_counts, len(candidates))[0]
        quantum_successor = _first_move_successor(state, candidates[quantum_choice].path)

        if quantum_successor not in tabu_set:
            chosen_idx = quantum_choice
            source = "quantum"
        else:
            fallback_idx = None
            for i, c in enumerate(candidates):
                if _first_move_successor(state, c.path) not in tabu_set:
                    fallback_idx = i
                    break
            if fallback_idx is not None:
                chosen_idx = fallback_idx
                source = "fallback"
            else:
                chosen_idx = 0  # every successor is tabu; forced to move anyway
                source = "forced"

        if capture_first_step and first_step_payload is None:
            diag_counts, _, _, _ = grover_select(
                len(candidates), marked, shots=diagnostic_shots,
                seed_sim=step_seed, seed_transpile=seed_transpile,
            )
            first_step_payload = {
                "state": state,
                "candidates": candidates,
                "marked": marked,
                "counts": diag_counts,
                "n_bits": n_bits,
                "num_states": num_states,
                "iterations": iters,
                "chosen_idx": chosen_idx,
                "source": source,
            }

        next_state = _first_move_successor(state, candidates[chosen_idx].path)
        state = next_state
        tabu.append(state)
        tabu_set = set(tabu)
        t += 1

        source_counts[source] += 1
        trace.append(StepRecord(step=t, state=state, h=manhattan_distance(state, goal), source=source))

    return SolveResult(
        final_state=state,
        solved=(state == goal),
        trace=trace,
        source_counts=source_counts,
        first_step_payload=first_step_payload,
    )
