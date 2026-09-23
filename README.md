# Hybrid Quantum-Classical Look-Ahead Search Framework for Sliding-Tile Puzzles

Implementation, experiment scripts, and recorded results supporting the
paper of the same name (Rempoutsikas & Sgarbas).

A classical beam-search lookahead stage expands and scores candidate move
sequences with the Manhattan distance heuristic; a dynamically-constructed
Grover circuit then probabilistically selects among the lowest-cost
candidates via a single projective measurement. The quantum circuit
operates only on a compact index register sized to the candidate set, not
the puzzle's state space, so qubit count and circuit depth stay
independent of problem size.

## Method, in short

1. **Classical lookahead** — bounded breadth-first search to depth `L`, with
   reverse-move pruning and shortest-path deduplication, produces a beam of
   up to `k` candidate paths, each scored by `f = g + h` (Manhattan
   distance heuristic).
2. **Quantum selection** — a Grover circuit over `ceil(log2(k))` index
   qubits amplifies the candidates sharing the minimum `f`, then a single
   projective measurement picks one.
3. **Move execution** — if the selected successor state is on a fixed-size
   tabu list, a classical fallback picks the best non-tabu candidate
   instead.

## Repo layout

```
codes/       puzzle.py, lookahead.py, quantum_selector.py, solver.py -- the
             implementation -- plus run_single_instance.py, run_batch.py,
             run_second_example.py (experiments) and generate_*.py (figure
             generation).
results/     JSON/log output from the experiment scripts -- the recorded
             outcome of every run.
figures/     the plots generated from results/.
```

## Reproducing the results

```bash
pip install -r requirements.txt
cd codes
python run_single_instance.py    # -> ../results/single_instance.json
python run_batch.py              # -> ../results/batch.json
python run_second_example.py     # -> ../results/second_example.json
python generate_convergence.py   # -> ../figures/convergence.png
python generate_histogram.py     # -> ../figures/histogram.png
python generate_histogram2.py    # -> ../figures/histogram2.png
```

All randomness is seeded (`seed_sim`, `seed_transpile`); re-running
produces identical output. Parameters (lookahead depth, beam width, tabu
window, step budget) are fixed at the top of each script. The per-step
move decision is a single projective measurement (seeded per-step from
`seed_sim`); the 1024-shot counts you'll see in `results/*.json` are
separate diagnostic snapshots used only for illustrative figures, not the
decision itself.

> **Note on Windows ARM64:** `qiskit-aer` has no prebuilt wheel for
> win-arm64. If `pip install` fails trying to compile `rustworkx` from
> source, install any standard x86_64 Python (e.g. the
> [embeddable package](https://www.python.org/downloads/windows/), which
> runs fine under Windows' x64 emulation) and use that interpreter instead.
> On Linux/macOS/Windows x86_64 this is not an issue.

## License

MIT — see `LICENSE`.
