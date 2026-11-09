"""Batch evaluation: the hybrid solver on twenty fixed, randomly generated
solvable 8-puzzle instances (the paper's batch-results table). The simulation
seed for instance i (1-indexed) is 42 + 100*i.

Usage:
    python run_batch.py

Writes ../results/batch.json and prints one line per instance and a summary.
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from astar import optimal_length
from puzzle import GOAL, manhattan_distance
from solver import solve

INSTANCES = [
    "203861457", "248307561", "567034281", "307284651", "380721456",
    "627158340", "376215840", "432851706", "328764015", "320814675",
    "167308452", "816243570", "852307146", "783612405", "032167854",
    "645318072", "561423708", "278105436", "806275413", "630275841",
]

BASE_PARAMS = dict(lookahead=4, beam_k=16, tabu_window=20, diagnostic_shots=1024,
                   max_steps=200, seed_transpile=42)


def summarize_run(instance, result, seed_sim):
    steps = len(result.trace) - 1
    counts = result.source_counts
    total = sum(counts.values())
    moves = result.trace[1:]
    return {
        "instance": instance,
        "h_start": manhattan_distance(instance, GOAL),
        "optimal_length": optimal_length(instance, GOAL),
        "seed_sim": seed_sim,
        "steps": steps,
        "quantum_pct": round(100 * counts["quantum"] / total, 1) if total else 0.0,
        "solved": result.solved,
        "h_end": result.trace[-1].h,
        "source_counts": counts,
        "selector_hits": sum(1 for s in moves if s.selector_hit),
        "selector_draws": len(moves),
        "p_marked_sum": round(sum(s.p_marked for s in moves), 6),
        "p_hit_sum": round(sum(s.p_hit for s in moves), 6),
    }


def main():
    rows = []
    for i, instance in enumerate(INSTANCES, start=1):
        seed_sim = 42 + 100 * i
        result = solve(instance, goal=GOAL, seed_sim=seed_sim, **BASE_PARAMS)
        row = summarize_run(instance, result, seed_sim)
        rows.append(row)
        print(f"{instance}  h={row['h_start']:2d}  opt={row['optimal_length']:2d}  "
              f"steps={row['steps']:3d}  quantum={row['quantum_pct']:5.1f}%  "
              f"solved={row['solved']}")

    solved_rows = [r for r in rows if r["solved"]]
    mean_h = statistics.mean(r["h_start"] for r in rows)
    std_h = statistics.pstdev(r["h_start"] for r in rows)
    mean_steps = statistics.mean(r["steps"] for r in rows)
    std_steps = statistics.pstdev(r["steps"] for r in rows)
    mean_q = statistics.mean(r["quantum_pct"] for r in rows)
    std_q = statistics.pstdev(r["quantum_pct"] for r in rows)
    draws = sum(r["selector_draws"] for r in rows)
    hits = sum(r["selector_hits"] for r in rows)
    p_sum = sum(r["p_marked_sum"] for r in rows)
    p_hit_sum = sum(r["p_hit_sum"] for r in rows)

    print(f"\nSolved: {len(solved_rows)}/{len(rows)}")
    print(f"Mean h_start: {mean_h:.1f}  (std {std_h:.1f})")
    print(f"Mean steps: {mean_steps:.1f}  (std {std_steps:.1f})")
    print(f"Mean quantum%: {mean_q:.1f}  (std {std_q:.1f})")
    print(f"Selector draws on a minimum-cost candidate: {hits}/{draws} "
          f"({100 * hits / draws:.1f}%; theory {100 * p_sum / draws:.1f}%)")

    out = {
        "params": {**BASE_PARAMS, "seed_sim_formula": "42 + 100*i, i=1..20"},
        "rows": rows,
        "summary": {
            "solved": len(solved_rows),
            "total": len(rows),
            "mean_h_start": round(mean_h, 1),
            "std_h_start": round(std_h, 1),
            "mean_steps": round(mean_steps, 1),
            "std_steps": round(std_steps, 1),
            "mean_quantum_pct": round(mean_q, 1),
            "std_quantum_pct": round(std_q, 1),
            "selector_hit_pct": round(100 * hits / draws, 1),
            "selector_theory_pct": round(100 * p_sum / draws, 1),
            "selector_expected_pct": round(100 * p_hit_sum / draws, 1),
            "mean_optimal_length": round(statistics.mean(r["optimal_length"] for r in rows), 1),
            "mean_steps_solved": round(statistics.mean(r["steps"] for r in solved_rows), 1),
        },
    }

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "batch.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {results_dir / 'batch.json'}")


if __name__ == "__main__":
    main()
