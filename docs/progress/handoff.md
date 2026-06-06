# Session Handoff — May 2026

## What we did this session

---

### 1. Union pipeline (A∪B) — implemented

**Problem:** Teacher asked to implement the combined pipeline union that was already benchmarked in the report (HR@10 = 0.7886) but never wired into the backend. The UI had two separate tabs (People Also Buy / You Might Like).

**What was done:**
- `app/services/passive_recommend.py` — after both pipelines run, compute the union:
  ```python
  pab_asins = {rec[0] for rec in people_also_buy}
  combined  = people_also_buy + [rec for rec in you_might_like if rec[0] not in pab_asins]
  ```
  Pipeline A items first (Cleora order), then B's unique additions (DIF-SASRec order). No RRF — this matches exactly how `eval_joint` computed the 0.7886 figure in `evaluate_recommendation.py`.

- `app/api/routes/recommend.py` — three changes:
  - `top_k=5` → `top_k=10` per pipeline (matches the eval that produced 0.7886)
  - Added `"combined": enrich_list(rec_dict.get("combined", []))` to response
  - `_cold_start()` updated to return 20 random items split into pab + yml + combined

- `frontend/src/App.jsx` — removed the two sub-tabs (pab / yml), replaced with a single "Union (A∪B)" label bar showing both pipeline badges. Each `RecommendCard` retains its `LayerTag` ("Cleora + BGE-M3" or "DIF-SASRec") to show provenance. New-badge tracking updated to use `combined` instead of `you_might_like`.

---

### 2. Pipeline A label bug — fixed

**Problem:** Some recommendations in the combined view showed "Cleora + CLIP" instead of "Cleora + BGE-M3". Teacher would question this since the architecture describes Pipeline A as Cleora + BGE-M3 for semantic re-ranking.

**Root cause:** `passive_recommend.py` was ranking Pipeline A candidates by `max(text_score, visual_score)` and labelling whichever was higher. If a book's CLIP similarity happened to be higher than its BGE-M3 similarity, it got labelled "Cleora + CLIP".

**Fix:** Pipeline A now always ranks by `text_score` (BGE-M3) only and always labels "Cleora + BGE-M3". CLIP is still used in `content_verify` as a veto gate (OR logic: item passes if either score ≥ 0.3) but plays no role in ranking or labelling.

```python
# before
pab_ranked = sorted(verified_pab, key=lambda x: max(x["text_score"], x["visual_score"]))
layer = "Cleora + BGE-M3" if text_s >= vis_s else "Cleora + CLIP"

# after
pab_ranked = sorted(verified_pab, key=lambda x: x["text_score"])
layer = "Cleora + BGE-M3"  # always
```

---

### 3. User switch state bleed — fixed

**Problem:** Switching accounts in the demo left the previous user's Train Feed, step counter, loss sparkline, and recommendations visible until the API responded. `rlStep` never reset at all — it just kept counting across users.

**Root cause:** `App` component never unmounts on login/logout — it just re-renders. `handleLogin` only called `setUserId` and `setIsGuest`, leaving all other state from the previous user intact.

**Fix:** `handleLogin` now synchronously resets all user-scoped state before setting the new `userId`:
```javascript
setInteractions([]);
setRlStep(0);
setRlMetrics({ loss_history: [], step: 0, arch: "" });
setProfileStats({ recent_items: [] });
setTrainPulse(null);
setRecommendations({ people_also_buy: [], you_might_like: [], combined: [] });
setNewRecAsins(new Set());
setSearchResults([]);
setCart([]);
prevRecMode.current  = null;
prevYmlAsins.current = new Set();
```
`loadProfile` and `loadRecs` still fire immediately after (via `useEffect` on `userId`), so the new user's real data loads right away into a clean slate.

---

## Q&A / conceptual explanations (no code changes, good for thesis defense)

### Search score badges
- **RRF badge (100, 98, 97)** — normalized and square-root compressed: `√(raw_rrf / max_raw_rrf) × 100`. Rank #1 is always 100. Relative within a single search, not absolute. Numbers cluster near 100 because of the sqrt.
- **BGE-M3 badge (e.g. 57)** — raw cosine similarity × 100. Absolute measure, not relative to other results.
- **Why some books show only RRF, no BGE-M3** — BGE-M3 badge only appears if the book was inside that query's BGE-M3 HNSW top-50 results. Books found only by BM25/Tantivy keyword match, not by semantic HNSW, have `text_sim = 0` so the badge is hidden.
- **Why adding "Oda" to the query adds the BGE-M3 badge** — "Oda" shifts the query embedding into the One Piece neighborhood of the HNSW graph; One Piece now appears in the semantic top-50 so `text_sim` gets written.

### How FAISS maps vectors → ASINs
- FAISS stores vectors at integer positions 0..N-1. It knows nothing about ASINs.
- `asins.csv` maps position i → ASIN string (built once at index construction time).
- `asins[I[0][j]]` converts a FAISS result position to an ASIN string.
- `text_flat.reconstruct(idx)` does the reverse: ASIN → position via `asin_to_idx` → read the stored vector.
- Cleora has its own parallel list `cleora_asins` (375k items, not aligned to the 3M BGE-M3 index).

### Pipeline B candidate retrieval
- `text_profile` = weighted mean of BGE-M3 vectors of all clicked items (temporal decay λ=0.1). Sits in the semantic neighborhood of what the user reads.
- HNSW search on `text_profile` returns 200 books whose BGE-M3 vectors are nearest to that point → semantically relevant by construction.
- DIF-SASRec does NOT search — it only scores those 200. It outputs a 512-dim `intent` vector from the ordered click sequence, then `intent @ candidate_proj.T` gives a scalar score per candidate.
- `intent` ≠ `text_profile`: text_profile is the average of what you read; intent captures the *trajectory* (if you shifted from fantasy to manga, intent points toward manga even if your average still leans fantasy).

### Cleora vs DIF-SASRec core difference
- **Cleora** is order-agnostic: treats your history as a set, finds items co-purchased by similar people. Collaborative signal.
- **DIF-SASRec** is order-sensitive: reads your history left-to-right through a causal transformer, predicts what comes *next* in your trajectory. Sequential intent signal.

### Online training trigger
- Only `click` and `cart` actions trigger `train_step`. `skip` does not.
- Training input = click sequence *before* the clicked item. Target = the clicked item. 512 random negatives sampled from the 3M catalog.
- Loss = sampled softmax (push intent toward target, away from 512 negatives) + 0.1 × category cross-entropy (auxiliary genre prediction task).
- Weights saved to `data/profiles/{user_id}_dif_sasrec.pt` after every click.

### Agent pool
- 8 `DIFSASRecAgent` instances in RAM (~148 MB each ≈ 1.18 GB total).
- Every request: borrow agent → `load_user` (overwrite weights from disk) → infer/train → `save_user` → release back to pool.
- New users with no `.pt` file get the pretrained baseline weights (trained on 100k users, snapshotted in RAM at startup).

---

## Files changed this session

| File | Change |
|---|---|
| `app/services/passive_recommend.py` | Added combined union; fixed Pipeline A to rank by text_score only, label always "Cleora + BGE-M3" |
| `app/api/routes/recommend.py` | top_k 5→10; added combined to response; _cold_start returns 20 items + combined |
| `frontend/src/App.jsx` | Removed pab/yml sub-tabs; added Union label bar; reset all user state on login |
