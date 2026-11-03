"""Second worked example of the paper: the selection mechanism on a different
branching and marked-set structure than the first example.

The example is the second solver step of the reference trajectory
(../results/single_instance.json), taken at state s_1 = "425387016". The blank
tile is at a corner position (geometric branching factor 2, versus the first
example's edge position, branching factor 3), beam truncation is active (16
candidates, i.e. the full beam width k = 16, versus 14 in the first example),
and the marked set is larger (|M| = 4 versus 2), which gives a different
iteration regime (r = 1 versus 2).

The diagnostic histogram uses the same seed convention as the solver's own
per-step decision (seed_sim * 1000 + t, with t the 0-indexed step), so it
reflects the distribution that step's single-shot decision was drawn from.

Usage:
    python run_second_example.py      (run run_single_instance.py first)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lookahead import lookahead_candidates
from puzzle import GOAL
from quantum_selector import grover_select, ranked_indices_from_counts, success_probability

T = 1  # 0-indexed decision step; the decision is taken at state s_T
PARAMS = dict(lookahead=4, beam_k=16, diagnostic_shots=1024, seed_sim=42, seed_transpile=42)
RESULTS = Path(__file__).resolve().parent.parent / "results"


def main():
    with open(RESULTS / "single_instance.json", encoding="utf-8") as f:
        state = json.load(f)["trajectory_states"][T]

    candidates = lookahead_candidates(state, PARAMS["lookahead"], PARAMS["beam_k"], GOAL)
    f_min = candidates[0].f
    marked = [i for i, c in enumerate(candidates) if c.f == f_min]

    step_seed = PARAMS["seed_sim"] * 1000 + T

    # The actual decision, exactly as solve() makes it: one projective measurement.
    decision_counts, n_bits, num_states, iterations = grover_select(
        len(candidates), marked, shots=1,
        seed_sim=step_seed, seed_transpile=PARAMS["seed_transpile"],
    )
    chosen_idx = ranked_indices_from_counts(decision_counts, len(candidates))[0]
    chosen = candidates[chosen_idx]

    # A separate multi-shot snapshot of the same circuit and seed, for the
    # histogram only (not the decision).
    counts, _, _, _ = grover_select(
        len(candidates), marked, shots=PARAMS["diagnostic_shots"],
        seed_sim=step_seed, seed_transpile=PARAMS["seed_transpile"],
    )
    p_theory = success_probability(num_states, len(marked), iterations)
    on_marked = sum(c for b, c in counts.items() if int(b.replace(" ", "")[::-1], 2) in marked)

    print(f"State: {state}  (blank at index {state.index('0')})")
    print(f"Candidates: {len(candidates)}  Marked: {marked} (|M|={len(marked)})")
    print(f"Index qubits: {n_bits}  N: {num_states}  Grover iterations: {iterations}")
    print(f"Theoretical P(marked) = {p_theory:.4f}; measured {on_marked}/{PARAMS['diagnostic_shots']}")
    print(f"Chosen (single-shot decision): idx={chosen_idx} f={chosen.f} h={chosen.h} "
          f"path={chosen.path} leaf={chosen.leaf}")
    print(f"Diagnostic {PARAMS['diagnostic_shots']}-shot counts: {counts}")

    out = {
        "step": T + 1,
        "state": state,
        "num_candidates": len(candidates),
        "marked": marked,
        "n_bits": n_bits,
        "num_states": num_states,
        "iterations": iterations,
        "p_marked_theory": round(p_theory, 6),
        "shots_on_marked": on_marked,
        "chosen_idx": chosen_idx,
        "chosen_f": chosen.f,
        "chosen_h": chosen.h,
        "chosen_path": chosen.path,
        "chosen_leaf": chosen.leaf,
        "counts": counts,
    }
    with open(RESULTS / "second_example.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {RESULTS / 'second_example.json'}")


if __name__ == "__main__":
    main()
