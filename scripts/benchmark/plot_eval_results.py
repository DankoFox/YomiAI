"""
Generate a Vercel-style minimalist horizontal bar chart for HR@10 results.
Output: evaluation/hr10_chart.png

Usage:
    python scripts/benchmark/plot_eval_results.py
"""

import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT  = os.path.join(ROOT, "evaluation", "hr10_chart.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ── Data (bottom to top) ──────────────────────────────────────────────────────
labels = [
    "GRU-SeqDQN  (prior)",
    "Random Baseline",
    "Content Baseline  (BGE-M3)",
    "Pipeline B  (DIF-SASRec)",
    "Pipeline A  (Cleora + BGE-M3)",
]
values = [0.082, 0.100, 0.435, 0.775, 0.905]

# Kanagawa palette
COLORS = {
    "pipeline_a": "#2e3257",   # deep navy
    "pipeline_b": "#627d9a",   # muted steel blue
    "baseline":   "#727169",   # warm gray
    "prior":      "#c34043",   # muted red
}
bar_colors = [
    COLORS["prior"],
    COLORS["baseline"],
    COLORS["baseline"],
    COLORS["pipeline_b"],
    COLORS["pipeline_a"],
]

RANDOM_VAL  = 0.100
TEXT_DARK   = "#1a1a1a"
GRID_COLOR  = "#e8e8e8"
SPINE_COLOR = "#d0d0d0"

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
fig.patch.set_alpha(0)
ax.set_facecolor("none")

# ── Bars ──────────────────────────────────────────────────────────────────────
y_pos = range(len(labels))
bars  = ax.barh(
    y_pos, values,
    color=bar_colors,
    height=0.50,
    zorder=3,
)

# ── Value labels ──────────────────────────────────────────────────────────────
for bar, val in zip(bars, values):
    ax.text(
        val + 0.014,
        bar.get_y() + bar.get_height() / 2,
        f"{val:.3f}",
        va="center", ha="left",
        fontsize=10.5, fontweight="700",
        color=TEXT_DARK,
        fontfamily="DejaVu Sans",
    )

# ── Random baseline dashed line ───────────────────────────────────────────────
ax.axvline(
    x=RANDOM_VAL,
    color="#aaaaaa",
    linestyle="--",
    linewidth=1.0,
    zorder=4,
)

# ── Y-axis labels ─────────────────────────────────────────────────────────────
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=10, color=TEXT_DARK, fontfamily="DejaVu Sans")

# ── X-axis ────────────────────────────────────────────────────────────────────
ax.set_xlim(0, 1.02)
ax.set_xlabel("HR@10", fontsize=10.5, color="#555555",
              labelpad=10, fontfamily="DejaVu Sans")
ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.tick_params(axis="x", colors="#999999", labelsize=9, length=0)
ax.tick_params(axis="y", length=0, pad=10)

# ── Spines ────────────────────────────────────────────────────────────────────
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color(SPINE_COLOR)
ax.spines["bottom"].set_linewidth(0.8)

# ── Grid ──────────────────────────────────────────────────────────────────────
ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8, zorder=1)
ax.set_axisbelow(True)

# ── Layout & export ───────────────────────────────────────────────────────────
plt.tight_layout(pad=1.4)
plt.savefig(OUT, dpi=300, bbox_inches="tight", transparent=True)
print(f"Saved: {OUT}")
