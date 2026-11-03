"""Shared matplotlib style for the paper's figures (IEEE single-column width)."""

import matplotlib as mpl

COLUMN_WIDTH_IN = 3.5  # IEEE single-column width in inches

MARKED = "#1f4e9c"
UNMARKED = "#9a9a9a"
PADDING = "#d9d9d9"


def apply_style():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "pdf.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })
