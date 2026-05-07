"""Run all figure generation code from the notebooks."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from utils import (
    setup_style, save_fig, FIG_DIR, ROOT,
    load_results_history, load_multiseed, load_encoder_comparison, load_profiling,
    PALETTE, STRATEGY_ORDER, STRATEGY_LABELS,
)

setup_style()
print(f"Writing figures to: {FIG_DIR}")

# ── Figure 1: Dataset statistics ──────────────────────────────────────────────
print("\n[1/8] Dataset statistics...")
eval_path = ROOT / 'evaluation' / 'eval_users.json'
with open(eval_path, encoding='utf-8') as f:
    all_users = json.load(f)

train_lens = [len(u['train_clicks']) for u in all_users]

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

ax = axes[0]
bins = [1, 5, 10, 20, 50, 100, 200, 500, 1000, max(train_lens) + 1]
counts, edges = np.histogram(train_lens, bins=bins)
labels = [f'{int(edges[i])}–{int(edges[i+1])-1}' for i in range(len(counts))]
labels[-1] = f'{int(edges[-2])}+'
bars = ax.bar(range(len(counts)), counts, color='#61AFEF', edgecolor='white', linewidth=0.5)
ax.set_xticks(range(len(counts)))
ax.set_xticklabels(labels, rotation=40, ha='right', fontsize=9)
ax.set_xlabel('Training sequence length')
ax.set_ylabel('Number of users')
ax.set_title('(a) Distribution of training sequence lengths')
for bar, cnt in zip(bars, counts):
    if cnt > 1000:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                f'{cnt/1000:.0f}k', ha='center', va='bottom', fontsize=8)

ax2 = axes[1]
percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
pct_values  = [int(np.percentile(train_lens, p)) for p in percentiles]
ax2.barh(range(len(percentiles)), pct_values, color='#98C379', edgecolor='white')
ax2.set_yticks(range(len(percentiles)))
ax2.set_yticklabels([f'p{p}' for p in percentiles])
ax2.set_xlabel('Sequence length (clicks)')
ax2.set_title('(b) Percentiles of training sequence length')
for i, v in enumerate(pct_values):
    ax2.text(v + 2, i, str(v), va='center', fontsize=9)

save_fig('fig_dataset_statistics', fig)
plt.close(fig)

# ── Figure 2: Main results bar chart ─────────────────────────────────────────
print("[2/8] Main results bar chart...")
canonical = {
    'Random Baseline':      dict(hr5=0.050,  hr10=0.100,  ndcg10=0.0454, mrr10=None),
    'Content Baseline':     dict(hr5=0.3597, hr10=0.4346, ndcg10=0.3022, mrr10=0.2609),
    'GRU-SeqDQN':           dict(hr5=0.0519, hr10=0.1031, ndcg10=0.0472, mrr10=0.0306),
    'DIF-SASRec':           dict(hr5=0.5877, hr10=0.7745, ndcg10=0.5024, mrr10=0.4191),
    'Pipeline A (Cleora)':  dict(hr5=0.5750, hr10=0.9047, ndcg10=0.5393, mrr10=0.4302),
    'System (A∪B)':         dict(hr5=None,   hr10=0.9736, ndcg10=0.5571, mrr10=None),
}

models = STRATEGY_ORDER
hr10   = [canonical[m]['hr10']   for m in models]
ndcg10 = [canonical[m]['ndcg10'] for m in models]
x = np.arange(len(models))
w = 0.38

fig, ax = plt.subplots(figsize=(9, 4.5))
colors_hr = [PALETTE[m] for m in models]
bars_hr   = ax.bar(x - w/2, hr10,   w, label='HR@10',   color=colors_hr,  edgecolor='white', linewidth=0.6)
bars_ndcg = ax.bar(x + w/2, ndcg10, w, label='NDCG@10', color=colors_hr,  edgecolor='white', linewidth=0.6, alpha=0.65, hatch='//')

for bar, val in zip(bars_hr, hr10):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)
for bar, val in zip(bars_ndcg, ndcg10):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels([STRATEGY_LABELS[m] for m in models], fontsize=9)
ax.set_ylabel('Score')
ax.set_ylim(0, 1.08)
ax.set_title('Main evaluation results (N=99 negatives, 100k users, seed=42)')
solid_p = mpatches.Patch(color='#555', label='HR@10')
hatch_p = mpatches.Patch(facecolor='#555', alpha=0.65, hatch='//', label='NDCG@10')
ax.legend(handles=[solid_p, hatch_p], loc='upper left')
ax.axvline(x=len(models)-1.5, color='#555', linestyle='--', linewidth=0.8, alpha=0.5)
ax.text(len(models)-1.45, 1.04, 'Combined system →', fontsize=8, color='#555', style='italic')
save_fig('fig_main_results', fig)
plt.close(fig)

# ── Figure 3: N-sensitivity ────────────────────────────────────────────────────
print("[3/8] N-sensitivity chart...")
strategies_n = ['Content Baseline', 'GRU-SeqDQN', 'DIF-SASRec', 'Pipeline A (Cleora)']
n99_hr10  = [0.4346, 0.1031, 0.7745, 0.9047]
n999_hr10 = [0.2122, 0.0141, 0.3142, 0.3272]
x = np.arange(len(strategies_n))
w = 0.38

fig, ax = plt.subplots(figsize=(8, 4))
colors = [PALETTE[s] for s in strategies_n]
b1 = ax.bar(x - w/2, n99_hr10,  w, label='N = 99',  color=colors, edgecolor='white')
b2 = ax.bar(x + w/2, n999_hr10, w, label='N = 999', color=colors, edgecolor='white', alpha=0.55, hatch='..')
for bar, val in zip(b1, n99_hr10):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)
for bar, val in zip(b2, n999_hr10):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels([STRATEGY_LABELS[s] for s in strategies_n], fontsize=9)
ax.set_ylabel('HR@10')
ax.set_ylim(0, 1.08)
ax.set_title('HR@10 vs. Negative Sample Size (100k users)')
ax.legend()
ax.axhline(0.100, color='#9E9E9E', linestyle='--', linewidth=0.9)
ax.axhline(0.010, color='#9E9E9E', linestyle=':', linewidth=0.9)
save_fig('fig_n_sensitivity', fig)
plt.close(fig)

# ── Figure 4: Multiseed stability ─────────────────────────────────────────────
print("[4/8] Multiseed stability...")
multiseed = load_multiseed()
seeds     = multiseed['seeds']
hr10_vals = [s['hr10']   for s in multiseed['per_seed']]
ndcg_vals = [s['ndcg10'] for s in multiseed['per_seed']]
mean_hr   = multiseed['mean_hr10']
std_hr    = multiseed['std_hr10']
mean_nd   = multiseed['mean_ndcg10']
std_nd    = multiseed['std_ndcg10']

fig, axes = plt.subplots(1, 2, figsize=(9, 4))
for ax, vals, mean, std, metric, color in [
    (axes[0], hr10_vals, mean_hr, std_hr, 'HR@10',   '#61AFEF'),
    (axes[1], ndcg_vals, mean_nd, std_nd, 'NDCG@10', '#98C379'),
]:
    bars = ax.bar(range(len(seeds)), vals, color=color, edgecolor='white', alpha=0.85)
    ax.axhline(mean, color='#E06C75', linewidth=1.5, linestyle='--', label=f'Mean={mean:.4f}')
    ax.fill_between([-0.5, len(seeds)-0.5], mean - std, mean + std,
                    color='#E06C75', alpha=0.15, label=f'±σ={std:.4f}')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{val:.4f}', ha='center', va='bottom', fontsize=8)
    ax.set_xticks(range(len(seeds)))
    ax.set_xticklabels([f'seed={s}' for s in seeds], rotation=30, ha='right', fontsize=9)
    ax.set_ylabel(metric)
    lo = min(vals) - 0.01
    hi = max(vals) + 0.015
    ax.set_ylim(lo, hi)
    ax.set_title(f'DIF-SASRec {metric} across seeds')
    ax.legend(fontsize=9)
save_fig('fig_multiseed_stability', fig)
plt.close(fig)

# ── Figure 5: Complementarity ─────────────────────────────────────────────────
print("[5/8] Complementarity chart...")
comp = {'A∩B (both hit)': 70557, 'A only': 19909, 'B only': 6893, 'Neither': 2641}
total = sum(comp.values())
labels_comp = list(comp.keys())
values_comp = list(comp.values())
pcts_comp   = [v / total * 100 for v in values_comp]
colors_comp = ['#C678DD', '#98C379', '#61AFEF', '#9E9E9E']

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
ax = axes[0]
wedges, texts, autotexts = ax.pie(
    values_comp, labels=None, colors=colors_comp, autopct='%1.1f%%',
    startangle=90, pctdistance=0.75,
    wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2),
)
for at in autotexts:
    at.set_fontsize(10)
ax.legend(wedges, [f'{l} ({v:,})' for l, v in zip(labels_comp, values_comp)],
          loc='lower center', bbox_to_anchor=(0.5, -0.12), fontsize=9, ncol=2)
ax.set_title('(a) Hit distribution across pipelines\n(100k users, N=99)')

ax2 = axes[1]
bars = ax2.barh(range(len(labels_comp)), values_comp, color=colors_comp, edgecolor='white')
ax2.set_yticks(range(len(labels_comp)))
ax2.set_yticklabels(labels_comp)
ax2.set_xlabel('Number of users')
ax2.set_title('(b) Absolute counts')
for bar, v, p in zip(bars, values_comp, pcts_comp):
    ax2.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
             f'{v:,} ({p:.1f}%)', va='center', fontsize=9)
ax2.set_xlim(0, max(values_comp) * 1.3)
save_fig('fig_complementarity', fig)
plt.close(fig)

# ── Figure 6: Encoder comparison (query retrieval) ────────────────────────────
print("[6/8] Encoder query comparison...")
enc = load_encoder_comparison()
qg = enc['query_test']['per_group']
groups = list(qg.keys())
bge_vals   = [qg[g]['bge_avg_gp']   for g in groups]
blair_vals = [qg[g]['blair_avg_gp'] for g in groups]
group_labels_map = {'short': 'Short (EN)', 'medium': 'Medium (EN)', 'long': 'Long (EN)',
                    'vi_short': 'Short (VI)', 'vi_long': 'Long (VI)'}

x = np.arange(len(groups))
w = 0.38
fig, ax = plt.subplots(figsize=(8, 4))
b1 = ax.bar(x - w/2, bge_vals,   w, label='BGE-M3 (current)', color='#61AFEF', edgecolor='white')
b2 = ax.bar(x + w/2, blair_vals, w, label='BLaIR (legacy)',   color='#E06C75', edgecolor='white')
for bar, v in zip(b1, bge_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
            f'{v:.2f}', ha='center', va='bottom', fontsize=8)
for bar, v in zip(b2, blair_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
            f'{v:.2f}', ha='center', va='bottom', fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels([group_labels_map[g] for g in groups], fontsize=10)
ax.set_ylabel('Precision@10')
ax.set_ylim(0, 0.72)
ax.set_title('Search query retrieval precision by query type')
ax.legend()
ax.axvspan(2.5, len(groups) - 0.5, alpha=0.06, color='#98C379')
ax.text(3.5, 0.67, 'Vietnamese queries', ha='center', fontsize=9, style='italic', color='#4B8B3B')
save_fig('fig_encoder_query_comparison', fig)
plt.close(fig)

# ── Figure 7: HNSW latency ────────────────────────────────────────────────────
print("[7/8] HNSW latency chart...")
hnsw = enc['hnsw_recall']
fig, axes = plt.subplots(1, 2, figsize=(9, 4))
ax = axes[0]
index_types = ['Flat (exact)', 'HNSW (ANN)']
p50s = [hnsw['flat_p50_ms'], hnsw['hnsw_p50_ms']]
p95s = [hnsw['flat_p95_ms'], hnsw['hnsw_p95_ms']]
x = np.arange(len(index_types))
w = 0.38
b1 = ax.bar(x - w/2, p50s, w, label='P50', color=['#5C85D6', '#98C379'], edgecolor='white')
b2 = ax.bar(x + w/2, p95s, w, label='P95', color=['#5C85D6', '#98C379'], edgecolor='white', alpha=0.6, hatch='//')
for bar, v in zip(list(b1) + list(b2), p50s + p95s):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f'{v:.0f}ms', ha='center', va='bottom', fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(index_types)
ax.set_ylabel('Latency (ms)')
ax.set_title('(a) Search latency: Flat vs HNSW')
solid_p = mpatches.Patch(color='#555', label='P50')
hatch_p = mpatches.Patch(facecolor='#555', alpha=0.6, hatch='//', label='P95')
ax.legend(handles=[solid_p, hatch_p])

ax2 = axes[1]
recall = hnsw['mean_recall_at_k']
ax2.barh(['HNSW Recall@k'], [recall],  color='#C678DD', edgecolor='white')
ax2.barh(['Perfect Recall'], [1.0],    color='#9E9E9E', alpha=0.3, edgecolor='white')
ax2.set_xlim(0, 1.1)
ax2.set_xlabel('Recall')
ax2.set_title('(b) HNSW approximate recall')
ax2.text(recall + 0.01, 0, f'{recall:.4f}', va='center', fontsize=10)
ax2.axvline(1.0, color='#9E9E9E', linestyle='--', linewidth=0.8)
save_fig('fig_hnsw_latency', fig)
plt.close(fig)

# ── Figure 8: Search pipeline latency optimisation ────────────────────────────
print("[8/8] Search pipeline latency...")
profiling = load_profiling()
stages_to_show = [
    ('Baseline',          profiling[0]['key_metrics']),
    ('Translator\nOpt.',  profiling[5]['key_metrics']),
    ('Quality\nGate',     profiling[7]['key_metrics']),
    ('QG (warm)',         profiling[10]['key_metrics']),
    ('Translation\nImprv.',profiling[15]['key_metrics']),
    ('Cold\nCache',       profiling[16]['key_metrics']),
]
labels_s = [s[0] for s in stages_to_show]
e2e_vals  = [s[1]['e2e_wall_clock_ms']  for s in stages_to_show]
trans_vals = [s[1]['translate_ms']      for s in stages_to_show]
enc_vals   = [s[1]['encode_text_ms']    for s in stages_to_show]
other_vals = [max(0, e - t - en) for e, t, en in zip(e2e_vals, trans_vals, enc_vals)]

x = np.arange(len(labels_s))
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.bar(x, trans_vals, label='Translation',        color='#E06C75', edgecolor='white')
ax.bar(x, enc_vals,   bottom=trans_vals,           label='BGE-M3 encode',   color='#61AFEF', edgecolor='white')
ax.bar(x, other_vals, bottom=[t+e for t,e in zip(trans_vals, enc_vals)],
       label='FAISS + RRF + overhead', color='#C678DD', edgecolor='white')
for xi, e2e in zip(x, e2e_vals):
    ax.text(xi, e2e + 10, f'{e2e:.0f}ms', ha='center', va='bottom', fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels(labels_s, fontsize=9)
ax.set_ylabel('Latency (ms)')
ax.set_title('Search pipeline end-to-end latency by optimisation stage')
ax.legend(loc='upper right')
save_fig('fig_search_pipeline_latency', fig)
plt.close(fig)

print(f"\nAll figures saved to {FIG_DIR}")
import os
figs = list(FIG_DIR.glob('*.pdf'))
print(f"Generated {len(figs)} PDF figures:")
for f in sorted(figs):
    print(f"  {f.name}")
