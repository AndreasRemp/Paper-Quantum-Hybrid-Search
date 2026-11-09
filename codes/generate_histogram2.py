"""Regenerates the second worked-example measurement-distribution figure from
../results/second_example.json. See run_second_example.py.

Usage:
    python generate_histogram2.py              # figures/histogram2.{pdf,png}
    python generate_histogram2.py --springer   # figures/springer/Fig3.{pdf,eps}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_histogram import histogram_figure
from plot_style import variant_from_argv

ROOT = Path(__file__).resolve().parent.parent


def main():
    with open(ROOT / "results" / "second_example.json", encoding="utf-8") as f:
        data = json.load(f)
    histogram_figure(data["counts"], data["num_candidates"], data["num_states"],
                     data["marked"], "histogram2", variant_from_argv(), "Fig3")


if __name__ == "__main__":
    main()
