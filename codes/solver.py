"""The hybrid Grover lookahead solver (Algorithm 1 in the paper).

Each step runs the classical lookahead, marks the minimum-cost candidates,
and draws one candidate index from a Grover selector circuit. If the selected
successor state is on the tabu list, a classical fallback picks the
best-ranked non-tabu candidate instead. Every executed move is attributed to
one of three sources: the selector ("quantum"), the classical fallback
("fallback"), or a forced move ("forced", when every successor is tabu).

Decision rule. Algorithm 1 specifies "Measure index register -> j": a single
projective measurement. Each step therefore runs the circuit with one shot,
seeded with `seed_sim * 1000 + step`, so a whole run is reproducible from
`seed_sim` while every step draws independently. The `decision` argument
exposes two alternatives for the control experiments in `run_controls.py`:

  "single_shot"  (default) one projective measurement per step.
  "majority"     the most frequent outcome of a 1024-shot run. For a fixed
                 simulator seed this is a deterministic function of the
                 (state, marked-set) configuration.
  "classical"    uniform random choice among the marked candidates; replaces
                 the quantum circuit by the ideal selector it approximates.

The 1024-shot snapshot stored in `first_step_payload` is a diagnostic of the
output distribution at the first step; it never influences the decision.
"""

import random
from collections import deque
from dataclasses import dataclass, field

from lookahead import lookahead_candidates
from puzzle import GOAL, is_solvable, manhattan_distance, neighbors
from quantum_selector import (grover_select, ranked_indices_from_counts,
                              success_probability)

DECISIONS = ("single_shot", "majority", "classical")


def _first_move_successor(state: str, path: str) -> str:
    move = path[0]
    return dict(neighbors(state))[move]


@dataclass
class StepRecord:
    step: int
    state: str
    h: int
    source: str | None = None  # "quantum" | "fallback" | "forced" | None (initial state)
    num_candidates: int | None = None
    num_marked: int | None = None
    selector_hit: bool | None = None   # selector's draw was a minimum-cost candidate
    p_marked: float | None = None      # theoretical probability of a marked outcome


@dataclass
class SolveResult:
    final_state: str
    solved: bool
    trace: list = field(default_factory=list)          # list[StepRecord]
    source_counts: dict = field(default_factory=dict)   # {"quantum": n, "fallback": n, "forced": n}
    first_step_payload: dict | None = None              # diagnostics for the first step


def solve(initial: str, goal: str = GOAL, lookahead: int = 4, beam_k: int = 16,
          tabu_window: int = 20, diagnostic_shots: int = 1024, max_steps: int = 200,
          seed_sim: int = 42, seed_transpile: int = 42,
          capture_first_step: bool = True, decision: str = "single_shot") -> SolveResult:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {DECISIONS}, got {decision!r}")
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
            break  # no legal moves; cannot happen on a solvable, non-goal state

        f_min = candidates[0].f
        marked = [i for i, c in enumerate(candidates) if c.f == f_min]

        step_seed = seed_sim * 1000 + t  # deterministic but distinct per step

        if decision == "classical":
            quantum_choice = random.Random(step_seed).choice(marked)
            n_bits, num_states, iters, p_marked = None, None, None, 1.0
        else:
            shots = 1 if decision == "single_shot" else diagnostic_shots
            decision_counts, n_bits, num_states, iters = grover_select(
                len(candidates), marked, shots=shots,
                seed_sim=step_seed, seed_transpile=seed_transpile,
            )
            quantum_choice = ranked_indices_from_counts(decision_counts, len(candidates))[0]
            p_marked = success_probability(num_states, len(marked), iters)
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

        if capture_first_step and first_step_payload is None and decision != "classical":
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

        state = _first_move_successor(state, candidates[chosen_idx].path)
        tabu.append(state)
        tabu_set = set(tabu)
        t += 1

        source_counts[source] += 1
        trace.append(StepRecord(
            step=t, state=state, h=manhattan_distance(state, goal), source=source,
            num_candidates=len(candidates), num_marked=len(marked),
            selector_hit=quantum_choice in marked, p_marked=p_marked,
        ))

    return SolveResult(
        final_state=state,
        solved=(state == goal),
        trace=trace,
        source_counts=source_counts,
        first_step_payload=first_step_payload,
    )
