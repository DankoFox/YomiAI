"""
Generate three thesis defense slides as PNG:
  slide_nba_origins.png        — horizontal NBA timeline
  slide_nba_alternatives.png   — 3-column traditional approaches comparison
  slide_system_performance.png — dual-pipeline system performance
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Shared style ────────────────────────────────────────────────────────────
FONT = "DejaVu Sans"
plt.rcParams.update({
    "font.family": FONT,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
})

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved -> {path}")


# ══════════════════════════════════════════════════════════════════════════════
# Slide 1 — NBA Origins Timeline
# ══════════════════════════════════════════════════════════════════════════════
def slide_nba_origins():
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 5)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Title
    ax.text(8, 4.6, "Evolution of Next Best Action Recommendation Systems",
            ha="center", va="center", fontsize=16, fontweight="bold", color="#1a1a2e")

    # Timeline axis
    ax.annotate("", xy=(15.2, 2.0), xytext=(0.8, 2.0),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=2.0))

    nodes = [
        # (x_center, label_top, label_bot, fill, edge, text_col)
        (2.0,  "FPMC",         "2010",  "#d0d0d0", "#888888", "#222222"),
        (4.8,  "GRU4Rec",      "2016",  "#c8daf0", "#4a7abf", "#1a3a6e"),
        (7.6,  "SASRec",       "2018",  "#a8c8f0", "#2060c0", "#0d2a5e"),
        (10.6, "MMSSL · BM3",  "2022+", "#a0d8d0", "#288070", "#0a3830"),
        (13.6, "Our System",   "2024",  "#c8a8e8", "#7040b0", "#3a1060"),
    ]

    sub = [
        "Markov + MF\nnext-item",
        "RNN session\nmodeling",
        "Self-attention\nsequential",
        "Multimodal\nvisual + text",
        "Cleora + BGE-M3\nDIF-SASRec",
    ]

    box_w, box_h = 2.2, 1.0

    for (xc, top, bot, fc, ec, tc), desc in zip(nodes, sub):
        # Box
        rect = FancyBboxPatch((xc - box_w/2, 2.0 - box_h/2), box_w, box_h,
                              boxstyle="round,pad=0.08", linewidth=2,
                              edgecolor=ec, facecolor=fc)
        ax.add_patch(rect)
        # Top label (method name)
        ax.text(xc, 2.28, top, ha="center", va="center",
                fontsize=11, fontweight="bold", color=tc)
        # Bottom label (year)
        ax.text(xc, 1.82, bot, ha="center", va="center",
                fontsize=10, color=tc)
        # Sub-description below box
        ax.text(xc, 1.15, desc, ha="center", va="top",
                fontsize=8, color="#444444", linespacing=1.4)

    # Arrows between nodes
    arrow_xs = [(2.0 + box_w/2 + 0.05, 4.8 - box_w/2 - 0.05),
                (4.8 + box_w/2 + 0.05, 7.6 - box_w/2 - 0.05),
                (7.6 + box_w/2 + 0.05, 10.6 - box_w/2 - 0.05),
                (10.6 + box_w/2 + 0.05, 13.6 - box_w/2 - 0.05)]
    for x1, x2 in arrow_xs:
        ax.annotate("", xy=(x2, 2.0), xytext=(x1, 2.0),
                    arrowprops=dict(arrowstyle="-|>", color="#999999", lw=1.5))

    # Legend row
    leg_items = [
        mpatches.Patch(facecolor="#d0d0d0", edgecolor="#888888", label="Markov-era"),
        mpatches.Patch(facecolor="#a8c8f0", edgecolor="#2060c0", label="Deep learning-era"),
        mpatches.Patch(facecolor="#a0d8d0", edgecolor="#288070", label="Multimodal-era"),
        mpatches.Patch(facecolor="#c8a8e8", edgecolor="#7040b0", label="This work"),
    ]
    ax.legend(handles=leg_items, loc="lower center", ncol=4,
              fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.05))

    save(fig, "slide_nba_origins.png")


# ══════════════════════════════════════════════════════════════════════════════
# Slide 2 — Alternative NBA Approaches Comparison
# ══════════════════════════════════════════════════════════════════════════════
def slide_nba_alternatives():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(7, 6.7, "Traditional NBA Approaches: Strengths and Limitations",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#1a1a2e")

    cols = [
        {
            "x": 2.3, "title": "Markov Chains\n(FPMC, 2010)",
            "fc": "#e8e8e8", "ec": "#888888", "tc": "#333333",
            "strength": ["✓ Simple & interpretable", "✓ Low data requirement", "✓ Personalized transitions"],
            "weakness": ["✗ First-order only", "✗ No long-range context", "✗ No content signals"],
        },
        {
            "x": 7.0, "title": "RNN / GRU\n(GRU4Rec, 2016)",
            "fc": "#dce8f8", "ec": "#4a7abf", "tc": "#0d2a5e",
            "strength": ["✓ Captures sequence history", "✓ Handles variable length", "✓ Scalable to large catalogs"],
            "weakness": ["✗ No visual signals", "✗ Cold-start failure", "✗ Fixed weights at inference"],
        },
        {
            "x": 11.7, "title": "Self-Attention\n(SASRec, 2018)",
            "fc": "#d8eef8", "ec": "#2060c0", "tc": "#0d2a5e",
            "strength": ["✓ Long-range dependencies", "✓ Parallelizable training", "✓ Selective item attention"],
            "weakness": ["✗ ID-embedding only", "✗ Sparse item blindspot", "✗ No in-session adaptation"],
        },
    ]

    for col in cols:
        x = col["x"]
        # Column header box
        rect = FancyBboxPatch((x - 2.1, 5.0), 4.2, 1.35,
                              boxstyle="round,pad=0.1", lw=2,
                              edgecolor=col["ec"], facecolor=col["fc"])
        ax.add_patch(rect)
        ax.text(x, 5.68, col["title"], ha="center", va="center",
                fontsize=12, fontweight="bold", color=col["tc"])

        # Strengths section
        ax.text(x, 4.65, "Strengths", ha="center", va="center",
                fontsize=10, fontweight="bold", color="#226622")
        for i, s in enumerate(col["strength"]):
            ax.text(x, 4.25 - i * 0.42, s, ha="center", va="center",
                    fontsize=9, color="#226622")

        # Weaknesses section
        ax.text(x, 2.9, "Limitations", ha="center", va="center",
                fontsize=10, fontweight="bold", color="#aa2222")
        for i, w in enumerate(col["weakness"]):
            ax.text(x, 2.50 - i * 0.42, w, ha="center", va="center",
                    fontsize=9, color="#aa2222")

        # Vertical separator
        ax.plot([x - 2.1, x + 2.1], [3.10, 3.10], color="#cccccc", lw=1, ls="--")

    # Shared gap banner
    banner = FancyBboxPatch((0.4, 0.25), 13.2, 0.85,
                            boxstyle="round,pad=0.1", lw=2.5,
                            edgecolor="#cc4400", facecolor="#fff0e8")
    ax.add_patch(banner)
    ax.text(7, 0.68, "Shared Gap: Cannot model visual item attributes · Cold-start vulnerability · "
                     "No in-session adaptation",
            ha="center", va="center", fontsize=10.5, color="#aa2200", fontweight="bold")

    save(fig, "slide_nba_alternatives.png")


# ══════════════════════════════════════════════════════════════════════════════
# Slide 3 — End-to-End System Performance
# ══════════════════════════════════════════════════════════════════════════════
def slide_system_performance():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(7, 6.7, "System Performance: Dual-Pipeline NBA Recommendation",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#1a1a2e")

    # ── LEFT: Pipeline Bars ─────────────────────────────────────────────
    bar_x0, bar_y_base = 1.0, 1.2
    bar_max_w = 4.0

    metrics = [
        ("Pipeline A\n(Cleora + BGE-M3)", 0.9047, "#2060c0", "#a8c8f0"),
        ("Pipeline B\n(DIF-SASRec)",       0.7745, "#206060", "#a0d8d0"),
    ]

    ax.text(3.0, 5.85, "Isolated Pipeline HR@10 (sampled eval, N=99 neg)",
            ha="center", va="center", fontsize=10, color="#444444")

    for i, (label, score, ec, fc) in enumerate(metrics):
        y = bar_y_base + i * 1.9 + 0.3
        w = score * bar_max_w
        rect = FancyBboxPatch((bar_x0, y), w, 1.1,
                              boxstyle="round,pad=0.05", lw=2, edgecolor=ec, facecolor=fc)
        ax.add_patch(rect)
        ax.text(bar_x0 + w + 0.12, y + 0.55, f"HR@10 = {score:.4f}",
                va="center", fontsize=11, fontweight="bold", color=ec)
        ax.text(bar_x0 - 0.05, y + 0.55, label,
                ha="right", va="center", fontsize=9.5, color="#333333")

    # ── CENTER: Routing box ──────────────────────────────────────────────
    cx = 7.4
    rect_r = FancyBboxPatch((cx - 1.3, 2.8), 2.6, 1.4,
                            boxstyle="round,pad=0.1", lw=2.5,
                            edgecolor="#7040b0", facecolor="#e8d8f8")
    ax.add_patch(rect_r)
    ax.text(cx, 3.72, "Routing Layer", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#5020a0")
    ax.text(cx, 3.28, "97.4% user coverage\n(≥5 clicks → personalized)",
            ha="center", va="center", fontsize=9, color="#5020a0")

    # Routing arrows to pipelines
    for ya in [1.75, 3.45]:
        ax.annotate("", xy=(cx - 1.3, ya), xytext=(5.2, 3.3),
                    arrowprops=dict(arrowstyle="-|>", color="#888888", lw=1.5,
                                   connectionstyle="arc3,rad=0.1"))

    # ── RIGHT: Phase 2 block ─────────────────────────────────────────────
    rx = 10.8
    rect_p2 = FancyBboxPatch((rx - 1.5, 2.5), 3.0, 2.0,
                             boxstyle="round,pad=0.1", lw=2.5,
                             edgecolor="#c05020", facecolor="#fdf0e0")
    ax.add_patch(rect_p2)
    ax.text(rx, 4.25, "Phase 2 — AgentPool", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#c05020")
    ax.text(rx, 3.80, "Online fine-tuning", ha="center", va="center",
            fontsize=9.5, color="#c05020")
    ax.text(rx, 3.40, "1 gradient step / click", ha="center", va="center",
            fontsize=9, color="#555555")
    ax.text(rx, 3.00, "8 agents · ~1.18 GB VRAM", ha="center", va="center",
            fontsize=8.5, color="#777777")

    # Upward delta arrow on Phase 2
    ax.annotate("", xy=(rx, 4.55), xytext=(rx, 4.25),
                arrowprops=dict(arrowstyle="-|>", color="#c05020", lw=2.0))
    ax.text(rx + 0.18, 4.65, "↑ HR@10 uplift\n[DELTA_RESULT]",
            va="bottom", fontsize=9, color="#c05020", style="italic")

    # Arrow from routing to Phase 2
    ax.annotate("", xy=(rx - 1.5, 3.5), xytext=(cx + 1.3, 3.5),
                arrowprops=dict(arrowstyle="-|>", color="#888888", lw=1.5))

    # ── Bottom summary bar ───────────────────────────────────────────────
    banner = FancyBboxPatch((0.4, 0.1), 13.2, 0.75,
                            boxstyle="round,pad=0.08", lw=2,
                            edgecolor="#2040a0", facecolor="#e8eef8")
    ax.add_patch(banner)
    ax.text(7, 0.48, "System value > sum of isolated pipeline scores:  "
                     "Routing (97.4% coverage)  +  Phase 2 (in-session uplift)  "
                     "+  Pipeline A∪B deduplication",
            ha="center", va="center", fontsize=9.5, color="#1a2a80", fontweight="bold")

    save(fig, "slide_system_performance.png")


if __name__ == "__main__":
    print("Generating slides...")
    slide_nba_origins()
    slide_nba_alternatives()
    slide_system_performance()
    print("Done.")
