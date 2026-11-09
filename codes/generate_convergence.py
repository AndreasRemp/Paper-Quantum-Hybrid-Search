"""Regenerates the convergence figure from ../results/single_instance.json.
Run run_single_instance.py first.

Usage:
    python generate_convergence.py              # figures/convergence.{pdf,png}
    python generate_convergence.py --springer   # figures/springer/Fig4.{pdf,eps}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt

from plot_style import MARKED, apply_style, variant_from_argv, width_in

ROOT = Path(__file__).resolve().parent.parent


def main():
    variant = variant_from_argv()
    apply_style(variant)
    with open(ROOT / "results" / "single_instance.json", encoding="utf-8") as f:
        data = json.load(f)

    h_values = data["trajectory_h"]
    steps = list(range(len(h_values)))

    fig, ax = plt.subplots(figsize=(width_in(variant), 2.1 if variant == "ieee" else 2.7))
    ax.plot(steps, h_values, color=MARKED, linewidth=1.0, marker="o", markersize=2.2)
    ax.set_xlabel("Step $t$")
    ax.set_ylabel("Manhattan distance $h(s_t)$")
    ax.set_xlim(0, len(h_values) - 1)
    ax.set_ylim(bottom=0)
    ax.grid(True, linewidth=0.3, alpha=0.5)

    if variant == "springer":
        out_dir, stem, exts = ROOT / "figures" / "springer", "Fig4", ("pdf", "eps")
    else:
        out_dir, stem, exts = ROOT / "figures", "convergence", ("pdf", "png")
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in exts:
        path = out_dir / f"{stem}.{ext}"
        fig.savefig(path, dpi=300)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
