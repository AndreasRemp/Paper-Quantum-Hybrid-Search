"""Reproduces the paper's Section 4.6 batch evaluation (Table 3): the same
twenty solvable 8-puzzle instances originally reported, re-run with the
verified solver. Per-instance simulation seed is 42 + 100*i for instance i
(1-indexed), matching the paper's "seed offset by 100*i" note.

Usage:
    python run_batch.py

Writes ../results/batch.json and prints a table in the same shape as Table 3.
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from puzzle import GOAL, manhattan_distance
from solver import solve

# The exact twenty instances from the paper's Table 3 (kept fixed for a
# like-for-like comparison; the paper does not record the RNG/seed that
# originally generated them, so they are reused verbatim here).
INSTANCES = [
    "203861457", "248307561", "567034281", "307284651", "380721456",
    "627158340", "376215840", "432851706", "328764015", "320814675",
    "167308452", "816243570", "852307146", "783612405", "032167854",
    "645318072", "561423708", "278105436", "806275413", "630275841",
]

BASE_PARAMS = dict(lookahead=4, beam_k=16, tabu_window=20, diagnostic_shots=1024,
                    max_steps=200, seed_transpile=42)


def main():
    rows = []
    for i, instance in enumerate(INSTANCES, start=1):
        seed_sim = 42 + 100 * i
        result = solve(instance, goal=GOAL, seed_sim=seed_sim, **BASE_PARAMS)
        steps = len(result.trace) - 1
        counts = result.source_counts
        total = sum(counts.values())
        quantum_pct = 100 * counts["quantum"] / total if total else 0.0
        row = {
            "instance": instance,
            "h_start": manhattan_distance(instance, GOAL),
            "seed_sim": seed_sim,
            "steps": steps,
            "quantum_pct": round(quantum_pct, 1),
            "solved": result.solved,
            "source_counts": counts,
        }
        rows.append(row)
        print(f"{instance}  h={row['h_start']:2d}  steps={steps:3d}  "
              f"quantum={quantum_pct:5.1f}%  solved={result.solved}")

    solved_rows = [r for r in rows if r["solved"]]
    n_solved = len(solved_rows)
    mean_h = statistics.mean(r["h_start"] for r in rows)
    std_h = statistics.pstdev(r["h_start"] for r in rows)
    mean_steps = statistics.mean(r["steps"] for r in rows)
    std_steps = statistics.pstdev(r["steps"] for r in rows)
    mean_q = statistics.mean(r["quantum_pct"] for r in rows)
    std_q = statistics.pstdev(r["quantum_pct"] for r in rows)

    print(f"\nSolved: {n_solved}/{len(rows)}")
    print(f"Mean h_start: {mean_h:.1f}  (std {std_h:.1f})")
    print(f"Mean steps: {mean_steps:.1f}  (std {std_steps:.1f})")
    print(f"Mean quantum%: {mean_q:.1f}  (std {std_q:.1f})")

    out = {
        "params": {**BASE_PARAMS, "seed_sim_formula": "42 + 100*i, i=1..20"},
        "rows": rows,
        "summary": {
            "solved": n_solved,
            "total": len(rows),
            "mean_h_start": round(mean_h, 1),
            "std_h_start": round(std_h, 1),
            "mean_steps": round(mean_steps, 1),
            "std_steps": round(std_steps, 1),
            "mean_quantum_pct": round(mean_q, 1),
            "std_quantum_pct": round(std_q, 1),
        },
    }

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "batch.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {results_dir / 'batch.json'}")


if __name__ == "__main__":
    main()
