# Defense Prep — Handoff to Next Session
**Updated:** 2026-05-25  
**Context:** Thesis defense for a dual-pipeline multimodal NBA book recommendation system (Amazon Books, FastAPI + React stack).

---

## What Was Completed This Session (Do NOT redo)

| Item | File | Notes |
|------|------|-------|
| `content_only=True` flag added to DIFSASRecModel | `app/services/dif_sasrec.py` | Disables category stream + aux loss during training |
| SASRecF training script | `scripts/train_sasrec_content.py` | 30 epochs, batch=2048, same protocol as DIF-SASRec |
| SASRecF checkpoint | `data/sasrec_content_pretrained.pt` | step=46770, trained end-to-end without category stream |
| SASRecTrainedStrategy added to eval | `scripts/benchmark/evaluate_recommendation.py` | Loads sasrec_content_pretrained.pt |
| Benchmark run completed | `evaluation/logs/20260525_113118.log` | seed=42, 100k users, all 4 sequential strategies |
| Table updated with SASRecF row | `thesis/Captsone/chapter5_comparison_table.tex` | Row label: `SASRecF~\cite{kang2018self}$\ddagger$` |
| Table DIF-SASRec numbers updated | `thesis/Captsone/chapter5_comparison_table.tex` | 0.7755→0.7738, HR@5: 0.5860→0.5854 (same run) |
| Holistic text updated | `thesis/Captsone/chapter5_holistic.tex` | SASRecF framing, updated DIF-SASRec number, coarse-category explanation |
| SASRec row relabeled as ablation | `thesis/Captsone/chapter5_comparison_table.tex` | `SASRec-equiv. (ablation, α=0)†` |
| Xie et al. anchor sentence added | `thesis/Captsone/chapter5_holistic.tex` | Published comparison, direction confirmed |

---

## Final Benchmark Numbers (seed=42, N=99 neg, 100k users, run 2026-05-25)

| Strategy | HR@5 | HR@10 | NDCG@10 | MRR@10 |
|---|---|---|---|---|
| Random | 0.0500 | 0.1000 | 0.0454 | 0.1000 |
| Content Baseline (BGE-M3 profile mean) | 0.3597 | 0.4346 | 0.3022 | 0.2609 |
| SASRec-equiv. (ablation, α=0)† | 0.5707 | 0.7655 | 0.4932 | 0.4102 |
| SASRecF‡ | 0.6171 | **0.7932** | 0.5233 | 0.4403 |
| Pipeline B — DIF-SASRec | 0.5854 | 0.7738 | 0.5015 | 0.4182 |
| Pipeline A — Cleora + BGE-M3 | — | 0.9047 | 0.5393 | — |
| **System A∪B (ours)** | — | **0.9736** | **0.5571** | — |

**Key finding to defend:** SASRecF (0.7932) > DIF-SASRec (0.7738) on Amazon Books. Reason: book categories are coarse (817 categories, 3M items); the category stream provides limited discriminative signal. DIF-SASRec still improves over the ablation (+0.83pp), confirming the direction in Xie et al. 2022.

---

## One Remaining Placeholder

File: `thesis/Captsone/chapter5_holistic.tex`, line ~41  
Replace: `[DELTA\_RESULT]`  
With: Khoa's Phase 2 HR@10 delta (zero-click vs post-click). **Do NOT invent a number.**

---

## Next Task: Add GRU4Rec Baseline

### Why GRU4Rec (not NOVA)
- Completes the architectural progression: **Content Baseline → GRU4Rec → SASRecF → DIF-SASRec**
- Already cited as `hidasi2016gru4rec` in `ref.bib`
- Simple to implement: GRU over BGE-M3 embeddings, same training infrastructure
- NOVA sits between SASRecF and DIF-SASRec and is not part of our system lineage — not worth implementing

Expected HR@10: **0.55–0.68** (between Content Baseline and SASRec-equiv. ablation). GRU captures sequential structure but is weaker than self-attention.

---

## Step-by-Step Plan for GRU4Rec Session

### Step 1 — Build `app/services/gru4rec.py` (~1 hour)

Create a `GRU4RecAgent` class mirroring `DIFSASRecAgent`. Key components:

```python
class GRU4RecModel(nn.Module):
    def __init__(self, input_dim=1024, hidden_dim=256, num_layers=2, dropout=0.2):
        # ContentProjector: 1024 → 256 (same as dif_sasrec.py)
        # nn.GRU(input_size=256, hidden_size=256, num_layers=2,
        #        batch_first=True, dropout=0.2)
        # No category embedding, no category head

class GRU4RecAgent:
    # __init__(retriever, emb_cache)
    # train_step_batch(seqs, targets, neg_pool_vecs) → loss
    # recommend(seq) → scores dict
    # save(path) / load(path)
```

Training objective: same sampled-softmax loss as `DIFSASRecAgent.train_step_batch()`, no category auxiliary loss. Score candidates by dot product of last GRU hidden state with candidate embeddings.

Architecture reference from DEFENSE_NEXT_SESSION: `hidasi2016gru4rec`. Input dim 1024 (BGE-M3), hidden 256, 2 layers, dropout 0.2.

Do NOT copy the DIFSASRec scheduler logic blindly — GRU4Rec trains faster (fewer params), so 20 epochs at batch=2048 should suffice. Verify with a 2-epoch smoke test before committing to a full run.

### Step 2 — Build `scripts/train_gru4rec.py` (~30 min)

Mirror `scripts/train_sasrec_content.py` exactly:
- Same `_Tee` class for real-time logging
- Same `--epochs`, `--batch-size`, `--output`, `--resume-from`, `--log-file` args
- Default output: `data/gru4rec_pretrained.pt`
- Default epochs: 20 (not 30 — GRU4Rec converges faster)

Smoke-test command (run 2 epochs to confirm no crash):
```
python scripts/train_gru4rec.py --epochs 2 --log-file data/gru4rec_training.log
```

Full training command:
```
python scripts/train_gru4rec.py --log-file data/gru4rec_training.log
```

Monitor with: `Get-Content -Wait "data\gru4rec_training.log"`

### Step 3 — Add `GRU4RecStrategy` to eval script (~20 min)

File: `scripts/benchmark/evaluate_recommendation.py`

Add class immediately after `SASRecTrainedStrategy`. Pattern identical to that class, but loads `gru4rec_pretrained.pt`. Name string: `"GRU4Rec (content-based)"`.

Wire into the strategy list:
```python
gru4rec_path = os.path.join(DATA_DIR, "gru4rec_pretrained.pt")
gru4rec = GRU4RecStrategy(...) if os.path.exists(gru4rec_path) else None
strategies = [
    ContentBaseline(...),
    sasrec_strategy,        # ablation
    *([gru4rec] if gru4rec else []),
    *([sasrec_trained] if sasrec_trained else []),
    dif_strategy,
]
```

### Step 4 — Run benchmark (~35 min)

```
$env:PYTHONIOENCODING="utf-8"; python scripts/benchmark/evaluate_recommendation.py --seed 42
```

Run in background task. Results appear in `evaluation/results_history.json`.

### Step 5 — Update LaTeX

**`thesis/Captsone/chapter5_comparison_table.tex`:**
- Add `GRU4Rec~\cite{hidasi2016gru4rec}` row between Content Baseline and SASRec-equiv. ablation
- Add `\S` or `\S\S` footnote if needed explaining it uses GRU hidden state, not self-attention

**`thesis/Captsone/chapter5_holistic.tex`:**
- Add one sentence in the comparison paragraph: GRU4Rec establishes the upper bound for recurrent sequential modelling; the jump to self-attention (SASRecF) is the key gain, and DIF-SASRec decouples the category signal on top.

---

## Key Constraint Reminders

- **Citation format:** `\cite{}` ONLY — never `\parencite{}`. Zero tolerance.
- **Claim rule:** Every number in LaTeX must come from `evaluation/results_history.json` or a verified paper. No invented numbers.
- **CLAUDE.md:** Use `code-review-graph` MCP tools before Grep/Glob/Read for codebase exploration.
- **BibTeX keys:** `hidasi2016gru4rec`, `kang2018self`, `xie2022difsasrec`, `sun2019bert4rec`, `rendle2010fpmc`, `wei2023mmssl`, `zhou2023bm3`, `guo2024lgmrec`
- **Architecture ref in Foundation text:** `2.1.Foundation-knowledge.tex` mentions SASRecF, NOVA-SR, DIF-SR — the table now correctly labels our model as SASRecF (not plain SASRec)
- **`[DELTA_RESULT]`:** Still open — do not fill until Khoa provides data
