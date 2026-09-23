"""Quantum selector: dynamically-constructed Grover circuit over a candidate index
register (paper Section 3.2 "Quantum stage" and Section 3.5 "The Quantum Selector").

The circuit uses n = ceil(log2(k)) index qubits plus one ancilla qubit prepared in
the |-> state for phase kickback. The oracle marks every index in the marked set M
by flipping the zero bits of its binary representation, applying a multi-controlled
X onto the ancilla, then unflipping. The diffuser is the standard
H -> X -> MCZ -> X -> H inversion-about-the-mean on the index register.
"""

import math

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def grover_iterations(num_states: int, num_marked: int) -> int:
    """r = floor((pi/4) * sqrt(N / M)); a single iteration if M >= N/2."""
    if num_marked <= 0:
        return 0
    if num_marked >= num_states / 2:
        return 1
    r = math.floor((math.pi / 4.0) * math.sqrt(num_states / num_marked))
    return max(1, r)


def _apply_oracle(qc: QuantumCircuit, idx_qubits, anc_qubit: int, marked_indices, n_bits: int):
    for idx in marked_indices:
        bits = format(idx, f"0{n_bits}b")
        for i, bit in enumerate(bits):
            if bit == "0":
                qc.x(idx_qubits[i])
        qc.mcx(list(idx_qubits), anc_qubit)
        for i, bit in enumerate(bits):
            if bit == "0":
                qc.x(idx_qubits[i])


def _apply_diffuser(qc: QuantumCircuit, idx_qubits):
    qc.h(idx_qubits)
    qc.x(idx_qubits)
    last = idx_qubits[-1]
    qc.h(last)
    if len(idx_qubits) > 1:
        qc.mcx(idx_qubits[:-1], last)
    else:
        qc.z(last)
    qc.h(last)
    qc.x(idx_qubits)
    qc.h(idx_qubits)


def build_circuit(num_items: int, marked_indices):
    """Build the Grover selector circuit for `num_items` candidates with the given
    marked indices. Returns (circuit, n_bits, num_states, iterations)."""
    n_bits = max(1, math.ceil(math.log2(max(2, num_items))))
    num_states = 2 ** n_bits
    iterations = grover_iterations(num_states, len(marked_indices))

    qc = QuantumCircuit(n_bits + 1, n_bits)
    idx_qubits = list(range(n_bits))
    anc_qubit = n_bits

    qc.x(anc_qubit)
    qc.h(anc_qubit)
    qc.h(idx_qubits)

    for _ in range(iterations):
        _apply_oracle(qc, idx_qubits, anc_qubit, marked_indices, n_bits)
        _apply_diffuser(qc, idx_qubits)

    qc.measure(idx_qubits, list(range(n_bits)))
    return qc, n_bits, num_states, iterations


def decode_index(bitstring: str, num_items: int) -> int:
    """Reverse Qiskit's little-endian bitstring and interpret as a binary integer."""
    bits = bitstring.replace(" ", "")
    idx = int(bits[::-1], 2)
    return idx % num_items if idx >= num_items else idx


def grover_select(num_items: int, marked_indices, shots: int = 1024,
                   seed_sim: int = 42, seed_transpile: int = 42):
    """Run the Grover selector and return (counts, n_bits, num_states, iterations)."""
    qc, n_bits, num_states, iterations = build_circuit(num_items, marked_indices)

    simulator = AerSimulator(seed_simulator=seed_sim)
    transpiled = transpile(qc, simulator, seed_transpiler=seed_transpile)
    result = simulator.run(transpiled, shots=shots).result()
    counts = result.get_counts()

    return counts, n_bits, num_states, iterations


def ranked_indices_from_counts(counts: dict, num_items: int):
    """Decode every measured bitstring to a candidate index, ordered by descending count."""
    ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [decode_index(bitstring, num_items) for bitstring, _ in ordered]
