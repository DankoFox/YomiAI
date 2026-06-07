# Agent Guide — Dual-Mode Multimodal Book Recommendation System

## Project Identity

This is an **academic capstone + Springer LNNS paper** from HCMUT building a book
recommendation system for the Amazon Books catalog (~3M items). The core thesis:
most systems handle **active search** OR **passive recommendation**, but not both
in a unified way. This system bridges that gap.

| Aspect | Value |
|---|---|
| Paper | "Bridging Multimodal Content and Behavioral Signals for NBA Recommendation" — IAAA 2026 (Springer LNNS) |
| Backend | Python 3.11 + FastAPI + uvicorn |
| Frontend | React 19 + Vite 8 + Tailwind CSS |
| Infra | MongoDB (profiles/logs) + Redis (interaction queue) — via Docker |
| GPU | Single RTX 5060 Ti (16 GB VRAM) |

---

## Navigation Map

```
app/                          # FastAPI backend
├── api/routes/               # 7 route modules (see below)
├── core/                     # lifespan, container (DI), model loaders
├── infrastructure/           # MongoDB+Redis connection, NLLB translation
├── repository/               # FAISS index, parquet metadata, user profiles
├── services/                 # Search, recommend, DIF-SASRec, LLM, agent pool
└── config.py                 # Settings dataclass (every path + hyperparam)

frontend/                     # React 19 + Vite 8 + Tailwind
├── src/
│   ├── components/           # UI components
│   ├── services/             # API client logic
│   └── App.jsx               # Main app

scripts/
├── benchmark/                # eval scripts
├── train/                    # pretrain_dif_sasrec.py
├── test/                     # unit/integration tests
├── build/                    # index builders
└── data/                     # cleora pipeline

thesis/
├── paper/                    # Springer LNNS conference paper (8 sections)
├── Captsone/                 # Full capstone report (7 chapters)
└── poster/                   # Conference poster
```

---

## Architecture (Two Modes)

### Mode 1 — Active Search (`POST /search`)

```
User query (text ± image)
  → NLLB translation (19 languages → EN)
  → BGE-M3 text embedding + CLIP image embedding (parallel)
  → 3-channel retrieval:
      • HNSW text FAISS   (BGE-M3, top-50)
      • HNSW clip FAISS   (CLIP, top-50)
      • BM25 keyword     (Tantivy, top-30)
  → Adaptive Weighted RRF fusion
  → Metadata hydration (title, author, genre, image_url)
```

### Mode 2 — Passive Recommendation (`GET /recommend`)

| Pipeline | Name | Technique | Candidates → Final |
|---|---|---|---|
| A | "People Also Buy" | Cleora graph → Content veto (cosine τ=0.3) → BGE-M3 rank | 50 → top-10 |
| B | "You Might Like" | HNSW KNN → Content veto → **DIF-SASRec** score | 200 → top-10 |

Cold-start (< 5 clicks): random catalog sample with `"mode": "cold_start"`.

---

## Code Conventions (MUST FOLLOW)

### 1. Docstring format

Every module starts with:
```python
"""app/services/foo.py — Purpose of this module."""
```

### 2. Imports

Grouped: stdlib → third-party → `app.*` (absolute only, no relative imports).

```python
import logging
import time

import anyio
import numpy as np
from fastapi import APIRouter, Depends

from app.config import settings
from app.core.container import AppContainer
from app.api.dependencies import require_ready
```

### 3. Logging

```python
log = logging.getLogger("nba_api")
# then: log.info(...), log.warning(...), log.error(...)
```

### 4. Configuration is ALWAYS from settings

```python
from app.config import settings
settings.TOP_K, settings.PERSONAL_CANDIDATES, settings.DATA_DIR
```

Never hardcode paths or hyperparameters. Everything lives in `app/config.py`.

### 5. Routes receive dependencies via `require_ready`

```python
@router.get("/endpoint")
async def handler(user_id: str, container: AppContainer = Depends(require_ready)):
    retriever = container.retriever
    search_engine = container.search_engine
    ...
```

### 6. Blocking work offloads to threads

```python
# anyio (preferred in routes):
await anyio.to_thread.run_sync(ml.encode_text, query, encoder)

# asyncio loop (alternative):
loop = asyncio.get_event_loop()
await loop.run_in_executor(None, fn, arg)
```

### 7. Parallel encoding uses `anyio.create_task_group()`

```python
async with anyio.create_task_group() as tg:
    tg.start_soon(encode_text_task)
    tg.start_soon(encode_image_task)
```

### 8. Timing measurements

```python
t0 = time.perf_counter()
# ... do work ...
timings["step_name_ms"] = round((time.perf_counter() - t0) * 1000, 2)
```

### 9. Model agent pattern

Every sequential model (DIF-SASRec, GRU4Rec) uses the **Agent pattern**:

```python
async with container.agent_pool.borrow() as agent:  # acquire from pool
    agent.load_user(user_id, settings.DATA_DIR)     # reset to per-user or pretrained weights
    result = agent.get_candidate_scores(...)         # inference
    # or: agent.train_step(...)                      # online training
    agent.save_user(user_id, settings.DATA_DIR)      # persist per-user checkpoint
# agent auto-released back to pool
```

### 10. Tensor building pattern (all agent classes)

Synchronize: numpy zero-padded → torch tensor → move to device.

```python
bge_arr = np.zeros((MAX_SEQ_LEN, TEXT_EMBED_DIM), dtype=np.float32)
cat_arr = np.zeros(MAX_SEQ_LEN,                   dtype=np.int64)
bge_arr[:T] = np.array(vec_list)
cat_arr[:T] = np.array(cat_list)
bge_t = torch.FloatTensor(bge_arr).unsqueeze(0).to(self.device)
cat_t = torch.LongTensor(cat_arr).unsqueeze(0).to(self.device)
```

### 11. User profile serialization

Profiles persist to MongoDB as dicts. Numpy arrays convert with `.tolist()`:

```python
"text_profile": profile.text_profile.tolist() if profile.text_profile is not None else [],
```

### 12. Checkpoint format

Every agent's checkpoint must include an `"arch"` string for safety:

```python
torch.save({
    "arch": "dif_sasrec_v1",         # or "gru4rec_v1", "sasrec_content_v1"
    "model_state": self.model.state_dict(),
    "optimizer_state": self.optimizer.state_dict(),
    "step": self._step,
    "loss_history": self.loss_history,
}, path)
```

Loading checks `ckpt.get("arch")` against expected arch and skips on mismatch.

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/auth/check` | Check user exists |
| `POST` | `/auth/create` | Create new user |
| `POST` | `/search` | Mode 1: multimodal active search (text ± image) |
| `GET` | `/recommend` | Mode 2: "People Also Buy" + "You Might Like" |
| `GET` | `/rl_metrics` | DIF-SASRec loss/step for a user |
| `POST` | `/interact` | Log click/skip/not_interested + train DIF-SASRec |
| `GET` | `/profile` | User stats + hydrated recent history |
| `POST` | `/ask_llm` | Qwen2.5-1.5B book assistant (sync) |
| `POST` | `/ask_llm_stream` | Qwen2.5-1.5B book assistant (streaming) |

---

## Key Files & Their Roles

### `app/config.py`
Single source of truth: paths, model names, hyperparameters, thresholds.
`settings = Settings()` is a frozen dataclass — never mutate.

### `app/core/container.py`
`AppContainer` dataclass — holds EVERY runtime dependency. Populated during
lifespan startup. Routes receive via `Depends(require_ready)`.

### `app/core/lifespan.py`
Async context manager: loads FAISS indices, models, translation, LLM, agent pool.
Background worker drains Redis interaction queue → MongoDB, triggers Cleora refit.

### `app/core/models.py`
`load_text_encoder()`, `load_clip()`, `encode_text()`, `encode_image_b64()`.
Text encoding is LRU-cached (4096 entries).
CLIP embedding from base64 image string.

### `app/repository/faiss_repo.py`
`Retriever` class — loads and exposes FAISS indices:
- `text_index` (HNSW for ANN search)
- `text_flat` (flat for exact reconstruction)
- `clip_index` (visual)
- `cleora_index` (behavioral)
- `get_content_candidates()` — HNSW KNN for Pipeline B (zero Cleora dependency)

### `app/repository/metadata_repo.py`
`MetadataRepository` — reads `item_metadata.parquet`, hydrates ASIN → full item
dict (title, author, genre, image_url, description, cover_color).

### `app/repository/profile_repo.py`
`UserProfileManager` — per-user state (clicks, searches, aggregated embeddings).
Uses per-user `asyncio.Lock` to prevent concurrent-write races.
Temporal exponential decay for embedding aggregation.

### `app/services/active_search.py`
`ActiveSearchEngine.search()` — BM25 + HNSW text + HNSW clip → Adaptive RRF fusion.

### `app/services/passive_recommend.py`
`PassiveRecommendationEngine.recommend_for_user()` — orchestrates Pipeline A
(Cleora → content veto) and Pipeline B (HNSW → content veto → DIF-SASRec).

### `app/services/dif_sasrec.py`
`DIFSASRecModel` + `DIFSASRecAgent`. Decoupled content/category attention.
12.4M params. Sampled softmax loss. Online fine-tuning per user click.
Checkpoint arch string: `"dif_sasrec_v1"`.

### `app/services/gru4rec.py`
`GRU4RecModel` + `GRU4RecAgent`. 2-layer GRU baseline. No category stream.
Used for ablation comparison in the paper. Checkpoint arch: `"gru4rec_v1"`.

### `app/services/agent_pool.py`
`AgentPool` — 8 concurrent `DIFSASRecAgent` instances (~1.18 GB VRAM).
`borrow()` context manager → acquire → yield → always release.

### `app/services/llm.py`
Lazy-loaded Qwen2.5-1.5B-Instruct. Grounds responses via Google Books API +
Wikipedia. Semantic reranking of context with BGE-M3. Streaming supported.

### `app/infrastructure/database.py`
MongoDB (profiles, interactions) + Redis (interaction queue, blocked sets).

### `app/infrastructure/translation.py`
Lingua language detection (19 languages) + NLLB-200-Distilled-600M translation.
Two-tier: greedy (beam=1, ~16ms) → quality gate → beam=4 fallback (~30ms).
LRU cache (2048 entries).

---

## Running Commands

```bash
# Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm install && npm run dev

# Infrastructure
docker-compose up -d

# Pre-process dataset + build eval_users.json
python scripts/setup_dif_sasrec.py

# Pretrain DIF-SASRec
python scripts/train/pretrain_dif_sasrec.py

# Evaluation
python scripts/benchmark/evaluate_recommendation.py        # HR@10, NDCG@10
python scripts/benchmark/compare_encoders.py --max-users 20000  # BLaIR vs BGE-M3

# Test pipeline
python scripts/test_refit_pipeline.py
```

---

## Common Pitfalls for Agents

1. **Do NOT hardcode file paths.** Use `settings.DATA_DIR` + relative paths.
2. **Do NOT use `asyncio.gather` for parallel encoding.** Use `anyio.create_task_group()`.
3. **Do NOT share FAI S S index references across threads.** FAISS is not thread-safe for writes; reads via mmap are safe.
4. **Do NOT mutate `settings`.** It's a frozen dataclass.
5. **Do NOT import from old `src/` paths.** All imports are from `app.*`.
6. **Agent pool agents must call `load_user()` before every use** to prevent cross-user weight contamination.
7. **Numpy arrays in user profiles** must be serialized via `.tolist()` and deserialized via `np.array()`.
8. **New model agents must implement:** `get_intent_vector()`, `get_candidate_scores()`, `train_step()` / `train_step_batch()`, `save()`, `load()`, `load_user()`, `save_user()`, and a pretrained-state snapshot in `__init__`.
