"""Matplotlib palette and rcParams for figures in Quarto pptx decks.

This is a **generic placeholder palette**. Swap the hex values below for your
own brand colors and re-validate them for a dark chart surface before
production use (see the dataviz guidance referenced in presentations/README.md).

The bright accent hues are LINE / LABEL steps: use them for thin marks
(lines, markers, text accents) and never for large solid fills. The *_FILL
steps are darker in-band variants for solid fills (bars, tiles), chosen to
pass a categorical dark-surface check (lightness band, chroma floor, CVD
separation, and contrast against the ground). Adjacent solid fills should
still carry direct labels or surface gaps.

Usage in a Quarto chunk:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path("assets").resolve()))
    import deck_mpl
    deck_mpl.use()
"""

import matplotlib as mpl
from cycler import cycler

# Ground and ink (generic dark surface)
GROUND = "#0E1116"      # slide/chart ground — match your template's background
INK = "#F5F7FA"         # primary text
MUTED = "#A6AEBB"       # secondary text, axis labels
GRID = "#1E2530"        # recessive gridlines

# Line/label steps (bright — thin marks and text accents only)
BLUE = "#4EA1F0"
AMBER = "#E8A44C"
GREEN = "#57C88A"

# Fill steps (validated in-band for solid fills on GROUND)
BLUE_FILL = "#2E7FC2"
AMBER_FILL = "#C07A32"
GREEN_FILL = "#2FA268"

SERIES = [BLUE, AMBER, GREEN]
FILLS = [BLUE_FILL, AMBER_FILL, GREEN_FILL]


def use():
    """Apply the dark deck style to matplotlib rcParams.

    Emits transparent figures so they composite seamlessly on the slide
    ground — an opaque background that only approximates the slide color
    shows a visible seam under some renderers.
    """
    mpl.rcParams.update({
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "savefig.facecolor": "none",
        "savefig.transparent": True,
        "text.color": INK,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": MUTED,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": cycler(color=SERIES),
        "lines.linewidth": 2.5,
        "lines.markersize": 9,
        "font.family": ["DejaVu Sans", "Segoe UI", "sans-serif"],
        "font.size": 13,
        "figure.dpi": 150,
        "savefig.dpi": 200,
    })


def smooth(xs, ys, n=400, passes=3, window=25):
    """Dense piecewise-linear interpolation smoothed into a curve.

    Keeps figure code dependency-free (no scipy) while giving
    presentation-quality curves through a small set of control points.
    """
    import numpy as np

    x = np.linspace(xs[0], xs[-1], n)
    y = np.interp(x, xs, ys)
    kernel = np.ones(window) / window
    for _ in range(passes):
        pad = np.concatenate([np.full(window, y[0]), y, np.full(window, y[-1])])
        y = np.convolve(pad, kernel, mode="same")[window:-window]
    return x, y
