# Cleora Dynamic Refit Update — May 5, 2026

This document records the completion of Phase B (Slow Path) and Phase C (Hot-Swap) from the [Cleora Dynamic Integration Plan](../planning/cleora_dynamic_integration_plan.md).

---

## Overview

The system previously used Cleora embeddings as a static lookup table trained once on the Amazon Reviews 2023 dataset. This session closes the remaining gap: the Cleora graph now **automatically retrains on live user interactions** and **hot-reloads without an API restart**.

---

## Stage 1: Signal Design — Click vs. Cart vs. Purchase

### Decision: Cart + Click, No Purchase Action

A purchase action was considered but rejected for two reasons:
1. The system has no checkout flow — `cart` already represents the highest-intent signal available (reward = 5.0).
2. The original Amazon training data is built from reviews (purchase proxies). Using `cart` for delta updates preserves the same signal semantics.

**Final signal hierarchy for graph updates:**

| Action | Used in delta? | Rationale |
| :--- | :---: | :--- |
| `cart` | ✅ | Highest intent — direct proxy for purchase |
| `click` | ✅ | Behavioural co-occurrence signal |
| `skip` | ❌ | Negative signal; would introduce anti-edges |
| `purchase` | N/A | Not implemented; `cart` covers this role |

Guest/anonymous sessions (`is_guest: true`) are excluded from all graph updates since they have no persistent identity to anchor in the graph.

---

## Stage 2: Delta Hyperedge Export (`scripts/export_delta_hyperedges.py`)

### Status: ✅ Completed (new file)

**What it does:**
- Queries MongoDB `nba_logs.interactions` for `click` and `cart` events since the last run
- Filters to catalog-valid ASINs only (same `asins.csv` whitelist used by `filter_hyperedges.py` — keeps delta statistics consistent with the base)
- Groups by `user_id`, writes one hyperedge row per user (deduplicated ASINs)
- Persists a `data/delta_last_run.txt` timestamp so each export only captures new interactions

**Key design choices:**
- Uses `datetime.now()` (local time, no UTC suffix) to match the format already written by `interact.py`
- Minimum hyperedge size: 1 item (matches existing `filter_hyperedges.py` behaviour)
- Output: `data/delta_hyperedges.txt`

**Usage:**
```bash
python scripts/export_delta_hyperedges.py
# or with explicit cutoff:
python scripts/export_delta_hyperedges.py --since 2026-01-01T00:00:00
```

---

## Stage 3: Augmented Cleora Retraining (`scripts/data/run_cleora.py`)

### Status: ✅ Updated

Added `--augment` and `--augment-weight` CLI flags. The updated script streams the base `hyperedges_cleora.txt` file unchanged, then appends the delta block repeated `--augment-weight` times before feeding the combined iterator to the Cleora `SparseMatrix`.

**Recency up-weighting:**

A single up-weighting knob (`--augment-weight N`, default 10) repeats the entire delta block N times. This gives each live user N× the influence of any single historical base user in the Markov propagation. One parameter, one thesis argument: *recency bias*.

The alternative of repeating cart ASINs within individual rows was considered and rejected — two stacked multipliers are harder to defend and harder to tune.

**Usage:**
```bash
python scripts/data/run_cleora.py --augment data/delta_hyperedges.txt
python scripts/data/run_cleora.py --augment data/delta_hyperedges.txt --augment-weight 20
```

---

## Stage 4: Automated Trigger + Hot-Reload

### Status: ✅ Completed

### 4.1 Count-Based Trigger (`app/core/lifespan.py`)

The existing `_log_worker` (which drains Redis → MongoDB) was extended with an interaction counter. When the counter reaches `CLEORA_REFIT_THRESHOLD`, the full refit pipeline fires as a background asyncio task.

**Gate mechanism:** An `asyncio.Event` (`refit_gate`) prevents a second refit from launching while one is already running. The counter resets when the gate is cleared, so interactions that arrive during a refit are counted toward the next cycle.

**New `_run_cleora_refit` pipeline (runs in background):**
1. Deletes stale `delta_hyperedges.txt` to detect whether the export produces new data
2. Spawns `export_delta_hyperedges.py` as a subprocess via `asyncio.create_subprocess_exec(sys.executable, ...)`
3. If no delta file is produced (no new interactions since last run), stops early
4. Spawns `run_cleora.py --augment data/delta_hyperedges.txt`
5. On success, calls `retriever.reload_cleora()` to hot-swap the FAISS index

Using `sys.executable` ensures the subprocess inherits the correct virtualenv.

### 4.2 Configurable Threshold (`app/config.py`)

```python
CLEORA_REFIT_THRESHOLD: int = field(
    default_factory=lambda: int(os.getenv("CLEORA_REFIT_THRESHOLD", "500"))
)
```

Default: **500 interactions**. Override at startup without touching code:
```bash
CLEORA_REFIT_THRESHOLD=50 uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4.3 Hot-Reload (`app/repository/faiss_repo.py`)

Added `Retriever.reload_cleora(cleora_data)` which rebuilds the FAISS `IndexFlatIP` from the new `.npz` and reassigns `cleora_index`, `cleora_asins`, and `asin_to_cleora_idx` in-place.

**Thread safety:** The method contains no `await` points, so the asyncio event loop cannot interleave another coroutine mid-swap — the three attribute assignments are effectively atomic from the perspective of all async request handlers. Refits always produce a same-or-larger item set, so any in-flight search indices remain within bounds of the new asins list.

---

## End-to-End Flow

```
User click/cart
      │
      ▼
POST /interact → Redis queue → _log_worker
                                    │
                              counter += 1
                                    │
                         count >= threshold?
                                    │ yes
                          refit_gate.clear()
                                    │
                     _run_cleora_refit (background task)
                      ├─ export_delta_hyperedges.py
                      ├─ run_cleora.py --augment delta_hyperedges.txt
                      └─ retriever.reload_cleora(new_npz)
                                    │
                          refit_gate.set()  ← ready for next cycle
```

---

## Files Changed

| File | Change |
| :--- | :--- |
| `scripts/export_delta_hyperedges.py` | **New** — MongoDB → delta hyperedges |
| `scripts/data/run_cleora.py` | Added `--augment` / `--augment-weight` flags |
| `app/config.py` | Added `CLEORA_REFIT_THRESHOLD` (env-configurable) |
| `app/repository/faiss_repo.py` | Added `reload_cleora()` hot-swap method |
| `app/core/lifespan.py` | Added `_run_cleora_refit()` pipeline; extended `_log_worker` with counter and gate |

---

## Documented Limitation

Items not present in `asin_to_cleora_idx` are silently skipped in `UserProfileManager.update_aggregated_embeddings()` (profile_repo.py:168). A user clicking a book outside the Cleora embedding space contributes nothing to their `cleora_profile` until the next batch refit includes that item. This is expected behaviour for a batch-refresh system and is documented as a scope limitation (OOD items).

---

*Report generated on May 5, 2026. Completes Phase B (Slow Path) and Phase C (Hot-Swap) of the dynamic Cleora integration plan.*
