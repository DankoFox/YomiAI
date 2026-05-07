"""Shared utilities for Chapter 5 experiment notebooks."""
import json
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
EVAL_DIR = ROOT / "evaluation"
PROF_DIR = ROOT / "profiling"
FIG_DIR = ROOT / "Captsone" / "images" / "chapter5"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
PALETTE = {
    "Random Baseline":        "#9E9E9E",
    "Content Baseline":       "#5C85D6",
    "GRU-SeqDQN":             "#E06C75",
    "DIF-SASRec":             "#61AFEF",
    "Pipeline A (Cleora)":    "#98C379",
    "System (A∪B)":           "#C678DD",
    # aliases
    "Pipeline A":             "#98C379",
    "BGE-M3 (current)":       "#61AFEF",
    "BLaIR (legacy)":         "#E06C75",
}

def setup_style():
    matplotlib.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def save_fig(name: str, fig=None, tight=True):
    """Save figure to chapter5 images dir as both PDF and PNG."""
    if fig is None:
        fig = plt.gcf()
    if tight:
        fig.tight_layout()
    out_pdf = FIG_DIR / f"{name}.pdf"
    out_png = FIG_DIR / f"{name}.png"
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", bbox_inches="tight", dpi=300)
    print(f"Saved: {out_pdf.name}, {out_png.name}")


# ── Data loaders ─────────────────────────────────────────────────────────────

def load_results_history():
    with open(EVAL_DIR / "results_history.json", encoding="utf-8") as f:
        return json.load(f)


def load_multiseed():
    with open(EVAL_DIR / "multiseed_results.json", encoding="utf-8") as f:
        return json.load(f)


def load_encoder_comparison():
    path = sorted((EVAL_DIR).glob("encoder_comparison_*.json"))[-1]
    with open(path, encoding="utf-8", errors="replace") as f:
        return json.load(f)


def load_profiling():
    entries = []
    with open(PROF_DIR / "history.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def get_canonical_run(history, n_users=100_000, negatives=99, run_id=None):
    """Return the latest canonical run matching criteria."""
    candidates = [
        r for r in history
        if r.get("n_eval_users", 0) >= n_users
        and r.get("negatives", 0) == negatives
        and (run_id is None or r["run_id"] == run_id)
    ]
    return max(candidates, key=lambda r: r["run_id"])


def get_all_strategy_run(history, negatives=99):
    """Return the run that evaluated all 5 strategies at once."""
    candidates = [
        r for r in history
        if r.get("negatives", 0) == negatives
        and len(r.get("results", {})) >= 4
    ]
    # Prefer largest n_eval_users
    return max(candidates, key=lambda r: r.get("n_eval_users", 0))


# ── Metric helpers ────────────────────────────────────────────────────────────

STRATEGY_ORDER = [
    "Random Baseline",
    "Content Baseline",
    "GRU-SeqDQN",
    "DIF-SASRec",
    "Pipeline A (Cleora)",
    "System (A∪B)",
]

STRATEGY_LABELS = {
    "Random Baseline":      "Random",
    "Content Baseline":     "Content\nBaseline",
    "GRU-SeqDQN":           "GRU-SeqDQN",
    "DIF-SASRec":           "DIF-SASRec",
    "Pipeline A (Cleora)":  "Pipeline A\n(Cleora+BGE)",
    "System (A∪B)":         r"System ($A \cup B$)",
}
