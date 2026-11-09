"""Draws the hybrid search-loop flowchart (paper's Fig. 1) as a vector figure.

Usage:
    python generate_flowchart.py    # figures/springer/Fig1.{pdf,eps}
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

from plot_style import apply_style, width_in

ROOT = Path(__file__).resolve().parent.parent
FS = 8  # node text size in points at the final 119 mm width


def box(ax, cx, cy, w, h, text):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                fc="white", ec="black", lw=0.9))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=FS)


def diamond(ax, cx, cy, hw, hh, text):
    ax.add_patch(Polygon([(cx - hw, cy), (cx, cy + hh), (cx + hw, cy), (cx, cy - hh)],
                         closed=True, fc="white", ec="black", lw=0.9))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=FS)


def arrow(ax, pts, label=None, label_xy=None, label_ha="center"):
    """Polyline with an arrow head on the last segment."""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=0.9, solid_capstyle="butt")
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=7,
                                 color="black", lw=0.9, shrinkA=0, shrinkB=0))
    if label:
        ax.text(*label_xy, label, fontsize=FS, ha=label_ha, va="center")


def main():
    apply_style("springer")
    fig, ax = plt.subplots(figsize=(width_in("springer"), 2.75))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 58)
    ax.axis("off")

    xs = [11, 31, 51, 71, 91]
    y1, w, h = 49, 17, 10
    box(ax, xs[0], y1, w, h, "Current\nstate $s_t$")
    box(ax, xs[1], y1, w, h, "Look-ahead\nBFS")
    box(ax, xs[2], y1, w, h, "Candidate\nset $C$")
    box(ax, xs[3], y1, w, h, "Grover\nselector")
    box(ax, xs[4], y1, w, h, "Measure\nindex $j$")
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, [(a + w / 2, y1), (b - w / 2, y1)])

    y2 = 28
    diamond(ax, 91, y2, 9, 7.5, "Tabu?")
    box(ax, 62, y2, 20, 10, "Execute move\n$s_{t+1}$")
    diamond(ax, 29, y2, 12, 8.5, "Goal\nreached?")
    arrow(ax, [(91, y1 - h / 2), (91, y2 + 7.5)])
    arrow(ax, [(91 - 9, y2), (62 + 10, y2)], "No", (80.5, y2 + 2.8))

    box(ax, 90.5, 7, 18, 9, "Classical\nfallback")
    arrow(ax, [(91, y2 - 7.5), (91, 7 + 4.5)], "Yes", (92.5, 18), "left")
    arrow(ax, [(90.5 - 9, 7), (62, 7), (62, y2 - 5)])
    arrow(ax, [(62 - 10, y2), (29 + 12, y2)])

    arrow(ax, [(29, y2 - 8.5), (29, 6)], "Solved", (31, 15), "left")
    arrow(ax, [(29 - 12, y2), (1.5, y2), (1.5, y1), (xs[0] - w / 2, y1)], "Not solved", (9.5, y2 + 2.8))

    out_dir = ROOT / "figures" / "springer"
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "eps"):
        path = out_dir / f"Fig1.{ext}"
        fig.savefig(path, dpi=300)
        print(f"Wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
