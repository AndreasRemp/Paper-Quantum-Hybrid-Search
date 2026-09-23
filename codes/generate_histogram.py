"""Regenerates ../latex/histogram.png (paper Figure 2) from
../results/single_instance.json. Run run_single_instance.py first.

Usage:
    python generate_histogram.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent


def main():
    with open(ROOT / "results" / "single_instance.json", encoding="utf-8") as f:
        data = json.load(f)

    counts = data["first_step"]["counts"]
    num_items = data["first_step"]["num_candidates"]

    def decode(bitstring):
        bits = bitstring.replace(" ", "")
        idx = int(bits[::-1], 2)
        return idx % num_items if idx >= num_items else idx

    decoded = {}
    for bitstring, c in counts.items():
        idx = decode(bitstring)
        decoded[idx] = decoded.get(idx, 0) + c

    indices = sorted(decoded.keys())
    values = [decoded[i] for i in indices]

    plt.figure(figsize=(8, 5))
    marked = set(data["first_step"]["marked"])
    colors = ["#1f77b4" if i in marked else "#c7c7c7" for i in indices]
    plt.bar([str(i) for i in indices], values, color=colors)
    plt.xlabel("Candidate index")
    plt.ylabel("Counts")
    plt.title(f"Grover selector measurement, step 1, instance {data['initial']}")
    plt.tight_layout()

    out_path = ROOT / "figures" / "histogram.png"
    plt.savefig(out_path, dpi=150)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
