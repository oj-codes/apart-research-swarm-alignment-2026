#!/usr/bin/env python3
"""Figure 1: Agent-Session trailer adoption per participant at main 32ecea4, ordered by first commit.
Two series (with / without trailer), hues validated against the light surface (#2a78d6, #eb6834)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

out = sys.argv[1] if len(sys.argv) > 1 else "figure1.png"
# (participant, first commit, commits with trailer, commits without), ordered by first commit, oldest at top
rows = [
    ("Auran",  "7 Nov 12:10", 2, 24),
    ("Corrie", "7 Nov 19:51", 4, 17),
    ("Codex",  "7 Nov 23:19", 1, 3),
    ("Tern",   "8 Nov 00:26", 8, 0),
    ("Venice", "8 Nov 04:17", 11, 0),
    ("Rill",   "8 Nov 05:42", 3, 0),
]
WITH, WITHOUT = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d3"

fig, ax = plt.subplots(figsize=(6.5, 3.1), dpi=300)
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
y = list(range(len(rows)))[::-1]
h = 0.56
for yi, (name, first, w, wo) in zip(y, rows):
    ax.barh(yi, w, height=h, color=WITH, edgecolor="white", linewidth=1.5, zorder=3)
    ax.barh(yi, wo, left=w, height=h, color=WITHOUT, edgecolor="white", linewidth=1.5, zorder=3)
    total = w + wo
    ax.text(total + 0.4, yi, f"{w} of {total}", va="center", ha="left", fontsize=8, color=INK, zorder=4)
ax.set_yticks(y)
ax.set_yticklabels([f"{n}\n{f}" for n, f, _, _ in rows], fontsize=8, color=INK)
ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 30)
ax.set_xlabel("non-merge commits on main at 32ecea4", fontsize=8, color=INK2)
ax.tick_params(axis="x", labelsize=7.5, colors=INK2, length=0)
ax.xaxis.grid(True, color=GRID, linewidth=0.6, zorder=0)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
# divider between the three who arrived before the convention and the three after
ax.axhline(2.5, color=INK2, linewidth=0.8, linestyle=(0, (3, 2)), zorder=2)
ax.text(29.8, 2.5 + 0.1, "first commit before the trailer convention landed (8 Nov 01:06 EST)", ha="right", va="bottom", fontsize=7, color=INK2)
ax.text(29.8, 2.5 - 0.12, "first commit after it", ha="right", va="top", fontsize=7, color=INK2)
# Codex annotation
ax.text(7.6, 3.0, "none of the 3 before the convention; the 1 after has it", fontsize=7, color=INK2, va="center", ha="left")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=WITH, label="with Agent-Session trailer"), Patch(color=WITHOUT, label="without")],
          loc="lower right", fontsize=7.5, frameon=False, labelcolor=INK)
plt.tight_layout(pad=0.4)
fig.savefig(out, dpi=300, facecolor="white")
print("wrote", out)
