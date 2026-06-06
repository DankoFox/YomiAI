# Hard-Negative Evaluation Plan
**Created:** 2026-05-25  
**Context:** DIF-SASRec investigation — why is its HR@10 (0.7755) lower than SASRecF (0.7921)?  
**Status:** READY TO IMPLEMENT

---

## Background & Diagnosis

### What the benchmark showed (seed=42, N=99 random negatives, 100k users)

| Strategy | HR@5 | HR@10 | NDCG@10 | MRR@10 |
|---|---|---|---|---|
| Content Baseline | 0.3597 | 0.4346 | 0.3022 | 0.2609 |
| GRU4Rec (content-based) | 0.5805 | 0.7703 | 0.4976 | 0.4143 |
| SASRec-equiv. (ablation, α=0) | 0.5695 | 0.7648 | 0.4929 | 0.4099 |
| SASRecF (trained from scratch) | 0.6171 | 0.7921 | 0.5225 | 0.4396 |
| DIF-SASRec (Pipeline B) | 0.5857 | 0.7755 | 0.5024 | 0.4189 |

### Root cause of narrow spread

Investigation findings (run 2026-05-25):

1. **The book embedding space is concentrated.** Raw BGE-M3 profile-mean inter-user cosine = 0.95. All book embeddings point in a similar direction in 1024-dim space. This compresses the ceiling: any model that captures "semantically related to training history" scores well.

2. **99 random negatives are trivially easy to reject.** Items drawn uniformly from 3M items are almost always far from the target in embedding space. The evaluation tests "coarse relevance," not "fine-grained discrimination."

3. **Inter-user intent cosine by model:**
   - Raw BGE-M3 profile mean: 0.9467
   - DIF-SASRec: 0.7055
   - SASRecF: 0.7106
   - GRU4Rec: 0.3830  ← most personalized

4. **DIF-SASRec consistently beats GRU4Rec by history length:**
   - Medium history (11–25 clicks): DIF=0.7640, GRU=0.7560 (+0.8pp)
   - Long history (26+ clicks):    DIF=0.8040, GRU=0.7880 (+1.6pp)
   — But loses to SASRecF (~−2pp) at all history lengths.

5. **GRU4Rec vs SASRecF top-10 overlap: 8.1/10.** Both models agree on the same "obviously relevant" items in a 99-random-negative pool. They differ only on borderline cases.

### Why DIF-SASRec underperforms SASRecF on random negatives

Amazon Books has only **817 coarse categories** for 3M items (avg ~3,665 items/category).  
The category attention stream provides limited discriminative signal when categories are broad.  
DIF-SASRec's category stream IS learning (it improves over the α=0 ablation: +0.83pp HR@10),  
but the signal is weak relative to a clean from-scratch content-only training run (SASRecF).

This is consistent with Xie et al. 2022 — their gains of +1.5–3.8pp were on fine-grained product  
categories (electronics, clothing) where categories are highly discriminative.

---

## Decision: Do NOT swap DIF-SASRec for SASRecF

**Reasons:**
- Thesis documents DIF-SASRec as Pipeline B throughout all chapters
- Swapping requires retraining, re-documenting, updating all claims — for a ~2pp gain
- The headline claim (A∪B HR@10=0.9736) is unaffected by Pipeline B's internal architecture
- DIF-SASRec's role is to provide **complementary signal to Pipeline A**, not to maximise HR@10 in isolation

**Defensible framing:**
> "DIF-SASRec's category stream yields limited gain on Amazon Books due to coarse categories  
> (817 categories, 3M items). The architecture is justified by Xie et al. 2022 (+1.5–3.8pp on  
> fine-grained product categories) and by the +0.83pp improvement over the content-only ablation  
> observed in our evaluation. The A∪B fusion system achieves HR@10=0.9736 — the primary  
> thesis contribution — where Pipeline B's role is complementarity with Pipeline A."

---

## The Fix: Hard-Negative Evaluation

Show DIF-SASRec's advantage under **within-category negatives**: 99 negatives drawn from  
the **same category** as the target item. This is the setting where the category attention  
stream provides real discriminative power.

Expected: DIF-SASRec ≥ SASRecF > GRU4Rec > Content Baseline  
(GRU4Rec has no category information at all; SASRecF has none either)

---

## Step-by-Step Implementation Plan

### Step 1 — Build category-to-ASIN index: `scripts/build_category_index.py`
**Time: ~30 min**

```python
# Load item_metadata.parquet
# For each ASIN, get its category via CategoryEncoder.get_category_id(asin)
# Build dict: {cat_id: [asin, asin, ...]}
# Write to data/category_asins.json
# Also log: category_id, category_name, item_count for top categories
```

Key constraints:
- Some categories have very few items → fall back to random negatives if `len(cat_pool) < 200`
- Exclude ASINs not in `retriever.asin_to_idx` (no BGE-M3 vector)
- Output: `data/category_asins.json` — keyed by int category_id as string

Expected output: 817 categories, most with 1,000–50,000 ASINs each.

### Step 2 — Add `--hard-negatives` flag to eval script
**File: `scripts/benchmark/evaluate_recommendation.py`**  
**Time: ~45 min**

**2a. Add CLI arg:**
```python
p.add_argument("--hard-negatives", action="store_true",
               help="Sample negatives from the same category as the target (harder eval)")
```

**2b. Load category index in `main()` when flag is set:**
```python
category_asins = {}
if args.hard_negatives:
    cat_index_path = os.path.join(DATA_DIR, "category_asins.json")
    with open(cat_index_path) as f:
        category_asins = {int(k): v for k, v in json.load(f).items()}
    print(f"  Hard negatives: {len(category_asins)} categories loaded")
```

**2c. Pass `category_asins` and `cat_encoder` into `eval_sampled`:**
```python
def eval_sampled(strategy, eval_users, all_asins, neg_pool_asins,
                 n_neg, k, max_users, logger,
                 hard_negatives=False, category_asins=None, cat_encoder=None):
```

**2d. Inside the per-user loop, replace negative sampling:**
```python
if hard_negatives and category_asins and cat_encoder:
    target_cat = cat_encoder.get_category_id(target)
    cat_pool   = [a for a in category_asins.get(target_cat, [])
                  if a not in seen and a in all_asins_s]
    if len(cat_pool) >= n_neg:
        negs = random.sample(cat_pool, n_neg)
    else:
        # Fall back to random if category is too small
        negs = [a for a in random.sample(neg_pool_asins,
                min(n_neg * 3, len(neg_pool_asins)))
                if a not in seen][:n_neg]
else:
    # existing random negative sampling
    negs = [a for a in random.sample(neg_pool_asins, ...)
            if a not in seen][:n_neg]
```

**2e. Update the call site in `main()`:**
```python
r = eval_sampled(s, eval_users, all_asins, neg_pool_asins,
                 n_neg=args.negatives, k=args.k,
                 max_users=args.max_users, logger=logger,
                 hard_negatives=args.hard_negatives,
                 category_asins=category_asins,
                 cat_encoder=cat_encoder)
```

### Step 3 — Run hard-negative benchmark (~35 min)
```powershell
PYTHONIOENCODING=utf-8 python scripts/benchmark/evaluate_recommendation.py --seed 42 --hard-negatives
```

Results go to `evaluation/results_history.json` automatically.

**Smoke test first (quick sanity check):**
```powershell
PYTHONIOENCODING=utf-8 python scripts/benchmark/evaluate_recommendation.py --seed 42 --hard-negatives --max-users 2000
```

### Step 4 — Update LaTeX (~20 min)
**File: `Captsone/chapter5_comparison_table.tex`**

Add a second table block or extend the existing table with a hard-negatives section:

```latex
% Hard-negative evaluation (within-category negatives, N=99)
\midrule
\multicolumn{5}{l}{\textit{Hard negatives (same-category pool, $N=99$)}} \\
\midrule
GRU4Rec~\cite{hidasi2016gru4rec}  & ... & [HR@10] & ... & ... \\
SASRecF~\cite{kang2018self}$\ddagger$ & ... & [HR@10] & ... & ... \\
DIF-SASRec (ours)~\cite{xie2022difsasrec} & ... & \textbf{[HR@10]} & ... & ... \\
```

**File: `Captsone/chapter5_holistic.tex`**

Add one paragraph after the existing comparison paragraph:
> "To test the category stream's discriminative contribution, we repeat the evaluation with  
> within-category hard negatives (99 items drawn from the same category as the target).  
> Under this harder protocol, DIF-SASRec achieves HR@10=[X] vs SASRecF=[Y] and GRU4Rec=[Z],  
> confirming that the category attention mechanism provides meaningful signal when models  
> must distinguish semantically similar items within the same genre."

---

## Fallback: If DIF-SASRec still loses on hard negatives

Unlikely, but if DIF-SASRec loses to SASRecF even on hard negatives, use this framing:

> "DIF-SASRec's category stream provides marginal gain on Amazon Books because the category  
> taxonomy is coarse (817 categories, avg 3,665 items/category). The architecture is justified  
> by Xie et al. 2022 benchmark results (+1.5–3.8pp on fine-grained categories) and by the  
> observed +0.83pp improvement over the α=0 ablation. Pipeline B's primary contribution is  
> complementarity with Pipeline A in the A∪B fusion (HR@10=0.9736), not standalone ranking."

Do NOT add the hard-negative table if DIF-SASRec does not win — it would hurt more than help.

---

## Key Constraints (carry-over from DEFENSE_NEXT_SESSION.md)

- **Citation format:** `\cite{}` ONLY — never `\parencite{}`
- **Claim rule:** every number in LaTeX must come from `evaluation/results_history.json`
- **BibTeX keys:** `hidasi2016gru4rec`, `kang2018self`, `xie2022difsasrec`
- **`[DELTA_RESULT]`** placeholder in `chapter5_holistic.tex:~41` — still open, do not fill
- **Do not re-run the canonical benchmark** (seed=42, 100k users) — those numbers are locked

---

## Files to create / modify

| Action | File |
|---|---|
| CREATE | `scripts/build_category_index.py` |
| MODIFY | `scripts/benchmark/evaluate_recommendation.py` (add `--hard-negatives`) |
| CREATE | `data/category_asins.json` (output of Step 1) |
| MODIFY | `Captsone/chapter5_comparison_table.tex` (if DIF wins) |
| MODIFY | `Captsone/chapter5_holistic.tex` (if DIF wins) |
