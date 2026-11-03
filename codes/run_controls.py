"""Control experiments on the paper's twenty batch instances.

  1. decision rule  - the per-step decision taken as the majority outcome of a
                      1024-shot run instead of a single projective measurement;
  2. classical      - the Grover selector replaced by its ideal classical
                      counterpart, a uniform random choice among the marked
                      candidates (same lookahead, tabu list, and fallback);
  3. tabu window    - the majority-vote rule re-run with tau in {20, 40, 80}.

Each configuration uses the same instances and the same per-instance seeds as
run_batch.py, so the single-shot row reproduces batch.json.

Usage:
    python run_controls.py

Writes ../results/controls.json.
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from puzzle import GOAL
from run_batch import BASE_PARAMS, INSTANCES
from solver import solve

CONFIGS = [
    ("single_shot", "single_shot", 20),
    ("classical", "classical", 20),
    ("majority_tau20", "majority", 20),
    ("majority_tau40", "majority", 40),
    ("majority_tau80", "majority", 80),
]


def run_config(decision, tabu_window):
    rows = []
    for i, instance in enumerate(INSTANCES, start=1):
        params = {**BASE_PARAMS, "tabu_window": tabu_window}
        result = solve(instance, goal=GOAL, seed_sim=42 + 100 * i,
                       capture_first_step=False, decision=decision, **params)
        rows.append({"instance": instance, "steps": len(result.trace) - 1,
                     "solved": result.solved})
    solved = [r for r in rows if r["solved"]]
    return {
        "decision": decision,
        "tabu_window": tabu_window,
        "solved": len(solved),
        "total": len(rows),
        "mean_steps_all": round(statistics.mean(r["steps"] for r in rows), 1),
        "mean_steps_solved": round(statistics.mean(r["steps"] for r in solved), 1) if solved else None,
        "rows": rows,
    }


def main():
    out = {}
    for name, decision, tau in CONFIGS:
        out[name] = run_config(decision, tau)
        r = out[name]
        print(f"{name:16s} solved {r['solved']}/{r['total']}  "
              f"mean steps (all) {r['mean_steps_all']}  (solved) {r['mean_steps_solved']}")

    results_dir = Path(__file__).resolve().parent.parent / "results"
    with open(results_dir / "controls.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {results_dir / 'controls.json'}")


if __name__ == "__main__":
    main()
