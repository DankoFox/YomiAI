# Next Session — Copy-Paste Prompt Guide
**Updated:** 2026-05-25  
**Purpose:** Exact prompts to use at the start of each new Claude session to continue thesis defense work without losing context.

---

## How to start any session

Always open with this to reload context:

```
Read docs/progress/DEFENSE_NEXT_SESSION.md and docs/progress/HARD_NEGATIVES_PLAN.md, confirm what's done and what's next.
```

---

## Session A — Hard-Negative Evaluation (immediate next)

Run these prompts **in order**, one per response.

---

### Prompt A-1: Build the category index

```
Build scripts/build_category_index.py.

Load item_metadata.parquet using pandas, then use CategoryEncoder (already at
app/services/category_encoder.py, load from data/category_vocab.json) to map every
ASIN to its category_id via get_category_id(asin).

Build a dict {cat_id (int): [asin, asin, ...]} containing only ASINs that exist in
the FAISS retriever (check retriever.asin_to_idx). Write the result to
data/category_asins.json (keys as strings). Print a summary: total categories,
mean/min/max items per category, and the 5 largest categories by name.

Use Retriever from app.repository.faiss_repo. Load cleora_embeddings.npz to
instantiate it. Do not run the script yet.
```

---

### Prompt A-2: Smoke-test the category index

```
Run scripts/build_category_index.py and confirm it produces data/category_asins.json
with a reasonable distribution (all 817 categories present, no empty categories).
```

---

### Prompt A-3: Add --hard-negatives to the eval script

```
Add a --hard-negatives flag to scripts/benchmark/evaluate_recommendation.py.

When set, for each user in eval_sampled, sample the 99 negatives from
data/category_asins.json[target_category] instead of the global neg_pool_asins.
Fall back to random negatives if the category pool has fewer than 200 available
items (after excluding items the user has seen).

Load category_asins.json in main() only when --hard-negatives is set. Pass it and
cat_encoder into eval_sampled as optional kwargs (default None). Do not change
anything in the --combined or --pipeline-a-only branches.

Full plan is in docs/progress/HARD_NEGATIVES_PLAN.md Steps 2a-2e.
```

---

### Prompt A-4: Smoke-test hard negatives

```
Run a quick smoke test of the hard-negative eval on 2000 users:

  PYTHONIOENCODING=utf-8 python scripts/benchmark/evaluate_recommendation.py \
    --seed 42 --hard-negatives --max-users 2000

Confirm it runs without error and that DIF-SASRec, GRU4Rec, and SASRecF all score.
Report the HR@10 for each strategy.
```

---

### Prompt A-5: Full hard-negative benchmark

```
Run the full hard-negative benchmark (100k users, seed 42):

  PYTHONIOENCODING=utf-8 python scripts/benchmark/evaluate_recommendation.py \
    --seed 42 --hard-negatives

Tell me when it's done and give me the HR@10 table.
```

---

### Prompt A-6: Update LaTeX (ONLY if DIF-SASRec wins on hard negatives)

```
DIF-SASRec achieved HR@10=[X] on hard negatives vs SASRecF=[Y] and GRU4Rec=[Z]
(from evaluation/results_history.json).

Do the following:
1. Add a second table block to thesis/Captsone/chapter5_comparison_table.tex showing the
   hard-negative results. Use \midrule to separate from the existing random-negative
   block. Add a row label footnote explaining "hard negatives = same-category pool".
2. Add one paragraph to thesis/Captsone/chapter5_holistic.tex (after the existing comparison
   paragraph) explaining the hard-negative result and what it reveals about the
   category stream's contribution.
3. Also add the GRU4Rec row to the existing random-negative table block
   (it is still missing — do not redo the DIF-SASRec or SASRecF rows).

Use \cite{} only. All numbers must come from evaluation/results_history.json.
```

### Prompt A-6 (fallback): Update LaTeX (if DIF-SASRec does NOT win)

```
DIF-SASRec did not outperform SASRecF on hard negatives. Do not add the
hard-negative table. Instead:

1. Add only the GRU4Rec row to thesis/Captsone/chapter5_comparison_table.tex between
   Content Baseline and SASRec ablation. Use \cite{hidasi2016gru4rec}.
2. Add one sentence to thesis/Captsone/chapter5_holistic.tex establishing the GRU4Rec
   recurrent baseline and the jump to self-attention (SASRecF).
3. In the existing DIF-SASRec paragraph, add one sentence citing Xie et al. 2022
   to explain the limited category gain on Amazon Books (coarse taxonomy).

Use \cite{} only. Numbers from evaluation/results_history.json only.
```

---

## Session B — [DELTA_RESULT] Placeholder (when Khoa sends data)

```
Khoa provided the Phase 2 HR@10 delta: [VALUE].

Fill the placeholder in thesis/Captsone/chapter5_holistic.tex line ~41.
Replace [DELTA_RESULT] with the actual value. Do not change anything else in that file.
Confirm the surrounding sentence still reads correctly with the new number.
```

---

## Session C — Defense Slides

```
Read docs/progress/DEFENSE_NEXT_SESSION.md for the canonical benchmark numbers.

Build a defense slide deck outline for a 20-minute thesis presentation on a dual-pipeline
multimodal book recommendation system (Amazon Books, FastAPI + React). The system achieves
HR@10=0.9736 (Pipeline A∪B). Key claims to hit:
  - Pipeline A: Cleora graph embeddings + BGE-M3 profile → HR@10=0.9047
  - Pipeline B: DIF-SASRec sequential model → HR@10=0.7755
  - Combined A∪B: HR@10=0.9736, NDCG@10=0.5571
  - Architectural progression table (Content Baseline → GRU4Rec → SASRecF → DIF-SASRec)

Structure: title / motivation / system overview / Pipeline A / Pipeline B / evaluation /
ablation table / conclusion / Q&A. ~15 slides. Focus on what a committee will challenge.
```

---

## Future Steps (after hard-negative eval is done)

### Near-term (before defense)

| Priority | Task | Prompt hint |
|---|---|---|
| HIGH | Fill `[DELTA_RESULT]` | Session B above (wait for Khoa) |
| HIGH | Defense slides | Session C above |
| MEDIUM | Q&A preparation | "Generate likely committee questions for a thesis defense on [system]. For each question, write a 3-sentence answer using our benchmark numbers." |
| MEDIUM | System demo check | "Start the FastAPI backend and React frontend. Verify the recommendation endpoint returns results for a sample user. Check for any startup errors." |

### Optional strengthening (if time permits)

| Task | What it shows | Prompt hint |
|---|---|---|
| Complementarity analysis | Which test users are hit by A only, B only, both, neither | "In the combined eval, break down the 0.9736 HR@10 into: hit by A only / B only / both / neither. Shows A and B are genuinely complementary." |
| Category-stratified eval | DIF-SASRec wins on users with clear genre preferences | "Split eval_users by category entropy of train_clicks (low = focused reader, high = eclectic). Compare DIF-SASRec vs GRU4Rec HR@10 for each group." |
| Online fine-tuning demo | Shows Pipeline B adapts at inference time | "Write a script that simulates 5 online fine-tuning steps for a user, printing loss and the top-3 recommended items before and after fine-tuning." |
| Latency profiling | Committee may ask about production feasibility | "Profile the recommendation endpoint: time the FAISS search, DIF-SASRec inference, and full response for a single user request. Report p50/p95/p99." |

---

## Key Numbers to Know for the Defense

| Metric | Value | Source |
|---|---|---|
| System A∪B HR@10 | **0.9736** | evaluation/results_history.json 2026-04-26 |
| System A∪B NDCG@10 | **0.5571** | same |
| Pipeline A HR@10 | 0.9047 | same |
| DIF-SASRec HR@10 | 0.7755 | evaluation/results_history.json 2026-05-25 |
| SASRecF HR@10 | 0.7921 | same |
| GRU4Rec HR@10 | 0.7703 | same |
| Content Baseline HR@10 | 0.4346 | same |
| Random baseline HR@10 | 0.1000 | theoretical (10/100) |
| DIF-SASRec vs ablation gain | +0.83pp HR@10 | 0.7755 − 0.7648 + rounding from 2026-05-25 run |

---

## BibTeX Keys (never invent new ones)

`hidasi2016gru4rec` · `kang2018self` · `xie2022difsasrec` · `sun2019bert4rec`  
`rendle2010fpmc` · `wei2023mmssl` · `zhou2023bm3` · `guo2024lgmrec`

## Critical Rules (never break these)

- `\cite{}` ONLY — never `\parencite{}`
- Every number in LaTeX must come from `evaluation/results_history.json` or a verified paper
- `[DELTA_RESULT]` in `chapter5_holistic.tex:~41` — do NOT fill until Khoa provides it
- Do NOT re-run the canonical seed=42 100k-user benchmark — those numbers are locked
