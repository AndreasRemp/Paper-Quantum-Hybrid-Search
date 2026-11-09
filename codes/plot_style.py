"""Shared matplotlib style for the paper's figures.

Two variants are provided: "ieee" (single-column width, serif lettering) and
"springer" (119 mm width, sans-serif lettering, files written as Fig<N>.eps/.pdf).
"""

import sys

import matplotlib as mpl

MARKED = "#1f4e9c"
UNMARKED = "#9a9a9a"
PADDING = "#d9d9d9"

VARIANTS = {
    "ieee": {"width_in": 3.5, "font_size": 8, "family": "serif",
             "serif": ["Times New Roman", "Times", "DejaVu Serif"], "mathtext": "stix"},
    "springer": {"width_in": 119 / 25.4, "font_size": 9, "family": "sans-serif",
                 "sans": ["Arial", "Helvetica", "DejaVu Sans"], "mathtext": "dejavusans"},
}

# Back-compat constant used by the IEEE-width figures.
COLUMN_WIDTH_IN = VARIANTS["ieee"]["width_in"]


def variant_from_argv(argv=None):
    """'springer' if --springer is among the command-line arguments, else 'ieee'."""
    return "springer" if "--springer" in (argv if argv is not None else sys.argv[1:]) else "ieee"


def width_in(variant="ieee"):
    return VARIANTS[variant]["width_in"]


def apply_style(variant="ieee"):
    v = VARIANTS[variant]
    rc = {
        "font.family": v["family"],
        "mathtext.fontset": v["mathtext"],
        "font.size": v["font_size"],
        "axes.labelsize": v["font_size"],
        "xtick.labelsize": v["font_size"] - 1,
        "ytick.labelsize": v["font_size"] - 1,
        "legend.fontsize": v["font_size"] - 1,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    }
    if "serif" in v:
        rc["font.serif"] = v["serif"]
    if "sans" in v:
        rc["font.sans-serif"] = v["sans"]
    mpl.rcParams.update(rc)
