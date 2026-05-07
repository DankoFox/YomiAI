# Experiment Notebooks

Run in order. Each notebook is self-contained.

| Notebook | Purpose | Runtime | GPU? |
|---|---|---|---|
| `01_dataset_verification.ipynb` | Sanity-check indices + sample outputs | ~5 min | No |
| `02_accuracy_evaluation.ipynb` | Load results, render metric tables, LaTeX export | ~1 min | No (reads cache) |
| `03_latency_profiling.ipynb` | Encode latency, HNSW recall, per-strategy timing | ~5 min | No |
| `04_ablation.ipynb` | Component isolation analysis | ~1 min | No (reads cache) |
| `05_figures_tables.ipynb` | Generate all PNG figures + .tex tables → paper/figures/ | ~2 min | No |

## Before running any notebook

```bash
# from project root
pip install jupyter matplotlib seaborn pandas pyarrow
python scripts/benchmark/evaluate_recommendation.py --max-users 2000 --dif-only  # smoke test
```

See `EXPERIMENT_ROADMAP.md` in the project root for the full walkthrough.
