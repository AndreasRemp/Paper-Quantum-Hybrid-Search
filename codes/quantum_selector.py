"""Quantum selector: dynamically constructed Grover circuit over a candidate index
register (the "quantum stage" of the paper's Algorithm 1).

The circuit uses n = ceil(log2(|C|)) index qubits plus one ancilla qubit prepared
in the |-> state for phase kickback. Two equivalent oracles are provided. The
direct oracle marks every index in the marked set M by flipping the zero bits of
its binary representation, applying a multi-controlled X onto the ancilla, then
unflipping, so its cost grows linearly with |M|. Because the candidate list is
sorted by cost, M is always the prefix {0, ..., |M|-1}; the prefix oracle (the
default) marks it with at most n multi-controlled gates, one per set bit of |M|.
The diffuser is the standard H -> X -> MCZ -> X -> H inversion about the mean on
the index register.
"""

import math

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def grover_iterations(num_states: int, num_marked: int) -> int:
    """Number of Grover iterations r.

    r = floor((pi/4) * sqrt(N / M)) when M < N/2. When M >= N/2 no iteration is
    applied (r = 0): the uniform superposition already succeeds with probability
    M/N >= 1/2, and a Grover iteration would not increase it (it leaves it
    unchanged at M/N = 1/2 and lowers it for M/N > 1/2).
    """
    if num_marked <= 0 or 2 * num_marked >= num_states:
        return 0
    return math.floor((math.pi / 4.0) * math.sqrt(num_states / num_marked))


def success_probability(num_states: int, num_marked: int, iterations: int) -> float:
    """Probability that measuring the index register yields a marked state after
    `iterations` Grover iterations: sin^2((2r + 1) * theta), sin(theta) = sqrt(M/N)."""
    if num_marked <= 0:
        return 0.0
    theta = math.asin(math.sqrt(num_marked / num_states))
    return math.sin((2 * iterations + 1) * theta) ** 2


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


def _apply_prefix_oracle(qc: QuantumCircuit, idx_qubits, anc_qubit: int, num_marked: int, n_bits: int):
    """Oracle for the prefix {0, ..., m-1}, m = num_marked < 2**n_bits.

    The prefix is a union of one aligned block per set bit j of m: the indices
    whose bits above position j equal those of m, whose bit j is 0, and whose
    lower bits are free. Each block is a conjunction on the n - j leading
    qubits, so it needs a single multi-controlled X onto the ancilla. At most
    n_bits such gates are used, whatever the size of the marked set. Qubit q
    holds the bit at position n_bits - 1 - q (the convention of _apply_oracle).
    """
    for j in range(n_bits):
        if not (num_marked >> j) & 1:
            continue
        flips = []
        for q in range(n_bits - j):
            position = n_bits - 1 - q
            required = 0 if position == j else (num_marked >> position) & 1
            if required == 0:
                flips.append(q)
        for q in flips:
            qc.x(idx_qubits[q])
        qc.mcx(list(idx_qubits[: n_bits - j]), anc_qubit)
        for q in flips:
            qc.x(idx_qubits[q])


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


def is_prefix(marked_indices) -> bool:
    """True if the marked set is {0, ..., m-1}, which the solver always produces
    because the candidate list is sorted by cost."""
    return sorted(marked_indices) == list(range(len(marked_indices)))


def build_circuit(num_items: int, marked_indices, oracle: str = "auto", iterations=None):
    """Build the Grover selector circuit for `num_items` candidates with the given
    marked indices. Returns (circuit, n_bits, num_states, iterations).

    oracle: "direct" uses one multi-controlled gate per marked index; "prefix"
    uses the block decomposition of {0, ..., m-1} (at most n_bits gates);
    "auto" (default) uses "prefix" when the marked set is a prefix and "direct"
    otherwise. Both implement the same unitary. `iterations` overrides the
    iteration rule (used to compare the two oracles)."""
    n_bits = max(1, math.ceil(math.log2(max(2, num_items))))
    num_states = 2 ** n_bits
    if iterations is None:
        iterations = grover_iterations(num_states, len(marked_indices))
    if oracle not in ("auto", "direct", "prefix"):
        raise ValueError(f"unknown oracle {oracle!r}")
    use_prefix = oracle == "prefix" or (oracle == "auto" and is_prefix(marked_indices))
    if use_prefix and not is_prefix(marked_indices):
        raise ValueError("the prefix oracle requires the marked set {0, ..., m-1}")
    if use_prefix and len(marked_indices) >= num_states:
        use_prefix = False  # every state marked: fall back to the direct form

    qc = QuantumCircuit(n_bits + 1, n_bits)
    idx_qubits = list(range(n_bits))
    anc_qubit = n_bits

    qc.x(anc_qubit)
    qc.h(anc_qubit)
    qc.h(idx_qubits)

    for _ in range(iterations):
        if use_prefix:
            _apply_prefix_oracle(qc, idx_qubits, anc_qubit, len(marked_indices), n_bits)
        else:
            _apply_oracle(qc, idx_qubits, anc_qubit, marked_indices, n_bits)
        _apply_diffuser(qc, idx_qubits)

    qc.measure(idx_qubits, list(range(n_bits)))
    return qc, n_bits, num_states, iterations


def decode_index(bitstring: str, num_items: int) -> int:
    """Reverse Qiskit's little-endian bitstring and interpret as a binary integer.

    If the candidate count is not a power of two, register values >= num_items
    are padding outcomes (never marked); they are mapped onto a valid candidate
    by modular reduction."""
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
