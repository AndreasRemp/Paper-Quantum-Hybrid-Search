"""Single-instance run of the hybrid solver on the paper's reference instance:
the first representative selector step, the convergence trajectory, and the
selection-source statistics.

Usage:
    python run_single_instance.py

Writes ../results/single_instance.json and prints a summary.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from astar import optimal_length
from puzzle import GOAL
from solver import solve

INITIAL = "425087316"
PARAMS = dict(lookahead=4, beam_k=16, tabu_window=20, diagnostic_shots=1024,
              max_steps=200, seed_sim=42, seed_transpile=42)


def main():
    result = solve(INITIAL, goal=GOAL, **PARAMS)

    steps = len(result.trace) - 1
    h_start = result.trace[0].h
    h_end = result.trace[-1].h
    counts = result.source_counts
    total_moves = sum(counts.values())

    moves = result.trace[1:]
    print(f"Initial state: {INITIAL}  (h_start = {h_start}, "
          f"optimal length = {optimal_length(INITIAL, GOAL)})")
    print(f"Solved: {result.solved}")
    print(f"Steps: {steps}")
    print(f"h: {h_start} -> {h_end}")
    print("Selection source statistics:")
    for source in ("quantum", "fallback", "forced"):
        n = counts[source]
        pct = 100 * n / total_moves if total_moves else 0.0
        print(f"  {source:9s} {n:4d}  ({pct:.1f}%)")

    payload = result.first_step_payload
    print("\nRepresentative step (step 1):")
    print(f"  candidates: {len(payload['candidates'])}")
    print(f"  marked: {payload['marked']}")
    print(f"  index qubits: {payload['n_bits']}  iterations: {payload['iterations']}")
    print(f"  chosen: {payload['candidates'][payload['chosen_idx']]}")
    print(f"  counts: {payload['counts']}")

    out = {
        "initial": INITIAL,
        "goal": GOAL,
        "params": PARAMS,
        "solved": result.solved,
        "steps": steps,
        "h_start": h_start,
        "h_end": h_end,
        "source_counts": counts,
        "optimal_length": optimal_length(INITIAL, GOAL),
        "selector_hits": sum(1 for s in moves if s.selector_hit),
        "trajectory_h": [s.h for s in result.trace],
        "trajectory_source": [s.source for s in result.trace],
        "trajectory_num_marked": [s.num_marked for s in result.trace],
        "trajectory_num_candidates": [s.num_candidates for s in result.trace],
        "trajectory_states": [s.state for s in result.trace],
        "first_step": {
            "num_candidates": len(payload["candidates"]),
            "marked": payload["marked"],
            "n_bits": payload["n_bits"],
            "num_states": payload["num_states"],
            "iterations": payload["iterations"],
            "chosen_idx": payload["chosen_idx"],
            "chosen_path": payload["candidates"][payload["chosen_idx"]].path,
            "chosen_f": payload["candidates"][payload["chosen_idx"]].f,
            "chosen_h": payload["candidates"][payload["chosen_idx"]].h,
            "chosen_leaf": payload["candidates"][payload["chosen_idx"]].leaf,
            "counts": payload["counts"],
        },
    }

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "single_instance.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {results_dir / 'single_instance.json'}")


if __name__ == "__main__":
    main()
