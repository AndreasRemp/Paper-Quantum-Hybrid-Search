"""Regenerates the step-1 measurement-distribution figure from
../results/single_instance.json. Run run_single_instance.py first.

The bars show the raw measured index-register value 0..N-1. Values at or above
the candidate count are padding outcomes (they correspond to no candidate) and
are drawn in light grey.

Usage:
    python generate_histogram.py              # figures/histogram.{pdf,png}
    python generate_histogram.py --springer   # figures/springer/Fig2.{pdf,eps}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from plot_style import MARKED, PADDING, UNMARKED, apply_style, variant_from_argv, width_in

ROOT = Path(__file__).resolve().parent.parent


def raw_index_counts(counts: dict, num_states: int) -> list:
    """Map Qiskit little-endian bitstrings to raw register values 0..N-1."""
    values = [0] * num_states
    for bitstring, c in counts.items():
        values[int(bitstring.replace(" ", "")[::-1], 2)] += c
    return values


def histogram_figure(counts: dict, num_items: int, num_states: int, marked, out_stem: str,
                     variant: str = "ieee", springer_stem: str = "Fig2"):
    apply_style(variant)
    values = raw_index_counts(counts, num_states)
    marked = set(marked)
    colors = [MARKED if i in marked else (UNMARKED if i < num_items else PADDING)
              for i in range(num_states)]

    fig, ax = plt.subplots(figsize=(width_in(variant), 2.0 if variant == "ieee" else 2.6))
    ax.bar(range(num_states), values, color=colors, width=0.8)
    ax.set_xticks(range(num_states))
    ax.set_xlabel("Measured index $j$")
    ax.set_ylabel("Counts (1024 shots)")
    ax.set_xlim(-0.7, num_states - 0.3)
    handles = [Patch(color=MARKED, label="marked ($j \\in M$)"),
               Patch(color=UNMARKED, label="unmarked candidate")]
    if num_items < num_states:
        handles.append(Patch(color=PADDING, label="padding ($j \\geq |C|$)"))
    ax.legend(handles=handles, frameon=False, loc="upper right")

    if variant == "springer":
        out_dir, stem, exts = ROOT / "figures" / "springer", springer_stem, ("pdf", "eps")
    else:
        out_dir, stem, exts = ROOT / "figures", out_stem, ("pdf", "png")
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in exts:
        path = out_dir / f"{stem}.{ext}"
        fig.savefig(path, dpi=300)
        print(f"Wrote {path}")
    plt.close(fig)


def main():
    with open(ROOT / "results" / "single_instance.json", encoding="utf-8") as f:
        data = json.load(f)["first_step"]
    histogram_figure(data["counts"], data["num_candidates"], data["num_states"],
                     data["marked"], "histogram", variant_from_argv(), "Fig2")


if __name__ == "__main__":
    main()
