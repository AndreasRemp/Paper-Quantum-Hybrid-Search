"""Regenerates the convergence figure (convergence.pdf/.png) from
../results/single_instance.json. Run run_single_instance.py first.

Usage:
    python generate_convergence.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt

from plot_style import COLUMN_WIDTH_IN, MARKED, apply_style

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "figures"


def main():
    apply_style()
    with open(ROOT / "results" / "single_instance.json", encoding="utf-8") as f:
        data = json.load(f)

    h_values = data["trajectory_h"]
    steps = list(range(len(h_values)))

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH_IN, 2.1))
    ax.plot(steps, h_values, color=MARKED, linewidth=1.0, marker="o", markersize=2.2)
    ax.set_xlabel("Step $t$")
    ax.set_ylabel("Manhattan distance $h(s_t)$")
    ax.set_xlim(0, len(h_values) - 1)
    ax.set_ylim(bottom=0)
    ax.grid(True, linewidth=0.3, alpha=0.5)

    OUT_DIR.mkdir(exist_ok=True)
    for ext in ("pdf", "png"):
        path = OUT_DIR / f"convergence.{ext}"
        fig.savefig(path, dpi=300)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
