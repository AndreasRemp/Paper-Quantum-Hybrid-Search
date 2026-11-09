"""Larger benchmark: the hybrid solver and its ideal classical counterpart on
200 random solvable 8-puzzle instances.

The instances are generated from a fixed seed (uniform random permutations of
the tiles, rejecting unsolvable ones, duplicates, the goal, and the twenty
instances of run_batch.py). Instance i uses simulation seed 100000 + i for both
selectors, so the comparison is paired. The quantum selector draws the index
from the Grover circuit with one measurement per step; the classical selector
draws it uniformly from the marked set. Everything else is identical.

Usage:
    python run_large_benchmark.py [--workers W]

Writes ../results/large_benchmark.json.
"""

import argparse
import json
import math
import random
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from astar import optimal_length
from puzzle import GOAL, is_solvable, manhattan_distance
from run_batch import BASE_PARAMS, INSTANCES as BATCH_INSTANCES
from solver import solve

N_INSTANCES = 200
INSTANCE_SEED = 2026
SIM_SEED_BASE = 100000


def make_instances():
    rng = random.Random(INSTANCE_SEED)
    seen = set(BATCH_INSTANCES) | {GOAL}
    out = []
    while len(out) < N_INSTANCES:
        tiles = list("012345678")
        rng.shuffle(tiles)
        s = "".join(tiles)
        if s in seen or not is_solvable(s):
            continue
        seen.add(s)
        out.append(s)
    return out


def run_one(args):
    i, instance = args
    seed_sim = SIM_SEED_BASE + i
    row = {"i": i, "instance": instance, "h_start": manhattan_distance(instance, GOAL),
           "optimal_length": optimal_length(instance, GOAL)}
    for name, decision in (("quantum", "single_shot"), ("classical", "classical")):
        r = solve(instance, goal=GOAL, seed_sim=seed_sim, capture_first_step=False,
                  decision=decision, **BASE_PARAMS)
        moves = r.trace[1:]
        row[name] = {
            "solved": r.solved,
            "steps": len(r.trace) - 1,
            "h_end": r.trace[-1].h,
            "selector_hits": sum(1 for s in moves if s.selector_hit),
            "selector_draws": len(moves),
            "p_marked_sum": round(sum(s.p_marked for s in moves), 6),
            "p_hit_sum": round(sum(s.p_hit for s in moves), 6),
            "fallback": r.source_counts["fallback"],
            "forced": r.source_counts["forced"],
        }
    return row


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def mcnemar_exact(b, c):
    """Two-sided exact McNemar p from the discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def summarize(rows, name):
    sol = [r for r in rows if r[name]["solved"]]
    lo, hi = wilson(len(sol), len(rows))
    draws = sum(r[name]["selector_draws"] for r in rows)
    return {
        "solved": len(sol),
        "total": len(rows),
        "solve_rate": round(len(sol) / len(rows), 4),
        "wilson95": [round(lo, 4), round(hi, 4)],
        "mean_steps_all": round(statistics.mean(r[name]["steps"] for r in rows), 1),
        "mean_steps_solved": round(statistics.mean(r[name]["steps"] for r in sol), 1),
        "median_steps_solved": statistics.median(r[name]["steps"] for r in sol),
        "mean_steps_over_optimal_solved": round(
            sum(r[name]["steps"] for r in sol) / sum(r["optimal_length"] for r in sol), 2),
        "selector_hit_pct": round(100 * sum(r[name]["selector_hits"] for r in rows) / draws, 1),
        "selector_theory_pct": round(100 * sum(r[name]["p_marked_sum"] for r in rows) / draws, 1),
        "selector_expected_pct": round(100 * sum(r[name]["p_hit_sum"] for r in rows) / draws, 1),
    }


def sign_test_p(positive, negative):
    """Two-sided exact sign test p from the counts of positive and negative differences."""
    n = positive + negative
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(positive, negative) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def paired_solve_difference(rows):
    """Difference in solve rate (Grover minus classical) with a Wald 95% interval for
    paired proportions, from the discordant counts b and c."""
    n = len(rows)
    b = sum(1 for r in rows if r["quantum"]["solved"] and not r["classical"]["solved"])
    c = sum(1 for r in rows if r["classical"]["solved"] and not r["quantum"]["solved"])
    diff = (b - c) / n
    se = math.sqrt(b + c - (b - c) ** 2 / n) / n
    return {"difference_pp": round(100 * diff, 1),
            "wald95_pp": [round(100 * (diff - 1.959964 * se), 1), round(100 * (diff + 1.959964 * se), 1)]}


def paired_steps(rows):
    """Paired comparison of path lengths on instances solved by both selectors."""
    both = [r for r in rows if r["quantum"]["solved"] and r["classical"]["solved"]]
    d = [r["quantum"]["steps"] - r["classical"]["steps"] for r in both]
    rng = random.Random(1)
    boots = sorted(statistics.mean(rng.choice(d) for _ in d) for _ in range(10000))
    return {
        "n_both_solved": len(both),
        "mean_difference_quantum_minus_classical": round(statistics.mean(d), 1),
        "bootstrap95": [round(boots[249], 1), round(boots[9749], 1)],
        "quantum_longer": sum(1 for x in d if x > 0),
        "classical_longer": sum(1 for x in d if x < 0),
        "sign_test_p": round(sign_test_p(sum(1 for x in d if x > 0), sum(1 for x in d if x < 0)), 4),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--reuse", action="store_true",
                    help="recompute the summary from the saved per-instance rows")
    args = ap.parse_args()

    results_dir = Path(__file__).resolve().parent.parent / "results"
    if args.reuse:
        with open(results_dir / "large_benchmark.json", encoding="utf-8") as f:
            rows = json.load(f)["rows"]
    else:
        instances = make_instances()
        jobs = list(enumerate(instances, start=1))
        rows = []
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for k, row in enumerate(pool.map(run_one, jobs, chunksize=1), start=1):
                rows.append(row)
                if k % 10 == 0:
                    print(f"{k}/{len(jobs)} instances done", flush=True)

    q, c = summarize(rows, "quantum"), summarize(rows, "classical")
    b = sum(1 for r in rows if r["quantum"]["solved"] and not r["classical"]["solved"])
    cc = sum(1 for r in rows if r["classical"]["solved"] and not r["quantum"]["solved"])
    summary = {
        "n_instances": len(rows),
        "mean_h_start": round(statistics.mean(r["h_start"] for r in rows), 1),
        "mean_optimal_length": round(statistics.mean(r["optimal_length"] for r in rows), 1),
        "quantum": q,
        "classical": c,
        "only_quantum_solved": b,
        "only_classical_solved": cc,
        "mcnemar_exact_p": round(mcnemar_exact(b, cc), 4),
        "paired_solve_difference": paired_solve_difference(rows),
        "paired_steps": paired_steps(rows),
    }
    print(json.dumps(summary, indent=2))

    out = {"params": {**BASE_PARAMS, "instance_seed": INSTANCE_SEED,
                      "sim_seed": f"{SIM_SEED_BASE} + i, i = 1..{N_INSTANCES}"},
           "summary": summary, "rows": rows}
    with open(results_dir / "large_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {results_dir / 'large_benchmark.json'}")


if __name__ == "__main__":
    main()
