"""Regenerates ../latex/convergence.png (paper Figure 3) from
../results/single_instance.json. Run run_single_instance.py first.

Usage:
    python generate_convergence.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent


def main():
    with open(ROOT / "results" / "single_instance.json", encoding="utf-8") as f:
        data = json.load(f)

    h_values = data["trajectory_h"]
    steps = list(range(len(h_values)))

    plt.figure(figsize=(8, 5))
    plt.plot(steps, h_values, color="#d62728", linewidth=1.5)
    plt.xlabel("Step")
    plt.ylabel("Manhattan distance $h(s_t)$")
    plt.title(f"Convergence for instance {data['initial']}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    out_path = ROOT / "figures" / "convergence.png"
    plt.savefig(out_path, dpi=150)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
