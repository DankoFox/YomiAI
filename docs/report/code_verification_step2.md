# Step 2 — Code Verification

**Purpose:** Every number and mechanism cited in Chapter 5 must be traceable here.
**Verified on:** 2026-05-24

---

## 2A — Routing Logic

**Routing function:** `recommend()` in `app/api/routes/recommend.py:17`

**Routing condition:**
```python
COLD_START_THRESHOLD = settings.COLD_START_THRESHOLD  # = 5 (app/config.py:58)

if len(profile.clicks) < COLD_START_THRESHOLD:
    rec_dict, mode = _cold_start(retriever)   # mode = "cold_start"
else:
    async with container.agent_pool.borrow() as agent:
        agent.load_user(user_id, settings.DATA_DIR)
        res = await recommend_engine.recommend_for_user(user_id, agent, top_k=10)
    if res is None:
        rec_dict, mode = _cold_start(retriever)
    else:
        rec_dict, mode = res, "personalized"
```

- **→ Pipeline A + B (personalized):** users with ≥ 5 clicks AND recommend engine returns non-None
- **→ Cold start (random):** users with < 5 clicks OR recommend engine returns None

**Cold start fallback (`_cold_start()` at line 85):**
Samples 20 random items from `retriever.cleora_asins` that also exist in `retriever.asin_to_idx`.
Returns mode `"cold_start"`.

**The 2.6% unrouted (eval context):**
In `eval_sampled()` (`evaluate_recommendation.py:345`), users are `skipped` — excluded from coverage — when:
1. User has no train or test clicks
2. Target test item not present in FAISS flat index (`asin not in all_asins_s`)
3. Insufficient random negatives can be drawn from the negative pool

These three conditions together account for the ~2.6% of test users excluded from the HR@10 denominator.

---

## 2B — AgentPool / Phase 2 Mechanism

**Class:** `AgentPool` in `app/services/agent_pool.py:26`

**Pool configuration:**
- Size: `AGENT_POOL_SIZE = 8` agents (line 23)
- Memory: 8 agents × ~148 MB (weights + AdamW moments) ≈ 1.18 GB VRAM
- Backing: `asyncio.Queue` — 9th concurrent request awaits, never dropped

**Trigger for per-user fine-tuning:**
`POST /interact` with `req.action == "click"` AND user has a prior click sequence.
Source: `app/api/routes/interact.py:70–78`

```python
if click_seq_before and req.action == "click":
    async with container.agent_pool.borrow() as agent:
        agent.load_user(req.user_id, settings.DATA_DIR)
        loss = recommend_engine.train_personal(
            req.user_id, req.item_id, agent,
            click_seq_before=click_seq_before,
        )
        agent.save_user(req.user_id, settings.DATA_DIR)
```

**What changes:**
- `agent.load_user()` reads per-user weights (model state + AdamW optimizer state) from disk
- `train_personal()` runs one gradient step on the (s_t, a_t) transition
- `agent.save_user()` persists updated per-user weights back to disk

**Update frequency:** One gradient step per click event (online fine-tuning).

**Phase 2 delta:** [DELTA_RESULT — to be filled with Khoa's before/after HR@10 comparison]

---

## 2C — Evaluation Reproducibility

**Script:** `scripts/benchmark/evaluate_recommendation.py`

**Single-command reproduction:**
```bash
python scripts/benchmark/evaluate_recommendation.py
```

**Evaluation protocol (default `--mode sampled`):**
- Academic standard: rank 1 real test item against 99 random negatives (100 total)
- Protocol matches SASRec / BERT4Rec / DIF-SASRec papers
- Random baseline HR@10 = 10/100 = 0.100

**Dataset:** `evaluation/eval_users.json`
- Built by: `python scripts/setup_dif_sasrec.py`
- Train/test split: leave-last-out (test = last click, train = all prior)

**Key metric functions:**
- `hit_rate()` at line 271: `1.0 if target in ranked[:k]`
- `ndcg()` at line 274: `1.0 / math.log2(i + 2)` for rank i
- `eval_sampled()` at line 345: main evaluation loop

**Confirmed numbers:**
| Strategy | HR@10 | Source |
|----------|-------|--------|
| Pipeline A (Cleora + BGE-M3) | **0.9047** | `PipelineAStrategy` |
| Pipeline B (DIF-SASRec) | **0.7745** | `DIFSASRecStrategy` |
| Combined (A+B) | highest | `CombinedStrategy` via RRF |
| Content Baseline | lower | `ContentBaseline` (BGE-M3 only, no Cleora) |
| GRU-SeqDQN | lower | `GRUSeqDQNStrategy` |

**Coverage:** 97.4% = fraction of eval_users not skipped (see 2A for skip conditions).

---

## Baseline Labels (for Chapter 2 + Chapter 5)

| System | Academic label in report |
|--------|--------------------------|
| `GRUSeqDQNStrategy` | "traditional sequential NBA" |
| `ContentBaseline` | "non-multimedia NBA" |
| `PipelineAStrategy` | "Pipeline A (Cleora + BGE-M3)" |
| `DIFSASRecStrategy` | "Pipeline B (DIF-SASRec)" |
| `CombinedStrategy` | "combined dual-pipeline system" |

---

## Config Reference (app/config.py)

| Setting | Value | Meaning |
|---------|-------|---------|
| `COLD_START_THRESHOLD` | 5 | Min clicks to receive personalized recs |
| `WARM_USER_THRESHOLD` | 20 | Threshold for "warm" user classification |
| `SIMILARITY_THRESHOLD` | 0.3 | Cosine threshold τ for content veto (DIF-SASRec) |
| `BEHAVIORAL_CANDIDATES` | 50 | Candidates from Cleora graph |
| `PERSONAL_CANDIDATES` | (see config) | Candidates from HNSW for Pipeline B |
| `RRF_K` | 60 | RRF fusion constant |
| `TOP_K` | 10 | Final recommendations per pipeline |
