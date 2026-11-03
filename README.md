# Hybrid Quantum-Classical Look-Ahead Search Framework for Sliding-Tile Puzzles

Implementation, experiment scripts, and recorded results for the paper of the
same name (A. Rempoutsikas and K. N. Sgarbas, University of Patras).

A classical beam-search look-ahead stage expands and scores candidate move
sequences with the Manhattan distance heuristic. A dynamically constructed
Grover circuit then selects among the lowest-cost candidates with a single
projective measurement. The circuit acts on a compact index register of
`ceil(log2 |C|)` qubits over the candidate set `C`, not on the puzzle's state
space, so its size is set by the beam width and not by the problem size.

No quantum speedup is claimed: at a beam width of 16 a classical `argmin` is
trivial. The repository documents a reproducible architecture in which
amplitude amplification acts as a decision-level operator inside an iterative
heuristic search.

## Method

1. **Classical look-ahead.** Bounded breadth-first search to depth `L`, with
   reverse-move pruning and shortest-path deduplication, produces a beam of up
   to `k` candidate paths, each scored by `f = g + h` (Manhattan distance).
2. **Quantum selection.** A Grover circuit over `ceil(log2 |C|)` index qubits
   plus one ancilla amplifies the candidates sharing the minimum `f`. A single
   projective measurement picks one. The number of Grover iterations is
   `floor(pi/4 * sqrt(N/M))` for `M < N/2` marked states out of `N`, and zero
   otherwise.
3. **Move execution.** If the successor of the selected candidate is on a
   fixed-size tabu list, a classical fallback picks the best-ranked non-tabu
   candidate instead. Only the first move of the chosen path is executed.

## Repository layout

```text
codes/       puzzle.py            states, solvability, moves, Manhattan distance
             lookahead.py         classical look-ahead stage
             quantum_selector.py  Grover oracle, diffuser, iteration rule
             solver.py            the full hybrid loop (Algorithm 1)
             astar.py             reference A* (optimal solution lengths)
             run_single_instance.py, run_second_example.py, run_batch.py,
             run_controls.py, circuit_resources.py      experiments
             generate_*.py, plot_style.py               figures
             test_core.py         checks of the facts the paper states
results/     JSON and log output of every experiment
figures/     figures generated from results/ (PDF and PNG)
```

## Reproducing the results

```bash
pip install -r requirements.txt
cd codes
python run_single_instance.py    # -> ../results/single_instance.json
python run_second_example.py     # -> ../results/second_example.json
python run_batch.py              # -> ../results/batch.json
python run_controls.py           # -> ../results/controls.json  (slowest)
python circuit_resources.py      # -> ../results/circuit_resources.json
python generate_convergence.py   # -> ../figures/convergence.{pdf,png}
python generate_histogram.py     # -> ../figures/histogram.{pdf,png}
python generate_histogram2.py    # -> ../figures/histogram2.{pdf,png}
```

All randomness is seeded (`seed_sim`, `seed_transpile`), so re-running produces
identical output. Parameters (look-ahead depth, beam width, tabu window, step
budget) are set at the top of each script. The per-step move decision is a
single projective measurement, seeded per step as `1000 * seed_sim + t`; the
1024-shot counts stored in `results/*.json` are separate diagnostic snapshots
used only for the histogram figures, not for the decision. Run
`run_single_instance.py` before `run_second_example.py` and the figure
generators, which read its output.

`python test_core.py` (or `pytest`) checks the puzzle geometry, the look-ahead
candidate count, the Grover iteration rule, and the closed-form success
probabilities that the paper states.

Results were produced with Python 3.12, Qiskit 2.5.2, Qiskit Aer 0.17.2.

> **Note on Windows ARM64.** `qiskit-aer` has no prebuilt wheel for
> win-arm64. If `pip install` fails trying to compile `rustworkx` from source,
> install a standard x86_64 Python (for example the
> [embeddable package](https://www.python.org/downloads/windows/), which runs
> under Windows' x64 emulation) and use that interpreter. On Linux, macOS, and
> Windows x86_64 this is not an issue.

## License

MIT. See `LICENSE`.
