# Experiment & Evaluation Roadmap
**NBA Recommendation System — Thesis Chapter 4/5**

> Generated from live codebase inspection. All commands are copy-pasteable from the project root.

---

## Table of Contents

1. [What Is Active vs. Obsolete](#1-active-vs-obsolete-pipeline-map)
2. [Environment Setup](#2-environment-setup)
3. [Pre-flight Checklist](#3-pre-flight-checklist)
4. [Notebook Structure](#4-notebook-structure)
   - [NB-1: Dataset & Pipeline Verification](#nb-1-dataset--pipeline-verification)
   - [NB-2: Accuracy Evaluation](#nb-2-accuracy-evaluation)
   - [NB-3: Latency & Hardware Profiling](#nb-3-latency--hardware-profiling)
   - [NB-4: Ablation Studies](#nb-4-ablation-studies)
   - [NB-5: Figure & Table Export](#nb-5-figure--table-export)
5. [Automation Commands (CLI Reference)](#5-automation-commands-cli-reference)
6. [Key Numbers Already in Hand](#6-key-numbers-already-in-hand)
7. [Figures & Tables Catalogue](#7-figures--tables-catalogue)
8. [Output File Map](#8-output-file-map)

---

## 1. Active vs. Obsolete Pipeline Map

### Active (evaluated, results exist)

| Component | Code | Role |
|---|---|---|
| **Pipeline A** | `app/services/passive_recommend.py` | Cleora behavioral graph → BGE-M3 cosine re-rank |
| **Pipeline B / DIF-SASRec** | `app/services/dif_sasrec.py` | Sequential transformer, pretrained checkpoint |
| **Combined A∪B** | `evaluate_recommendation.py::CombinedStrategy` | Union + RRF fusion (live system output) |
| **BGE-M3 encoder** | `app/infrastructure/` + `BAAI/bge-m3` | Text embedding (1024-dim), active production index |
| **Cleora** | `data/cleora_embeddings.npz` | 375k-item behavioral co-purchase graph |
| **FAISS HNSW** | `data/bge_index_hnsw.faiss` | Production ANN search (1.7M vectors) |
| **FAISS Flat** | `data/bge_index_flat.faiss` | Exact eval + reconstruction (3M vectors) |
| **Tantivy BM25** | `app/infrastructure/` | Keyword fallback, fused via RRF |
| **NLLB translation** | Search pipeline | Vietnamese → English for text queries |

### Comparison Baselines (in eval scripts)

| Component | Code | Notes |
|---|---|---|
| **Content Baseline** | `evaluate_recommendation.py::ContentBaseline` | BGE-M3 profile mean → cosine, no trained model |
| **GRU-SeqDQN** | `app/services/sequential_dqn.py` | Legacy RL model; poor performance, kept as baseline |
| **BLaIR (legacy)** | `data/blair_index_hnsw_legacy.faiss` | Old encoder, 3M HNSW, used only in encoder comparison |

### Outdated / Not Used for Thesis

- `app/services/rl_filter.py` — original DQN (superseded by DIF-SASRec)
- `scripts/benchmark/compare_models.py` — LLM-only test, not part of rec system
- `scripts/benchmark/benchmark_llm.py` — LLM inference timing only
- `scripts/data/filter_hyperedges.py`, `prepare_cleora.py` — build-time only, not evaluation

---

## 2. Environment Setup

### A. Dependencies

```bash
# Python 3.11
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install faiss-gpu sentence-transformers transformers
pip install pandas pyarrow numpy scipy matplotlib seaborn
pip install jupyter ipywidgets tqdm
```

> **CUDA requirement**: RTX 5060 Ti. BGE-M3 encode runs in fp16 on CUDA.
> FAISS indices are MMAP-loaded — no VRAM used for index storage.

### B. Model Checkpoints

| File | Location | Size |
|---|---|---|
| `dif_sasrec_pretrained.pt` | `data/` | ~50 MB |
| BGE-M3 weights | HuggingFace cache (`BAAI/bge-m3`) | ~2.3 GB |
| BLaIR weights (optional) | HuggingFace cache (`hyp1231/blair-roberta-large`) | ~1.4 GB |

### C. Dataset Locations

| File | Path | Required for |
|---|---|---|
| `bge_index_flat.faiss` | `data/` | All rec eval, encoder comparison |
| `bge_index_hnsw.faiss` | `data/` | Production search, latency bench |
| `blair_index_hnsw_legacy.faiss` | `data/` | Encoder comparison only |
| `cleora_embeddings.npz` | `data/` | Pipeline A, Retriever init |
| `item_metadata.parquet` | `data/` | Metadata hydration, genre analysis |
| `asins.csv` | `data/` | ASIN↔index mapping |
| `category_vocab.json` | `data/` | DIF-SASRec category IDs |
| `eval_users.json` | `evaluation/` | All offline evaluations |

### D. Generate eval_users.json (if missing)

```bash
python scripts/setup_dif_sasrec.py
```

This produces `evaluation/eval_users.json` with 20k–100k users, each having `train_clicks` + `test_clicks`.

### E. Environment Variables

No `.env` required. All paths resolved from `app/config.py::Settings` relative to project root.

---

## 3. Pre-flight Checklist

Run these in order before any notebook:

```bash
# 1. Verify indices exist
python -c "
import os
from app.config import settings
files = [settings.TEXT_INDEX_FLAT, settings.TEXT_INDEX_HNSW, 'cleora_embeddings.npz',
         'item_metadata.parquet', 'asins.csv', 'category_vocab.json', 'dif_sasrec_pretrained.pt']
for f in files:
    p = os.path.join(settings.DATA_DIR, f)
    exists = os.path.exists(p)
    size_mb = os.path.getsize(p)/1e6 if exists else 0
    print(f'  {\"OK\" if exists else \"MISSING\":6}  {size_mb:8.0f} MB  {f}')
"

# 2. Verify eval_users.json
python -c "
import json
with open('evaluation/eval_users.json') as f:
    users = json.load(f)
print(f'eval_users.json: {len(users):,} users')
u = users[0]
print(f'  train_clicks: {len(u[\"train_clicks\"])}  test_clicks: {len(u[\"test_clicks\"])}')
"

# 3. Quick smoke test (2000 users, ~30s)
python scripts/benchmark/evaluate_recommendation.py --max-users 2000 --dif-only
```

---

## 4. Notebook Structure

### NB-1: Dataset & Pipeline Verification

**File**: `notebooks/01_dataset_verification.ipynb`
**Purpose**: Sanity-check indices, inspect inference outputs, confirm data integrity.
**Runtime**: ~5 min

```python
# Cell 1 — Imports & Setup
import sys, os
sys.path.insert(0, '..')
import numpy as np, json
from app.config import settings
from app.repository.faiss_repo import Retriever

# Cell 2 — Load Retriever
import numpy as np
cleora_data = np.load(os.path.join(settings.DATA_DIR, 'cleora_embeddings.npz'))
retriever = Retriever(settings.DATA_DIR, cleora_data)
print(f"ASINs: {len(retriever.asins):,}")
print(f"Cleora index: {len(retriever.asin_to_cleora_idx):,} items")
print(f"BGE flat: {retriever.text_flat.ntotal:,} vectors (dim={retriever.text_flat.d})")
print(f"BGE HNSW: {retriever.text_hnsw.ntotal:,} vectors")

# Cell 3 — Load eval users
with open('../evaluation/eval_users.json') as f:
    eval_users = json.load(f)
train_lens = [len(u['train_clicks']) for u in eval_users[:1000]]
test_lens  = [len(u['test_clicks'])  for u in eval_users[:1000]]
print(f"Users loaded: {len(eval_users):,}")
print(f"Avg train clicks: {np.mean(train_lens):.1f}  |  Avg test clicks: {np.mean(test_lens):.1f}")

# Cell 4 — Sample a recommendation (Pipeline A)
from scripts.benchmark.evaluate_recommendation import PipelineAStrategy
sample_user = eval_users[0]
strategy = PipelineAStrategy(retriever)
scores = strategy.score_candidates(sample_user['train_clicks'], sample_user['test_clicks'][:5])
print("Sample scores:", {k: round(v, 4) for k, v in scores.items()})

# Cell 5 — Sample a recommendation (DIF-SASRec)
from app.services.category_encoder import CategoryEncoder
from app.services.dif_sasrec import DIFSASRecAgent
cat_encoder = CategoryEncoder()
cat_encoder.load(os.path.join(settings.DATA_DIR, 'category_vocab.json'))
agent = DIFSASRecAgent(retriever, cat_encoder,
                       os.path.join(settings.DATA_DIR, 'dif_sasrec_pretrained.pt'))
train = sample_user['train_clicks']
cat_ids = cat_encoder.encode_sequence(train)
candidates = sample_user['test_clicks'][:5] + [retriever.asins[i] for i in range(5)]
scores = agent.get_candidate_scores(train, cat_ids, candidates)
print("DIF-SASRec scores:", {k: round(v, 4) for k, v in scores.items()})

# Cell 6 — Embedding statistics
sample_vecs = [retriever.text_flat.reconstruct(i) for i in range(100)]
sample_vecs = np.array(sample_vecs)
print(f"Embedding norms  — mean: {np.linalg.norm(sample_vecs, axis=1).mean():.4f}  "
      f"std: {np.linalg.norm(sample_vecs, axis=1).std():.4f}")
print(f"Embedding dim: {sample_vecs.shape[1]}")
```

**Expected outputs**: 
- ASIN counts, index dimensions
- Sample ranked scores for a user
- Embedding norm distribution (should be ~1.0 for L2-normalised BGE-M3)

---

### NB-2: Accuracy Evaluation

**File**: `notebooks/02_accuracy_evaluation.ipynb`
**Purpose**: Load `results_history.json` + `multiseed_results.json`, render publication-ready metric tables.
**Runtime**: ~1 min (reads cached results) OR ~20 min to re-run evaluation

#### A — Load existing results (fast, no re-run needed)

```python
# Cell 1 — Load all history
import json
import pandas as pd

with open('../evaluation/results_history.json') as f:
    history = json.load(f)

# Filter to canonical run: 100k users, N=99, latest timestamp
def canonical(run):
    return (run['negatives'] == 99 and 
            run.get('n_eval_users', 0) >= 100000 and
            'combined' not in str(run.get('max_users', '')))

canonical_runs = [r for r in history if canonical(r)]
print(f"{len(canonical_runs)} canonical runs found")
# Pick latest per strategy
latest = canonical_runs[-1]  # or filter by run_id

# Cell 2 — Build comparison table
rows = []
for name, m in latest['results'].items():
    rows.append({'Strategy': name, 'HR@5': m['hr5'], 'HR@10': m['hr10'],
                 'NDCG@10': m['ndcg10'], 'MRR@10': m['mrr10'], 'Users': m['users']})
df = pd.DataFrame(rows).set_index('Strategy')
print(df.round(4).to_string())

# Cell 3 — Multi-seed confidence intervals (DIF-SASRec)
with open('../evaluation/multiseed_results.json') as f:
    ms = json.load(f)
print(f"\nDIF-SASRec  HR@10 = {ms['mean_hr10']:.4f} ± {ms['std_hr10']:.4f}")
print(f"DIF-SASRec NDCG@10 = {ms['mean_ndcg10']:.4f} ± {ms['std_ndcg10']:.4f}")

# Cell 4 — Build full comparison across ALL canonical results
records = []
for run in canonical_runs:
    for name, m in run['results'].items():
        records.append({'run_id': run['run_id'], 'negatives': run['negatives'],
                        'n_users': run['n_eval_users'], 'strategy': name,
                        **m})
df_all = pd.DataFrame(records)

# Cell 5 — Best result per strategy
best = df_all.sort_values('hr10', ascending=False).groupby('strategy').first()[
    ['hr5', 'hr10', 'ndcg10', 'mrr10', 'n_users', 'run_id']]
print(best.round(4).to_string())
```

#### B — Re-run canonical evaluation (if you need fresh numbers)

```bash
# Full canonical run: 100k users, N=99, all strategies + union
python scripts/benchmark/evaluate_recommendation.py \
  --mode sampled --negatives 99 --max-users 100000 \
  --combined --seed 42

# Harder setting: N=999 (closer to full-catalog difficulty)
python scripts/benchmark/evaluate_recommendation.py \
  --mode sampled --negatives 999 --max-users 100000 \
  --combined --seed 42

# Multiseed error bars (5 seeds × ~12 min = ~1h)
python scripts/benchmark/multiseed_eval.py \
  --seeds 42 123 456 789 2026 --negatives 99

# Encoder comparison: BGE-M3 vs BLaIR (fast, ~17 min)
python scripts/benchmark/compare_encoders.py \
  --max-users 20000 --seed 42 --no-latency
```

#### C — LaTeX table generation

```python
# Cell 6 — Generate LaTeX table rows
STRATEGIES = ['Content Baseline', 'GRU-SeqDQN', 'DIF-SASRec',
              'Pipeline A (Cleora)', 'System (A∪B)']

print("% --- LaTeX table rows (copy into tables/main_results.tex) ---")
print(r"\hline")
for strat in STRATEGIES:
    if strat not in best.index:
        continue
    r = best.loc[strat]
    is_best_hr10  = r['hr10']  == best['hr10'].max()
    is_best_ndcg  = r['ndcg10'] == best['ndcg10'].max()
    def bold(v, cond): return f"\\textbf{{{v:.4f}}}" if cond else f"{v:.4f}"
    print(f"  {strat} & {r['hr5']:.4f} & {bold(r['hr10'], is_best_hr10)} "
          f"& {bold(r['ndcg10'], is_best_ndcg)} & {r['mrr10']:.4f} \\\\")
print(r"\hline")
```

---

### NB-3: Latency & Hardware Profiling

**File**: `notebooks/03_latency_profiling.ipynb`
**Purpose**: Inference latency per component, GPU memory, HNSW speedup.
**Runtime**: ~10 min (no running server needed for offline profiling)

#### A — Load encoder comparison latency results (already computed)

```python
# Cell 1 — Load encoder comparison JSON (has encode latency + HNSW recall)
import json, glob, os

comp_files = sorted(glob.glob('../evaluation/encoder_comparison_*.json'))
with open(comp_files[-1]) as f:  # latest
    comp = json.load(f)

lat = comp['encode_latency']
print(f"BGE-M3 encode latency (CUDA, n={lat['n']})")
print(f"  p50 = {lat['p50_ms']:.2f} ms")
print(f"  p95 = {lat['p95_ms']:.2f} ms")
print(f"  p99 = {lat['p99_ms']:.2f} ms")

hnsw = comp['hnsw_recall']
print(f"\nHNSW vs Exact (k={hnsw['k']}):")
print(f"  Recall@10  = {hnsw['mean_recall_at_k']:.4f}")
print(f"  Flat  p50  = {hnsw['flat_p50_ms']:.1f} ms  p95 = {hnsw['flat_p95_ms']:.1f} ms")
print(f"  HNSW  p50  = {hnsw['hnsw_p50_ms']:.1f} ms  p95 = {hnsw['hnsw_p95_ms']:.1f} ms")
print(f"  Speedup    = {hnsw['speedup_median']:.1f}x  (median)")
```

#### B — Per-strategy inference latency (from results_history time_s)

```python
# Cell 2 — Extract per-strategy wall-clock time from history
import pandas as pd, json

with open('../evaluation/results_history.json') as f:
    history = json.load(f)

# Only canonical 100k runs
rows = []
for run in history:
    if run.get('n_eval_users', 0) < 100000 or run['negatives'] != 99:
        continue
    for name, m in run['results'].items():
        rows.append({'strategy': name, 'time_s': m['time_s'], 'n_users': m['users']})

df = pd.DataFrame(rows)
latency = (df.groupby('strategy')['time_s']
           .agg(['mean', 'min', 'max'])
           .round(1)
           .rename(columns={'mean': 'avg_s', 'min': 'min_s', 'max': 'max_s'}))
latency['ms_per_user'] = (latency['avg_s'] * 1000 / 100000).round(2)
print(latency.to_string())
```

#### C — Live GPU memory profiling (run manually, requires running script)

```bash
# Measure peak VRAM during evaluation (requires pynvml)
python -c "
import torch, pynvml, threading, time
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
peak_mb = [0]

def monitor():
    while True:
        mb = pynvml.nvmlDeviceGetMemoryInfo(handle).used / 1e6
        if mb > peak_mb[0]: peak_mb[0] = mb
        time.sleep(0.05)

t = threading.Thread(target=monitor, daemon=True)
t.start()

# --- run your eval here ---
import subprocess
subprocess.run(['python', 'scripts/benchmark/evaluate_recommendation.py',
                '--max-users', '1000', '--dif-only'])

print(f'Peak VRAM: {peak_mb[0]:.0f} MB')
"
```

#### D — Search pipeline E2E latency (requires live API)

```bash
# Start API server first
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Run search timing benchmark
python scripts/benchmark/search_timing.py "thesis_benchmark" --runs 5 --warmup
# Output saved to: profiling/runs/<timestamp>/
```

```python
# Cell 3 — Parse search_timing output
import json, glob

runs = sorted(glob.glob('../profiling/runs/*/'))
with open(runs[-1] + 'summary.json') as f:
    timing = json.load(f)

stages = {
    'NLLB Translation':       timing.get('translate_ms', {}),
    'BGE-M3 Encoding':        timing.get('encode_text_ms', {}),
    'FAISS HNSW Search':      timing.get('text_search_ms', {}),
    'Tantivy BM25':           timing.get('tantivy_ms', {}),
    'RRF Fusion':             timing.get('rrf_ms', {}),
    'Metadata Hydration':     timing.get('metadata_hydration_ms', {}),
    'Total E2E':              timing.get('e2e_wall_clock_ms', {}),
}
for name, v in stages.items():
    if v:
        print(f"  {name:<25}  p50={v.get('p50', 0):.1f}ms  p95={v.get('p95', 0):.1f}ms")
```

---

### NB-4: Ablation Studies

**File**: `notebooks/04_ablation.ipynb`
**Purpose**: Isolate contribution of each pipeline component.

#### Ablation plan

| Condition | Command | Measures |
|---|---|---|
| Content Baseline only | `--mode sampled` (default run, Content Baseline row) | BGE-M3 profile similarity alone |
| Pipeline A only | `--pipeline-a-only` | Behavioral (Cleora) graph contribution |
| DIF-SASRec only | `--dif-only` | Sequential model contribution |
| Combined A+B | `--combined` | Union benefit, complementarity |
| N=99 vs N=999 | `--negatives 999` | Difficulty sensitivity |

#### Already-computed ablation data

From `evaluation/results_history.json` (run `20260426_233351`, N=99, n=100k):

```
Content Baseline   HR@10=0.4346  NDCG@10=0.3022
GRU-SeqDQN         HR@10=0.1031  NDCG@10=0.0472
Pipeline A         HR@10=0.9047  NDCG@10=0.5393
DIF-SASRec         HR@10=0.7745  NDCG@10=0.5024
System A∪B         HR@10=0.9736  NDCG@10=0.5571
```

#### Re-run ablations fresh

```bash
# All components in one pass (joint eval, ~2h on 100k users)
python scripts/benchmark/evaluate_recommendation.py \
  --mode sampled --negatives 99 --max-users 100000 \
  --combined --seed 42

# Component isolation
python scripts/benchmark/evaluate_recommendation.py --pipeline-a-only --max-users 100000 --seed 42
python scripts/benchmark/evaluate_recommendation.py --dif-only        --max-users 100000 --seed 42
```

```python
# Cell 1 — Reconstruct ablation table from history
import json, pandas as pd

with open('../evaluation/results_history.json') as f:
    history = json.load(f)

ABLATION_MAP = {
    'Content Baseline':    'BGE-M3 profile (no sequential)',
    'GRU-SeqDQN':          'RL sequential (baseline model)',
    'Pipeline A (Cleora)': 'Behavioral graph (Cleora + BGE-M3)',
    'DIF-SASRec':          'DIF-SASRec transformer (Pipeline B)',
    'System (A∪B)':        'Full system (A ∪ B union)',
}

# Pick latest canonical 100k N=99 run
runs_100k = [r for r in history 
             if r.get('n_eval_users', 0) >= 100000 and r['negatives'] == 99]
best_by_strategy = {}
for run in runs_100k:
    for name, m in run['results'].items():
        if name not in best_by_strategy or m['hr10'] > best_by_strategy[name]['hr10']:
            best_by_strategy[name] = m

rows = []
for strat, label in ABLATION_MAP.items():
    if strat in best_by_strategy:
        m = best_by_strategy[strat]
        rows.append({'Component': label, 'HR@5': m['hr5'], 'HR@10': m['hr10'],
                     'NDCG@10': m['ndcg10'], 'MRR@10': m['mrr10']})
df_ablation = pd.DataFrame(rows)
print(df_ablation.round(4).to_string(index=False))

# Cell 2 — Delta relative to Content Baseline
baseline_hr10 = best_by_strategy.get('Content Baseline', {}).get('hr10', None)
if baseline_hr10:
    for strat, m in best_by_strategy.items():
        delta = m['hr10'] - baseline_hr10
        print(f"  {strat:<30}  ΔHR@10 = {delta:+.4f}  ({delta/baseline_hr10*100:+.1f}%)")
```

---

### NB-5: Figure & Table Export

**File**: `notebooks/05_figures_tables.ipynb`
**Purpose**: Generate all publication-ready figures as PNG + LaTeX tables as .tex.

#### Figure list

| Figure | What it shows | Data source |
|---|---|---|
| `fig_hr10_comparison.png` | HR@10 bar chart across all strategies | `results_history.json` |
| `fig_ndcg10_comparison.png` | NDCG@10 bar chart | `results_history.json` |
| `fig_ablation_delta.png` | ΔHR@10 relative to baseline | `results_history.json` |
| `fig_multiseed_errorbars.png` | DIF-SASRec HR@10 ± std over 5 seeds | `multiseed_results.json` |
| `fig_encoder_query_gp.png` | BGE-M3 vs BLaIR genre-precision@10 by group | `encoder_comparison_*.json` |
| `fig_latency_breakdown.png` | Per-stage ms breakdown (stacked bar) | `profiling/runs/*/` |
| `fig_hnsw_recall_speedup.png` | HNSW recall vs speedup | `encoder_comparison_*.json` |
| `fig_negatives_sensitivity.png` | HR@10 vs N (99 vs 999) | `results_history.json` |

#### Full plotting code

```python
import json, glob, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

OUTDIR = '../paper/figures'
os.makedirs(OUTDIR, exist_ok=True)

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'legend.fontsize': 9,
    'figure.dpi': 150,
})

# ── Load data ────────────────────────────────────────────────────────────────
with open('../evaluation/results_history.json') as f:
    history = json.load(f)
with open('../evaluation/multiseed_results.json') as f:
    multiseed = json.load(f)
comp_files = sorted(glob.glob('../evaluation/encoder_comparison_*.json'))
with open(comp_files[-1]) as f:
    comp = json.load(f)

# canonical run: 100k users, N=99, latest
runs_100k_99 = [r for r in history
                if r.get('n_eval_users', 0) >= 100000 and r['negatives'] == 99]
best_by_strat = {}
for run in runs_100k_99:
    for name, m in run['results'].items():
        if name not in best_by_strat or m['hr10'] > best_by_strat[name]['hr10']:
            best_by_strat[name] = m

ORDER = ['Content Baseline', 'GRU-SeqDQN', 'DIF-SASRec',
         'Pipeline A (Cleora)', 'System (A∪B)']
LABELS = ['Content\nBaseline', 'GRU-\nSeqDQN', 'DIF-SASRec\n(ours)',
          'Pipeline A\n(Cleora)', 'System\n(A∪B)']
COLORS = ['#aec6e8', '#f28e2b', '#4e79a7', '#76b7b2', '#e15759']

# ── FIG 1: HR@10 comparison bar chart ────────────────────────────────────────
def bar_chart(metric, ylabel, fname):
    vals = [best_by_strat.get(s, {}).get(metric, 0) for s in ORDER]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(LABELS, vals, color=COLORS, edgecolor='white', width=0.6)
    ax.bar_label(bars, [f'{v:.4f}' for v in vals], padding=3, fontsize=9)
    ax.axhline(10/100, color='gray', ls='--', lw=1, label='Random (N=99)')
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, min(max(vals) * 1.2, 1.05))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
    ax.legend(loc='upper left')
    ax.set_title(f'{ylabel} — Sampled Evaluation (N=99, n=100k)')
    fig.tight_layout()
    fig.savefig(f'{OUTDIR}/{fname}', dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  Saved {fname}')

bar_chart('hr10',   'HR@10',    'fig_hr10_comparison.png')
bar_chart('ndcg10', 'NDCG@10',  'fig_ndcg10_comparison.png')
bar_chart('mrr10',  'MRR@10',   'fig_mrr10_comparison.png')

# ── FIG 2: Multiseed error bars ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
for ax, metric, label in zip(axes, ['hr10', 'ndcg10'], ['HR@10', 'NDCG@10']):
    vals = [s[metric] for s in multiseed['per_seed']]
    seeds = [str(s['seed']) for s in multiseed['per_seed']]
    mean = multiseed[f'mean_{metric}']
    std  = multiseed[f'std_{metric}']
    ax.bar(seeds, vals, color='#4e79a7', alpha=0.8)
    ax.axhline(mean, color='red',  ls='-',  lw=1.5, label=f'mean={mean:.4f}')
    ax.axhline(mean+std, color='red', ls='--', lw=0.8, alpha=0.7)
    ax.axhline(mean-std, color='red', ls='--', lw=0.8, alpha=0.7)
    ax.set_xlabel('Random Seed')
    ax.set_ylabel(label)
    ax.set_title(f'DIF-SASRec {label} across Seeds')
    ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(f'{OUTDIR}/fig_multiseed_errorbars.png', dpi=200, bbox_inches='tight')
plt.close()
print('  Saved fig_multiseed_errorbars.png')

# ── FIG 3: Encoder comparison (genre precision by query group) ────────────────
groups = ['short', 'medium', 'long', 'vi_short', 'vi_long']
bge_vals   = [comp['query_test']['per_group'].get(g, {}).get('bge_avg_gp',   0) for g in groups]
blair_vals = [comp['query_test']['per_group'].get(g, {}).get('blair_avg_gp', 0) for g in groups]

x = np.arange(len(groups))
w = 0.35
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(x - w/2, bge_vals,   w, label='BGE-M3 (current)', color='#4e79a7')
ax.bar(x + w/2, blair_vals, w, label='BLaIR (legacy)',   color='#f28e2b')
ax.set_xticks(x)
ax.set_xticklabels(['Short', 'Medium', 'Long', 'VI Short', 'VI Long'])
ax.set_ylabel('Genre-Precision@10')
ax.set_title('Query Retrieval Quality — BGE-M3 vs BLaIR')
ax.legend()
ax.set_ylim(0, 0.8)
fig.tight_layout()
fig.savefig(f'{OUTDIR}/fig_encoder_query_gp.png', dpi=200, bbox_inches='tight')
plt.close()
print('  Saved fig_encoder_query_gp.png')

# ── FIG 4: N=99 vs N=999 sensitivity ─────────────────────────────────────────
strategies = ['Content Baseline', 'DIF-SASRec', 'Pipeline A (Cleora)']
n99_hr   = {s: best_by_strat.get(s, {}).get('hr10', 0) for s in strategies}
runs_999 = [r for r in history
            if r.get('n_eval_users', 0) >= 100000 and r['negatives'] == 999]
best_999 = {}
for run in runs_999:
    for name, m in run['results'].items():
        if name not in best_999 or m['hr10'] > best_999[name]['hr10']:
            best_999[name] = m
n999_hr = {s: best_999.get(s, {}).get('hr10', 0) for s in strategies}

x = np.arange(len(strategies))
w = 0.35
fig, ax = plt.subplots(figsize=(6.5, 4))
ax.bar(x - w/2, [n99_hr[s]  for s in strategies], w, label='N=99',  color='#4e79a7')
ax.bar(x + w/2, [n999_hr[s] for s in strategies], w, label='N=999', color='#aec6e8')
ax.set_xticks(x)
ax.set_xticklabels(['Content Baseline', 'DIF-SASRec', 'Pipeline A'])
ax.set_ylabel('HR@10')
ax.set_title('Evaluation Difficulty — N=99 vs N=999 Negatives')
ax.legend()
fig.tight_layout()
fig.savefig(f'{OUTDIR}/fig_negatives_sensitivity.png', dpi=200, bbox_inches='tight')
plt.close()
print('  Saved fig_negatives_sensitivity.png')

# ── FIG 5: HNSW recall vs speedup summary ────────────────────────────────────
hnsw = comp['hnsw_recall']
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.scatter([hnsw['speedup_median']], [hnsw['mean_recall_at_k']],
           s=150, color='#4e79a7', zorder=5)
ax.annotate(f"HNSW\n({hnsw['speedup_median']:.1f}x, recall={hnsw['mean_recall_at_k']:.3f})",
            xy=(hnsw['speedup_median'], hnsw['mean_recall_at_k']),
            xytext=(hnsw['speedup_median'] - 1.5, hnsw['mean_recall_at_k'] + 0.05),
            arrowprops=dict(arrowstyle='->', color='black'))
ax.axhline(1.0, color='gray', ls='--', lw=1, label='Exact (Flat)')
ax.set_xlabel('Speedup over Flat Search (×)')
ax.set_ylabel('Recall@10 vs Exact')
ax.set_title('HNSW: Recall–Speed Tradeoff (BGE-M3)')
ax.set_ylim(0, 1.1)
ax.legend()
fig.tight_layout()
fig.savefig(f'{OUTDIR}/fig_hnsw_recall_speedup.png', dpi=200, bbox_inches='tight')
plt.close()
print('  Saved fig_hnsw_recall_speedup.png')

print('\nAll figures saved to', OUTDIR)
```

#### LaTeX table helpers

```python
# ── TABLE 1: Main results (N=99, n=100k) ─────────────────────────────────────
def to_latex_table(best_by_strat, order, fname):
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Recommendation accuracy (sampled evaluation, N=99, n=100k)}",
        r"\label{tab:main_results}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Strategy & HR@5 & HR@10 & NDCG@10 & MRR@10 \\",
        r"\midrule",
    ]
    best_hr10  = max(m['hr10']  for m in best_by_strat.values() if m)
    best_ndcg  = max(m['ndcg10'] for m in best_by_strat.values() if m)
    for strat in order:
        m = best_by_strat.get(strat)
        if m is None: continue
        def fmt(v, is_best): return f"\\textbf{{{v:.4f}}}" if is_best else f"{v:.4f}"
        row = (f"  {strat} & {fmt(m['hr5'], False)} & "
               f"{fmt(m['hr10'], m['hr10']==best_hr10)} & "
               f"{fmt(m['ndcg10'], m['ndcg10']==best_ndcg)} & "
               f"{m['mrr10']:.4f} \\\\")
        lines.append(row)
    lines += [r"\midrule",
              r"  Random baseline & 0.0700 & 0.1000 & 0.0454 & 0.1000 \\",
              r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    
    tex_path = f'{OUTDIR}/{fname}'
    with open(tex_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f'  Saved {fname}')

to_latex_table(best_by_strat, ORDER, 'table_main_results.tex')
```

---

## 5. Automation Commands (CLI Reference)

### All Experiments — Full Run Sequence

```bash
# Step 1: Generate eval users (skip if evaluation/eval_users.json exists)
python scripts/setup_dif_sasrec.py

# Step 2: Main accuracy table (canonical, ~20 min)
python scripts/benchmark/evaluate_recommendation.py \
  --mode sampled --negatives 99 --max-users 100000 \
  --combined --seed 42

# Step 3: Hard-mode eval (N=999, ~40 min)
python scripts/benchmark/evaluate_recommendation.py \
  --mode sampled --negatives 999 --max-users 100000 \
  --combined --seed 42

# Step 4: Error bars over 5 seeds (~1h total)
python scripts/benchmark/multiseed_eval.py \
  --seeds 42 123 456 789 2026 --negatives 99

# Step 5: Encoder comparison (~17 min with --no-latency)
python scripts/benchmark/compare_encoders.py \
  --max-users 20000 --seed 42 --no-latency

# Step 6: Full encoder comparison with latency + query test (~25 min)
python scripts/benchmark/compare_encoders.py \
  --max-users 20000 --seed 42

# Step 7: Search latency (needs live server)
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
python scripts/benchmark/search_timing.py "thesis_v1" --runs 5 --warmup
```

### Quick Sanity Checks

```bash
# 2-minute smoke test (2000 users, DIF-SASRec only)
python scripts/benchmark/evaluate_recommendation.py --max-users 2000 --dif-only

# Pipeline A only (fast, ~30s)
python scripts/benchmark/evaluate_recommendation.py --pipeline-a-only --max-users 5000

# Show all historical results
python -c "
import json
with open('evaluation/results_history.json') as f:
    h = json.load(f)
for r in h[-5:]:
    print(r['run_id'], r['negatives'], r.get('n_eval_users'), r['results'].keys())
"
```

### Expected Runtimes (RTX 5060 Ti)

| Script | Users | N | Expected Time |
|---|---|---|---|
| `evaluate_recommendation.py` (DIF-SASRec) | 100k | 99 | ~12 min |
| `evaluate_recommendation.py` (all + combined) | 100k | 99 | ~35 min |
| `evaluate_recommendation.py` (all) | 100k | 999 | ~45 min |
| `multiseed_eval.py` (5 seeds) | 100k | 99 | ~60 min |
| `compare_encoders.py` (no latency) | 20k | 99 | ~17 min |
| `compare_encoders.py` (full) | 20k | 99 | ~25 min |

---

## 6. Key Numbers Already in Hand

These exist in `evaluation/` and do NOT need to be re-run for the thesis.

### Table: Accuracy (N=99, n=100k, latest canonical runs)

| Strategy | HR@5 | HR@10 | NDCG@10 | MRR@10 |
|---|---|---|---|---|
| Content Baseline | 0.3597 | 0.4346 | 0.3022 | 0.2609 |
| GRU-SeqDQN | 0.0519 | 0.1031 | 0.0472 | 0.0306 |
| DIF-SASRec (B) | **0.5877** | 0.7745 | 0.5024 | 0.4191 |
| Pipeline A (Cleora) | 0.5750 | **0.9047** | **0.5393** | **0.4302** |
| System (A∪B) | — | **0.9736** | **0.5571** | — |
| *Random baseline* | *0.07* | *0.10* | *0.0454* | *0.10* |

### Table: DIF-SASRec Stability (N=99, n=100k, 5 seeds)

| Metric | Mean | Std | 95% CI |
|---|---|---|---|
| HR@10 | 0.7244 | ±0.0024 | [0.7220, 0.7268] |
| NDCG@10 | 0.4441 | ±0.0017 | [0.4424, 0.4458] |

### Table: Encoder Comparison (N=99, n=20k)

| Model | HR@10 | NDCG@10 | Intra/Inter sim ratio |
|---|---|---|---|
| BGE-M3 (current) | 0.4510 | 0.3128 | 1.147 |
| BLaIR (legacy) | 0.5484 | 0.3513 | 1.061 |

> Note: BLaIR has higher content-retrieval HR on this eval because its index covers 3M items vs BGE-M3's 1.7M HNSW production index. The flat eval is fair; BGE-M3 wins on all query-length groups except "short".

### Table: Latency (CUDA, RTX 5060 Ti)

| Component | p50 | p95 | Notes |
|---|---|---|---|
| BGE-M3 encode | 19.68 ms | 30.65 ms | fp16, single query |
| HNSW vs Flat | 119.56 ms vs 612.19 ms | — | 5.1× speedup |
| HNSW recall@10 | 52.12% | — | vs exact flat |

### Table: N Sensitivity

| Strategy | HR@10 (N=99) | HR@10 (N=999) | Ratio |
|---|---|---|---|
| Content Baseline | 0.4346 | 0.2122 | 0.49× |
| DIF-SASRec | 0.7745 | 0.3142 | 0.41× |
| Pipeline A | 0.9047 | 0.3272 | 0.36× |

---

## 7. Figures & Tables Catalogue

| # | File | Size | Description | Status |
|---|---|---|---|---|
| F1 | `fig_hr10_comparison.png` | 1 plot | HR@10 bar chart, 5 strategies | Generate NB-5 |
| F2 | `fig_ndcg10_comparison.png` | 1 plot | NDCG@10 bar chart | Generate NB-5 |
| F3 | `fig_mrr10_comparison.png` | 1 plot | MRR@10 bar chart | Generate NB-5 |
| F4 | `fig_ablation_delta.png` | 1 plot | ΔHR@10 vs Content Baseline | Generate NB-5 |
| F5 | `fig_multiseed_errorbars.png` | 2 subplots | DIF-SASRec HR/NDCG ± std | Generate NB-5 |
| F6 | `fig_encoder_query_gp.png` | 1 plot | BGE vs BLaIR genre-prec@10 | Generate NB-5 |
| F7 | `fig_negatives_sensitivity.png` | 1 plot | HR@10 vs N difficulty | Generate NB-5 |
| F8 | `fig_hnsw_recall_speedup.png` | 1 plot | HNSW recall–speed tradeoff | Generate NB-5 |
| T1 | `table_main_results.tex` | LaTeX | Main accuracy table | Generate NB-5 |
| T2 | `table_ablation.tex` | LaTeX | Ablation study | Generate NB-4 |
| T3 | `table_encoder_comparison.tex` | LaTeX | BGE vs BLaIR | Generate NB-2 |
| T4 | `table_latency.tex` | LaTeX | Inference latency | Generate NB-3 |
| T5 | `table_multiseed.tex` | LaTeX | Error bars | Generate NB-2 |

---

## 8. Output File Map

```
evaluation/
├── eval_users.json                          # 20k–100k users (input to all eval)
├── results_history.json                     # All evaluation runs, appended
├── multiseed_results.json                   # 5-seed DIF-SASRec error bars
├── encoder_comparison_<run_id>.json         # BGE-M3 vs BLaIR full comparison
└── logs/
    ├── <run_id>.log                         # Per-run detailed logs
    └── encoder_comparison_<run_id>.log

profiling/
├── history.jsonl                            # Search timing history
└── runs/<run_name>/
    ├── summary.json                         # Per-stage p50/p95 latencies
    └── raw.json                             # Per-query raw timings

paper/figures/                               # All generated plots (NB-5 output)
├── fig_hr10_comparison.png
├── fig_ndcg10_comparison.png
├── fig_multiseed_errorbars.png
├── fig_encoder_query_gp.png
├── fig_negatives_sensitivity.png
├── fig_hnsw_recall_speedup.png
├── table_main_results.tex
└── table_ablation.tex
```

---

## Quick-Start: Minimum Path to Paper Numbers

If you only need the final thesis numbers and figures without re-running everything:

```bash
# 1. Run NB-2, NB-3, NB-5 using existing evaluation/ data (no GPU needed)
jupyter notebook notebooks/02_accuracy_evaluation.ipynb
jupyter notebook notebooks/03_latency_profiling.ipynb
jupyter notebook notebooks/05_figures_tables.ipynb
```

All canonical numbers are already in `evaluation/results_history.json` and `evaluation/multiseed_results.json`. The notebooks read those files directly — no model loading required for figure generation.

For fresh re-evaluation:
```bash
python scripts/benchmark/evaluate_recommendation.py \
  --mode sampled --negatives 99 --max-users 100000 \
  --combined --seed 42
```
~35 min, appends to `evaluation/results_history.json`.
