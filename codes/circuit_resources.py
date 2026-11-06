"""Resource counts for the Grover selector circuit.

Transpiles the selector to the {CX, RZ, SX, X} basis (all-to-all connectivity,
optimization level 1, fixed seed) for every marked-set size |M| and both
oracle constructions, and reports depth, CX count and total gate count, for the
paper's beam width k = 16 (n = 4 index qubits) and, to illustrate scaling,
k = 64 (n = 6).

  direct  one multi-controlled gate per marked index (cost grows with |M|);
  prefix  the block decomposition of {0, ..., |M|-1} (at most n gates).

The marked indices are 0..|M|-1, matching the sorted candidate list (a marked
set is always a prefix). Both oracles implement the same unitary, so the
selector's output distribution is the same; only the circuit cost differs.

Usage:
    python circuit_resources.py

Writes ../results/circuit_resources.json.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qiskit import transpile

from quantum_selector import build_circuit

BASIS = ["cx", "rz", "sx", "x"]


def resources(beam_width, num_marked, oracle):
    qc, n_bits, num_states, iterations = build_circuit(
        beam_width, list(range(num_marked)), oracle=oracle)
    qc.remove_final_measurements()
    t = transpile(qc, basis_gates=BASIS, optimization_level=1, seed_transpiler=42)
    ops = t.count_ops()
    return {
        "oracle": oracle,
        "beam_width": beam_width,
        "num_marked": num_marked,
        "qubits": n_bits + 1,
        "grover_iterations": iterations,
        "depth": t.depth(),
        "cx": int(ops.get("cx", 0)),
        "gates": int(sum(ops.values())),
    }


def main():
    rows = []
    for oracle in ("direct", "prefix"):
        for k in (16, 64):
            for m in range(1, k + 1):
                rows.append(resources(k, m, oracle))
    for r in rows:
        if r["beam_width"] == 16 and r["num_marked"] <= 8:
            print(r)
    results_dir = Path(__file__).resolve().parent.parent / "results"
    with open(results_dir / "circuit_resources.json", "w", encoding="utf-8") as f:
        json.dump({"basis_gates": BASIS, "optimization_level": 1, "rows": rows}, f, indent=2)
    print(f"Wrote {results_dir / 'circuit_resources.json'}")


if __name__ == "__main__":
    main()
