"""Checks of the facts the paper states about the puzzle, the look-ahead, and
the Grover selector. Runs under pytest or directly:

    python test_core.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from astar import optimal_length
from lookahead import lookahead_candidates
from puzzle import GOAL, is_solvable, manhattan_distance, neighbors
from quantum_selector import (build_circuit, decode_index, grover_iterations,
                              grover_select, success_probability)


def test_branching_factors():
    # Blank at a corner = 2 moves, at an edge = 3, at the center = 4.
    expected = [2, 3, 2, 3, 4, 3, 2, 3, 2]
    for pos, b in enumerate(expected):
        tiles = [str(i) for i in range(1, 9)]
        tiles.insert(pos, "0")
        assert len(list(neighbors("".join(tiles)))) == b, pos


def test_goal_and_solvability():
    assert manhattan_distance(GOAL) == 0
    assert is_solvable(GOAL)
    assert not is_solvable("213456780")  # two tiles swapped: odd inversion count
    assert manhattan_distance("425087316") == 15


def test_optimal_length_reference_instance():
    assert optimal_length("425087316") == 23


def test_first_example_lookahead():
    cands = lookahead_candidates("425087316", 4, 16, GOAL)
    assert len(cands) == 14
    f_min = cands[0].f
    assert [i for i, c in enumerate(cands) if c.f == f_min] == [0, 1]
    assert all(len(c.path) == 4 for c in cands)  # g = L for every candidate


def test_iteration_rule():
    assert grover_iterations(16, 1) == 3
    assert grover_iterations(16, 2) == 2
    assert grover_iterations(16, 4) == 1
    assert grover_iterations(16, 7) == 1
    assert grover_iterations(16, 8) == 0    # M = N/2: no iteration
    assert grover_iterations(16, 12) == 0   # M > N/2: no iteration


def test_success_probability():
    assert abs(success_probability(16, 4, 1) - 1.0) < 1e-12          # exact at M/N = 1/4
    assert abs(success_probability(16, 2, 2) - 0.9453) < 1e-3        # first worked example
    assert abs(success_probability(16, 8, 1) - 0.5) < 1e-12          # unchanged at M/N = 1/2
    assert success_probability(16, 10, 1) < 10 / 16                   # lowers it for M/N > 1/2
    assert abs(success_probability(16, 10, 0) - 10 / 16) < 1e-12


def test_circuit_registers():
    qc, n_bits, num_states, iterations = build_circuit(14, [0, 1])
    assert (n_bits, num_states, iterations) == (4, 16, 2)
    assert qc.num_qubits == 5  # four index qubits plus one ancilla


def test_decode_padding_wraps():
    assert decode_index("0111", 14) == 0   # register value 14 -> candidate 0
    assert decode_index("1111", 14) == 1   # register value 15 -> candidate 1
    assert decode_index("1000", 14) == 1   # little-endian: register value 1


def test_selector_matches_theory():
    counts, _, _, _ = grover_select(16, [0, 1, 2, 3], shots=1024, seed_sim=7)
    assert sum(counts.values()) == 1024
    on_marked = sum(c for b, c in counts.items() if int(b[::-1], 2) < 4)
    assert on_marked == 1024  # P = 1 exactly


def test_prefix_oracle_equals_direct_oracle():
    from qiskit.quantum_info import Statevector

    def distribution(num_items, marked, oracle, iterations):
        qc, n_bits, _, _ = build_circuit(num_items, marked, oracle=oracle, iterations=iterations)
        qc.remove_final_measurements()
        return Statevector(qc).probabilities(list(range(n_bits)))

    for n in range(2, 6):
        N = 2 ** n
        for m in range(1, N):
            marked = list(range(m))
            direct = distribution(N, marked, "direct", 2)
            prefix = distribution(N, marked, "prefix", 2)
            assert max(abs(a - b) for a, b in zip(direct, prefix)) < 1e-10, (n, m)
            # gates acting on the ancilla (the last qubit) are the oracle gates
            qc, _, _, _ = build_circuit(N, marked, oracle="prefix", iterations=1)
            ancilla = qc.qubits[n]
            oracle_gates = sum(1 for inst in qc.data
                               if inst.qubits and inst.qubits[-1] == ancilla
                               and inst.operation.name not in ("x", "h", "measure"))
            assert oracle_gates == bin(m).count("1") <= n, (n, m, oracle_gates)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)} tests passed")
