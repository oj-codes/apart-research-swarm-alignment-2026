#!/usr/bin/env python3
"""Figure 1: Agent-Session trailer adoption per participant, split at the moment the trailer convention landed
(8 Nov 01:06 EST, merge of PR #16). Counts at main b2ca5a7 from split_by_convention.py. Two series, hues
validated against the light surface (#2a78d6, #eb6834)."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

out = sys.argv[1] if len(sys.argv) > 1 else "figure1.png"
# participant, first commit, (before: with, total), (after: with, total); ordered by first commit
rows = [
    ("Auran",  "7 Nov 12:10", (0, 12), (10, 22)),
    ("Corrie", "7 Nov 19:51", (4, 21), (9, 9)),
    ("Codex",  "7 Nov 23:19", (0, 3),  (1, 1)),
    ("Tern",   "8 Nov 00:26", (6, 6),  (5, 5)),
    ("Venice", "8 Nov 04:17", (0, 0),  (18, 18)),
    ("Rill",   "8 Nov 05:42", (0, 0),  (10, 10)),
]
WITH, WITHOUT = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d3"

fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=300)
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
yt, ylab = [], []
y = 0.0
h = 0.34
for name, first, before, after in rows[::-1]:
    for label, (w, total), off in (("after", after, 0.0), ("before", before, h + 0.06)):
        if total == 0:
            continue
        yy = y + off
        ax.barh(yy, w, height=h, color=WITH, edgecolor="white", linewidth=1.2, zorder=3)
        ax.barh(yy, total - w, left=w, height=h, color=WITHOUT, edgecolor="white", linewidth=1.2, zorder=3)
        ax.text(total + 0.3, yy, f"{w} of {total} {label}", va="center", ha="left", fontsize=7.5, color=INK, zorder=4)
    yt.append(y + (h + 0.06) / 2); ylab.append(f"{name}\n{first}")
    y += 1.0
ax.set_yticks(yt); ax.set_yticklabels(ylab, fontsize=8, color=INK)
ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 26)
ax.set_xlabel("non-merge commits on main at b2ca5a7, split at the trailer convention (8 Nov 01:06 EST)", fontsize=7.5, color=INK2)
ax.tick_params(axis="x", labelsize=7.5, colors=INK2, length=0)
ax.xaxis.grid(True, color=GRID, linewidth=0.6, zorder=0)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.legend(handles=[Patch(color=WITH, label="with Agent-Session trailer"), Patch(color=WITHOUT, label="without")],
          loc="lower right", fontsize=7.5, frameon=False, labelcolor=INK)
plt.tight_layout(pad=0.4)
fig.savefig(out, dpi=300, facecolor="white")
print("wrote", out)
