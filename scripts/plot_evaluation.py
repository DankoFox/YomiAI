"""
scripts/plot_evaluation.py
Horizontal bar chart: HR@10 only, ordered low → high.
Output: evaluation/evaluation_chart.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evaluation", "evaluation_chart.png")
)

# ── Data (low → high so strongest sits at top) ────────────────────────────────
systems = [
    "Random Baseline",
    "Content Baseline (BGE-M3)",
    "GRU4Rec  (Hidasi et al. 2016)",
    "Pipeline B — DIF-SASRec",
    "SASRecF  (Kang & McAuley 2018)",
    "Pipeline A — Cleora + BGE-M3",
    "System A∪B  (Ours)",
]
hr10 = [0.100, 0.435, 0.770, 0.774, 0.793, 0.905, 0.974]

# ── Colours: grey for external baselines, blue for ours ───────────────────────
BASELINE_COLOR = "#8FA8C8"
OUR_COLOR      = "#2563EB"
HIGHLIGHT      = "#1D4ED8"

colors = [
    "#BBBBBB",   # Random
    BASELINE_COLOR,
    BASELINE_COLOR,
    OUR_COLOR,
    BASELINE_COLOR,
    OUR_COLOR,
    HIGHLIGHT,   # System A∪B — darkest
]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5.5))
fig.patch.set_facecolor("white")

y = np.arange(len(systems))
bars = ax.barh(y, hr10, height=0.55, color=colors, zorder=3)

# Value labels inside or just outside each bar
for bar, val, col in zip(bars, hr10, colors):
    x_pos = bar.get_width() + 0.008
    ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}", va="center", ha="left", fontsize=10,
            fontweight="bold", color=col)

# Reference line at random baseline
ax.axvline(0.100, color="#CCCCCC", linewidth=1.2, linestyle="--", zorder=2)

# ── Axes ──────────────────────────────────────────────────────────────────────
ax.set_yticks(y)
ax.set_yticklabels(systems, fontsize=10.5)
ax.set_xlabel("HR@10", fontsize=11)
ax.set_xlim(0, 1.12)
ax.set_title(
    "End-to-End Evaluation  —  Amazon Books\n"
    "Sampled protocol: N=99 negatives, leave-last-out split, 100k users",
    fontsize=11, pad=10
)
ax.xaxis.grid(True, linestyle="--", alpha=0.35, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend patch
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=BASELINE_COLOR, label="Literature baseline"),
    Patch(facecolor=OUR_COLOR,      label="Our system"),
]
ax.legend(handles=legend_elements, fontsize=9.5, loc="lower right", framealpha=0.9)

plt.tight_layout()
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT_PATH}")
plt.close()
