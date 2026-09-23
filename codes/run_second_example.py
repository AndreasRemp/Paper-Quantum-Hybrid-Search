"""Second worked example for the paper's Section 4.4-4.5, demonstrating the
selection mechanism across a different branching and marked-set structure
than the first example.

This uses step 21 of the verified single-instance trajectory
(../results/single_instance.json): state "310452786", blank tile at a
corner position (geometric branching factor 2, versus the first example's
edge position, branching factor 3), where beam truncation actually
engages (16 candidates, i.e. the full beam width k=16, versus 14 in the
first example) and the marked set is much larger (|M|=5 versus 2), giving
a different qubit/iteration regime.

The diagnostic histogram uses the same step-seed convention as the solver's
own per-step decision (seed_sim*1000 + step), so it reflects the exact
distribution the step-21 single-shot decision was actually drawn from.

Usage:
    python run_second_example.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lookahead import lookahead_candidates
from puzzle import GOAL
from quantum_selector import grover_select, ranked_indices_from_counts

STATE = "310452786"  # step 21 of the results/single_instance.json trajectory
STEP = 21
PARAMS = dict(lookahead=4, beam_k=16, diagnostic_shots=1024, seed_sim=42, seed_transpile=42)


def main():
    candidates = lookahead_candidates(STATE, PARAMS["lookahead"], PARAMS["beam_k"], GOAL)
    f_min = candidates[0].f
    marked = [i for i, c in enumerate(candidates) if c.f == f_min]

    step_seed = PARAMS["seed_sim"] * 1000 + STEP

    # The actual decision, exactly as solve() makes it: a single projective
    # measurement (shots=1) at this step's seed.
    decision_counts, n_bits, num_states, iterations = grover_select(
        len(candidates), marked, shots=1,
        seed_sim=step_seed, seed_transpile=PARAMS["seed_transpile"],
    )
    chosen_idx = ranked_indices_from_counts(decision_counts, len(candidates))[0]
    chosen = candidates[chosen_idx]

    # A separate multi-shot snapshot of the same circuit/seed, for the
    # illustrative histogram only (not the decision).
    counts, _, _, _ = grover_select(
        len(candidates), marked, shots=PARAMS["diagnostic_shots"],
        seed_sim=step_seed, seed_transpile=PARAMS["seed_transpile"],
    )

    print(f"State: {STATE}  (blank at index {STATE.index('0')}, a corner position)")
    print(f"Candidates: {len(candidates)}  Marked: {marked} (|M|={len(marked)})")
    print(f"Index qubits: {n_bits}  N: {num_states}  Grover iterations: {iterations}")
    print(f"Chosen (single-shot decision): idx={chosen_idx} f={chosen.f} h={chosen.h} path={chosen.path} leaf={chosen.leaf}")
    print(f"Diagnostic {PARAMS['diagnostic_shots']}-shot counts: {counts}")

    out = {
        "state": STATE,
        "num_candidates": len(candidates),
        "marked": marked,
        "n_bits": n_bits,
        "num_states": num_states,
        "iterations": iterations,
        "chosen_idx": chosen_idx,
        "chosen_f": chosen.f,
        "chosen_h": chosen.h,
        "chosen_path": chosen.path,
        "chosen_leaf": chosen.leaf,
        "counts": counts,
    }
    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "second_example.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {results_dir / 'second_example.json'}")


if __name__ == "__main__":
    main()
