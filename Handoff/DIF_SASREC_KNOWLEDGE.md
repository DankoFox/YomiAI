# DIF-SASRec: Complete Mechanism Reference

Everything documented here is derived from direct code inspection of the production codebase
(`app/services/dif_sasrec.py`, `app/services/passive_recommend.py`, `app/services/agent_pool.py`,
`app/repository/profile_repo.py`, `app/repository/faiss_repo.py`, `app/services/category_encoder.py`,
`app/api/routes/interact.py`, `app/api/routes/recommend.py`).

---

## Table of Contents

1. [System Constants](#1-system-constants)
2. [What Lives Where: Data Split](#2-what-lives-where-data-split)
3. [MongoDB User Document — Field-by-Field](#3-mongodb-user-document--field-by-field)
4. [Startup: AgentPool](#4-startup-agentpool)
5. [Model Architecture](#5-model-architecture)
   - 5.1 ContentProjector
   - 5.2 CategoryEncoder
   - 5.3 DIFAttentionLayer and the Alpha Fusion
   - 5.4 DIFSASRecBlock
   - 5.5 DIFSASRecModel (full forward pass)
6. [End-to-End: POST /interact (User Clicks a Book)](#6-end-to-end-post-interact-user-clicks-a-book)
7. [End-to-End: GET /recommend (Fetching Recommendations)](#7-end-to-end-get-recommend-fetching-recommendations)
   - 7.1 Pipeline A — People Also Buy (Cleora)
   - 7.2 Pipeline B — You Might Like (DIF-SASRec)
8. [Training Strategy: Sampled Softmax](#8-training-strategy-sampled-softmax)
9. [Why the Loss is ~5.x and Why That is Expected](#9-why-the-loss-is-5x-and-why-that-is-expected)
10. [Online Learning Dynamics: Loss Curve Behavior](#10-online-learning-dynamics-loss-curve-behavior)
11. [Key Design Clarifications and Common Misconceptions](#11-key-design-clarifications-and-common-misconceptions)

---

## 1. System Constants

Defined in `app/config.py` and loaded into `app/services/dif_sasrec.py`:

| Constant | Value | Meaning |
|---|---|---|
| `TEXT_EMBED_DIM` | 1024 | BGE-M3 output dimension |
| `HIDDEN_DIM` (`SASREC_HIDDEN_DIM`) | 512 | Model internal dimension (1024 → 512 projection) |
| `N_BLOCKS` | 4 | Number of DIFSASRecBlock transformer blocks |
| `N_HEADS` | 8 | Multi-head attention heads |
| `HEAD_DIM` | 64 | `HIDDEN_DIM / N_HEADS = 512 / 8` |
| `DROPOUT` | 0.2 | Dropout rate in all sub-modules |
| `LR` | 1e-3 | AdamW learning rate |
| `WEIGHT_DECAY` | 0.01 | AdamW weight decay |
| `ALPHA_INIT` | 0.7 | Initial value for the learnable α fusion parameter |
| `CAT_AUX_WEIGHT` | 0.1 | Weight of category auxiliary loss in total loss |
| `NUM_NEGATIVES` | 512 | Number of random negatives sampled per training step |
| `MAX_SEQ_LEN` | 50 | Maximum click sequence length fed to the model |
| `COLD_START_THRESHOLD` | 5 | Minimum clicks before personalized recommendations |
| `PERSONAL_CANDIDATES` | 200 | HNSW KNN retrieval count for Pipeline B |
| `SIMILARITY_THRESHOLD` | 0.3 | Content veto dot product threshold |
| `MAX_RECENT_INTERACTIONS` | 50 | Rolling deque size for recent interactions |
| `TEMPORAL_DECAY` | 0.1 | Exponential decay λ for profile embedding weights |
| `TOP_K` | 10 | Final recommendation count per pipeline |
| `BEHAVIORAL_CANDIDATES` | configurable | Cleora candidate pool size (Pipeline A) |
| `AGENT_POOL_SIZE` | 8 | Number of concurrent DIFSASRecAgent instances |

> **Note on stale comments:** The docstring at the top of `dif_sasrec.py` says "256-dim hidden space."
> This is stale. The actual value is 512. The `# [256]` comment in `get_intent_vector` is also wrong.
> Trust the constants above, not the docstring.

---

## 2. What Lives Where: Data Split

The user state is split across two separate storage systems:

### MongoDB (aggregated behavioral state)
Stores vectors and interaction history. Updated on every click event.

| What | Size | When updated |
|---|---|---|
| `text_profile` | 1024-dim float array | Every click/cart event |
| `visual_profile` | 512-dim float array | Every click/cart event |
| `cleora_profile` | 1024-dim float array | Every click/cart event |
| `recent_history` | Up to 50 `{item_id, action, timestamp}` entries | Every interaction |
| `recent_interactions` | Up to 50 ASIN strings (rolling deque) | Every click/cart event |
| `recent_recs` | Up to 20 recommendation log entries | Every /recommend call |
| `recent_searches` | Up to 20 search query entries | Every search |

### Disk (`data/profiles/{user_id}_dif_sasrec.pt`)
Stores the personalized model checkpoint as a PyTorch `.pt` file. Contains:
- `model_state`: all transformer weights (Q/K/V projections, FFN, LayerNorm, alpha_logit, etc.)
- `optimizer_state`: AdamW momentum and variance terms — persists across sessions
- `step`: total number of gradient steps taken for this user
- `loss_history`: last 200 loss values (rolling window)
- `num_categories`: vocab size, used for architecture reconstruction

> **Key insight:** MongoDB and the `.pt` file are independent. MongoDB does not store model weights.
> The `.pt` file does not store interaction history. They evolve in parallel.

---

## 3. MongoDB User Document — Field-by-Field

Example document seen in production:
```
_id:                  ObjectId('69ddc24a43742235de6d817a')
user_id:              "user123"
cleora_profile:       Array (1024 items)
last_updated:         "2026-04-14T13:16:43.831017"
recent_history:       Array (23 items)
recent_interactions:  Array (23 items)
recent_recs:          Array (20 items)
recent_searches:      Array (empty)
text_profile:         Array (1024 items)
visual_profile:       Array (512 items)
```

**`text_profile` [1024]:** Exponentially time-decayed weighted average of BGE-M3 embeddings for
every book the user has clicked or added to cart. More recent clicks get higher weight.
The exact formula (`profile_repo.py:272`):
```python
weights = np.exp(0.1 * np.arange(N))   # index 0 = oldest, index N-1 = most recent
weights /= weights.sum()               # normalize to sum=1
text_profile = np.average(text_vecs, axis=0, weights=weights)
```
With N=23 clicks, weight spread is `exp(0) = 1.0` (oldest) to `exp(0.1×22) ≈ 9.03` (most recent).
This vector is used as the HNSW query in Pipeline B (step 1), and as the text-similarity anchor
in the content veto filter.

**`visual_profile` [512]:** Same exponential weighting applied to CLIP embeddings for each clicked
item. Used only in the content veto filter.

**`cleora_profile` [1024]:** Same exponential weighting applied to Cleora co-purchase graph
embeddings. Used in Pipeline A (collaborative filtering via FAISS `IndexFlatIP`).

**`recent_history` [up to 50]:** Merged, reverse-sorted list of all click and skip events.
Each entry: `{item_id, action: "click"|"cart"|"skip", timestamp}`.

**`recent_interactions` [up to 50]:** Rolling deque of the last 50 item_ids from click/cart events
only. Used in Pipeline A as seeds for `get_behavioral_candidates()`.

**`recent_recs` [up to 20]:** Log of the last 20 recommendation batches served to this user.
Each entry: `{timestamp, item_ids: [...]}`. For analytics/debugging only, not used in ML pipeline.

**`recent_searches` [up to 20]:** Log of search queries. Not used in recommendation pipeline.

### Important: `text_profile` is NOT L2-normalized

The HNSW index stores pre-normalized BGE-M3 unit vectors. The `text_profile` is a weighted mean
of unit vectors, which is NOT a unit vector itself. Its magnitude encodes taste diversity:
- User who only reads manga: `text_profile` magnitude ≈ 1.0 (all vectors point same direction)
- User who reads many genres: `text_profile` magnitude < 1.0 (vectors spread across space)

`get_content_candidates()` (`faiss_repo.py:185`) passes this un-normalized vector directly to
HNSW search without calling `faiss.normalize_L2()`. This means the search is inner product, not
true cosine similarity. The content veto dot products (`user_text_profile @ item_text`) are also
not true cosine similarities. The 0.3 threshold is empirically tuned against this reality.

---

## 4. Startup: AgentPool

`AgentPool` (`app/services/agent_pool.py`) is initialized in `lifespan.py` at app startup.

**What it does:**
- Creates exactly `AGENT_POOL_SIZE = 8` independent `DIFSASRecAgent` instances
- Each agent has its own model weights, optimizer state, and GPU memory
- Instances are stored in an `asyncio.Queue` — routes borrow and return them

**Why 8 agents?**
- Each agent: ~148 MB (model weights + AdamW optimizer moments)
- 8 agents × 148 MB ≈ 1.18 GB VRAM
- Eliminates race conditions: a single shared agent reused across concurrent requests would
  cause one user's `load_user()` to corrupt another user's weights mid-inference

**Startup sequence:**
```python
# agents built in a thread (GPU loads are blocking, would stall event loop)
agents = await run_in_executor(None, self._build_agents)
for agent in agents:
    self._pool.put_nowait(agent)
```

**Per agent initialization:**
1. Load pretrained weights from `data/dif_sasrec_pretrained.pt` (trained offline on 100k users)
2. Immediately snapshot those weights in CPU RAM:
   ```python
   self._pretrained_state       = copy.deepcopy(self.model.state_dict())
   self._pretrained_opt_state   = copy.deepcopy(self.optimizer.state_dict())
   ```
   This snapshot is the "clean slate" that new users receive. It never changes at runtime.
3. Build `_all_asins` list for negative sampling during online training

**Borrow pattern:**
```python
async with container.agent_pool.borrow() as agent:
    agent.load_user(user_id, settings.DATA_DIR)
    # ... use agent ...
    agent.save_user(user_id, settings.DATA_DIR)
# agent automatically returned to pool even on exception
```

If all 8 agents are busy, the 9th request awaits via `asyncio.Queue.get()` — no error, no dropped
request, just queuing.

---

## 5. Model Architecture

### 5.1 ContentProjector

**File:** `dif_sasrec.py:50–67`  
**Purpose:** Reduces BGE-M3 1024-dim embeddings to 512-dim hidden space.

```python
class ContentProjector(nn.Module):
    def __init__(self, in_dim=1024, out_dim=512):
        self.proj = nn.Linear(in_dim, out_dim)
        self.norm = nn.LayerNorm(out_dim)
        self.drop = nn.Dropout(DROPOUT)

    def forward(self, x):
        return self.drop(self.norm(self.proj(x)))
```

**Shape:** `[*, 1024] → [*, 512]`

**The three layers in sequence:**

**`nn.Linear(1024, 512)`** — learned dimensionality reduction:
```
output = input @ W.T + b
[*, 512] = [*, 1024] @ [1024, 512] + [512]
```
W is a 1024×512 learned weight matrix. Unlike PCA (which is deterministic), this projection adapts
through gradient descent to serve the recommendation task. It learns which combinations of the
1024 BGE-M3 dimensions are predictive for sequential behavior.

**`nn.LayerNorm(512)`** — normalizes across the 512 feature dimensions per token, per example:
```
x_norm = (x - mean(x)) / sqrt(var(x) + 1e-5)
output = x_norm * γ + β       # γ and β are learned scalars per dimension
```
This is per-position normalization, NOT batch normalization. It doesn't care about batch size or
sequence length — it normalizes each 512-dim vector independently. Prevents internal covariate
shift: the raw Linear output can have wildly different scales for different books (dense academic
text vs. children's book produce very different BGE-M3 magnitudes). LayerNorm recenters everything.

**`nn.Dropout(p=0.2)`** — randomly zeros 20% of values during training, identity at inference:
```
Training:  each value set to 0 with p=0.2; survivors scaled by 1/0.8
Inference: no-op (model.eval() disables it)
```
Forces downstream attention layers not to rely on any single projected dimension. Regularization
against overfitting to the pretraining dataset.

There are **two separate ContentProjector instances** in the model:
- `self.content_proj` — projects the input sequence items
- `self.candidate_proj` — projects candidate items for scoring

They are independent (not shared weights) so the model can learn different projections for
"items in a sequence" vs. "items being scored as next candidates."

---

### 5.2 CategoryEncoder

**File:** `app/services/category_encoder.py`

Categories come from `item_metadata.parquet`, **not** from BGE-M3 or any neural encoder.

**Build process (`build_from_parquet`):**

Each book in the parquet has a `categories` column with a pipe-separated hierarchy:
```
"Books|Literature & Fiction|Action & Adventure"
```
The encoder extracts the **leaf** (last segment): `"Action & Adventure"`. This is the leaf category.

ID assignment:
```
0 → PAD   (padding token for sequences shorter than MAX_SEQ_LEN)
1 → UNK   (book missing from parquet, or no category field)
2 → "Action & Adventure"         (alphabetically sorted from index 2)
3 → "Animals"
4 → "Anime & Manga"
...
N → last sorted leaf category
```

Two lookup dicts built:
- `vocab`: `{"Action & Adventure": 2, "Animals": 3, ...}` — string → int
- `asin_to_cat_id`: `{"B00ABC123": 4, ...}` — ASIN → int (direct O(1) lookup)
- `id_to_cat`: reverse lookup int → string

**At runtime:**
```python
category_encoder.get_category_id("B00XYZ456")   # → e.g., 4 ("Anime & Manga")
category_encoder.encode_sequence(asin_list)      # → [4, 4, 12, 4, 7, ...]
```

**`num_categories`** determines the size of the `category_emb` embedding table in the model.
Saved as a JSON file at setup time and reloaded at startup for consistency across restarts.

---

### 5.3 DIFAttentionLayer and the Alpha Fusion

**File:** `dif_sasrec.py:70–155`

This is the core of the DIF (Decoupled Information Feature) mechanism.

**Critical clarification — what α fuses:**

α does NOT add the 512-dim content embedding and 512-dim category embedding together.
α fuses the **attention score matrices** (shape `[B, H, T, T]`), not the value tensors.

**Full forward pass traced:**

```python
# Input shapes:
# content:   [B, T, 512]   projected BGE-M3 embeddings
# category:  [B, T, 512]   category embeddings from category_emb lookup table

# --- Content stream: produces Q, K, and V ---
Q_c = split_heads(q_content(content))    # [B, 8, T, 64]   content query
K_c = split_heads(k_content(content))    # [B, 8, T, 64]   content key
V   = split_heads(v_content(content))    # [B, 8, T, 64]   content value

# --- Category stream: produces Q and K ONLY (no category V) ---
Q_k = split_heads(q_cat(category))       # [B, 8, T, 64]   category query
K_k = split_heads(k_cat(category))       # [B, 8, T, 64]   category key

# --- Two attention score matrices ---
A_content  = softmax((Q_c @ K_c.T) * scale)    # [B, 8, T, T]
A_category = softmax((Q_k @ K_k.T) * scale)    # [B, 8, T, T]
# (causal mask applied before softmax — upper triangle set to -inf)

# --- Alpha fusion: blending the SCORE MATRICES ---
alpha   = sigmoid(alpha_logit)                  # scalar, ~0.7
A_fused = alpha * A_category + (1-alpha) * A_content    # [B, 8, T, T]

# --- Apply fused attention to CONTENT values only ---
out = A_fused @ V                               # [B, 8, T, 64]
out = out.reshape(B, T, 512)                    # [B, T, 512]
out = out_proj(out)                             # [B, T, 512]
```

**What each component contributes:**

`A_content [B, H, T, T]` answers: "how much should position `i` attend to position `j` based on
the SEMANTIC SIMILARITY of their content embeddings?" (what those specific books are about)

`A_category [B, H, T, T]` answers: "how much should position `i` attend to position `j` based on
the GENRE SIMILARITY of their categories?" (what genre those books belong to)

`A_fused` is a blend of these two perspectives on relevance.

`V` (values) always comes from content only — the category stream has no V projection.

**The output is still 512-dim** — not a concatenation, not a vector addition of content + category.
The category information shapes *which past positions' content* gets aggregated, but the content
being aggregated is always from the content stream.

**Analogy:** You're deciding which past books to "remember" (A_fused), but the memories themselves
(V) always come from the content embeddings. Category tells you which memories to prioritize;
content provides the actual memory substance.

**The `_split_heads` operation:**
```python
def _split_heads(self, x):   # [B, T, 512] → [B, 8, T, 64]
    return x.view(B, T, 8, 64).transpose(1, 2)
```
Splits the 512-dim vector into 8 independent heads of 64-dim each. Each head learns a different
"aspect" of relevance. The 8 heads run in parallel with the same Q/K/V weights but separate
attention computations.

**The causal mask:**
```python
mask = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
# Applied: A.masked_fill(mask, float("-inf"))
```
Upper-triangular boolean matrix. Position `i` can only attend to positions `0..i`.
Position 3 cannot see positions 4, 5, ..., T-1. This enforces the autoregressive property:
the model can only use past context to predict the next item.

**The learnable α:**
```python
import math
init_logit = math.log(ALPHA_INIT / (1.0 - ALPHA_INIT))   # log(0.7/0.3) ≈ 0.847
self.alpha_logit = nn.Parameter(torch.tensor(init_logit))
# At forward: alpha = sigmoid(alpha_logit) ≈ 0.7
```
α is stored as `alpha_logit` (unbounded real number) and converted via sigmoid to ensure it stays
in [0, 1]. It is a fully trainable `nn.Parameter` — changes with every gradient step.

**Why α=0.7 initialization:**
Before any training, the model should rely more on category structure than fine-grained content.
Genre-level signals ("this user likes manga") are stable and generalizable. Item-level content
signals ("this user likes *this specific art style*") are noisier and require more data to learn.
Starting with category-dominant fusion helps training converge faster on the pretraining dataset.

**Where α=0.7 comes from at runtime:**
- The value 0.7 is only used once — at the start of pretraining from scratch
- After pretraining on 100k users, the pretrained `.pt` checkpoint contains whatever `alpha_logit`
  converged to (could be 0.65, 0.72, etc. — not necessarily 0.7)
- Every new user loads the pretrained `alpha_logit`, not the hardcoded 0.7 init
- Per-user fine-tuning continues updating `alpha_logit` further

Each of the 8 agents in the pool has its own independent `alpha_logit` tensor, overwritten on
every `load_user()` call.

---

### 5.4 DIFSASRecBlock

**File:** `dif_sasrec.py:158–186`

One complete transformer block. Pre-norm architecture (LayerNorm before each sub-layer).

```python
def forward(self, content, category, causal_mask):
    # DIF-Attention sub-layer (pre-norm + residual)
    h = content + drop(attn(norm1(content), category, causal_mask))

    # FFN sub-layer (pre-norm + residual)
    h = h + drop(ffn(norm2(h)))
    return h
```

**FFN architecture:**
```
Linear(512 → 1024) → GELU → Dropout(0.2) → Linear(1024 → 512)
```
The 512 → 1024 expansion lets the FFN capture complex non-linear interactions that attention
alone cannot. GELU (Gaussian Error Linear Unit) is smoother than ReLU, used in most modern
transformers. Bottleneck back to 512 preserves the residual dimension.

**Pre-norm vs. post-norm:** LayerNorm is applied to the INPUT before the sub-layer, not to the
output after. This stabilizes gradients in deep networks and is the standard in modern transformers.

**Residual connections:** Both `content + attn_output` and `h + ffn_output` add the input back.
This means gradients flow directly from the loss to early layers without passing through all
transformer blocks — prevents vanishing gradients.

The block runs 4 times (`N_BLOCKS = 4`). Each pass enriches the representation with
deeper, more abstract sequential patterns. The `category` tensor is passed unchanged into each
block — only `content` (which carries the residual) evolves through the blocks.

---

### 5.5 DIFSASRecModel (Full Forward Pass)

**File:** `dif_sasrec.py:189–276`

```python
class DIFSASRecModel(nn.Module):
    def __init__(self, num_categories, hidden_dim=512, n_blocks=4, max_len=50):
        self.content_proj   = ContentProjector(1024, 512)
        self.category_emb   = nn.Embedding(num_categories, 512, padding_idx=0)
        self.position_emb   = nn.Embedding(50, 512)
        self.blocks         = nn.ModuleList([DIFSASRecBlock(512) for _ in range(4)])
        self.final_norm     = nn.LayerNorm(512)
        self.candidate_proj = ContentProjector(1024, 512)
        self.category_head  = nn.Linear(512, num_categories)  # auxiliary task
        # Pre-built causal mask buffer (trimmed to actual T at runtime)
        self.register_buffer("causal_mask_full", torch.triu(..., diagonal=1))
```

**`category_emb` — NOT from BGE-M3:**
```python
self.category_emb = nn.Embedding(num_categories, 512, padding_idx=0)
```
This is a lookup table: matrix of shape `[num_categories, 512]`, initialized randomly, trained
from scratch via backprop. Passing category ID `4` does: `category_emb.weight[4]` — direct row
access, O(1), no computation.

It is completely separate from BGE-M3:
- BGE-M3 embeddings encode what a *specific book* is about (fine-grained semantics)
- `category_emb` encodes what a *genre* means in the context of sequential reading patterns

The genre embeddings learn co-occurrence patterns from training sequences: which genres tend to
follow which other genres, encoded purely through gradient descent on user click data.

**Full forward pass (`DIFSASRecModel.forward`):**

```python
def forward(self, bge_seqs, cat_ids, lengths):
    # Inputs:
    # bge_seqs: [B, T, 1024]  BGE-M3 embeddings for clicked sequence
    # cat_ids:  [B, T]        category IDs (0=PAD)
    # lengths:  [B]           actual sequence lengths (non-padded)

    # 1. Content projection + positional encoding
    content  = content_proj(bge_seqs)                          # [B, T, 512]
    pos_ids  = arange(T).expand(B, -1)
    content  = content + position_emb(pos_ids)                 # [B, T, 512]

    # 2. Category embedding
    category = category_emb(cat_ids)                           # [B, T, 512]

    # 3. Causal mask (trimmed to actual sequence length)
    causal_mask = causal_mask_full[:T, :T].unsqueeze(0).unsqueeze(0)   # [1, 1, T, T]

    # 4. Four DIFSASRecBlocks
    h = content
    for block in blocks:
        h = block(h, category, causal_mask)                    # [B, T, 512] each pass

    h = final_norm(h)                                          # [B, T, 512]

    # 5. Extract intent vector at last valid position
    idx    = (lengths - 1).clamp(min=0)                        # [B]
    intent = h[arange(B), idx]                                 # [B, 512]

    # 6. Category auxiliary prediction
    cat_logits = category_head(h)                              # [B, T, num_categories]

    return h, intent, cat_logits
```

**The intent vector:** `h[batch, last_valid_position]` — the 512-dim hidden state at the final
non-padded position. This is the model's compressed representation of the entire click sequence
and what it predicts the user will want next. It "mathematically embodies" the sequential pattern.

**Candidate scoring:**
```python
def score_candidates(self, intent, candidate_bge):
    # intent:         [B, 512]
    # candidate_bge:  [N, 1024]
    cand_proj = candidate_proj(candidate_bge)   # [N, 512]
    return intent @ cand_proj.T                 # [B, N]  — dot products
```

---

## 6. End-to-End: POST /interact (User Clicks a Book)

**Route file:** `app/api/routes/interact.py`  
**Request:** `{user_id, item_id, action: "click"|"cart"|"skip", session_id, source}`

### Step 1 — Capture state BEFORE the click
```python
click_seq_before = await profile_manager.get_click_sequence(req.user_id)
```
Returns ordered list of ASINs for all prior click/cart events (up to 50). This is critical —
it must be captured before the profile is updated, because this is the training input sequence
(the model needs to see what came *before* the new click).

### Step 2 — Profile update (click/cart)
`await profile_manager.log_click(user_id, item_id, source="web_ui", action=action)`

Inside `log_click`:
1. Append `{timestamp, item_id, source, position, action}` to `profile.clicks`
2. Append `item_id` to `profile.recent_interactions` deque (rolls off oldest if > 50)
3. Update `profile.preferred_categories` counter (genre name → count)
4. Call `update_aggregated_embeddings(profile)`:
   - Iterate all items in `profile.clicks` (entire history, not just recent)
   - For each item: `text_flat.reconstruct(idx)` → 1024-dim BGE-M3 vector from FAISS flat index
   - Also get CLIP vector (512-dim) and Cleora vector (1024-dim) per item
   - Compute temporal decay weights: `exp(0.1 * arange(N)) / sum`
   - `text_profile   = np.average(text_vecs,   axis=0, weights=weights)`
   - `visual_profile = np.average(clip_vecs,   axis=0, weights=weights)`
   - `cleora_profile = np.average(cleora_vecs, axis=0, weights=weights)`
5. `await db.upsert_profile(user_id, payload)` — persist to MongoDB

For `skip` action: only records purchase entry, NO embedding update, NO DIF-SASRec training.

### Step 3 — Redis logging
Raw interaction entry pushed to `nba_interactions` Redis list for async analytics.
```python
log_entry = {user_id, asin, action, timestamp, session_id, source, is_guest}
await db.redis.rpush("nba_interactions", json.dumps(log_entry))
```

### Step 4 — DIF-SASRec online training (click/cart only, only if click_seq_before non-empty)
```python
async with container.agent_pool.borrow() as agent:
    agent.load_user(req.user_id, settings.DATA_DIR)
    loss = recommend_engine.train_personal(
        req.user_id, req.item_id, agent,
        click_seq_before=click_seq_before,
    )
    agent.save_user(req.user_id, settings.DATA_DIR)
```

**`agent.load_user(user_id, data_dir)`:**
- Checks if `data/profiles/{user_id}_dif_sasrec.pt` exists
- **Returning user:** loads personal checkpoint — model weights, optimizer state, step, loss_history
- **New user:** resets to `_pretrained_state` (the CPU snapshot of pretrained weights taken at startup)
  ```python
  self.model.load_state_dict(self._pretrained_state)
  self.optimizer.load_state_dict(self._pretrained_opt_state)
  self._step = self._pretrained_step
  ```
  Every new user starts from identical pretrained weights. The pretrained state is never mutated.

**`train_personal()` → `agent.train_step(click_seq_before, item_asin, cat_id, all_asins)`:**

1. `target_vec = _get_asin_vec(item_asin)` — 1024-dim BGE-M3 for the clicked book (the positive)
2. `_build_tensors(click_seq_before)`:
   - Take last 50 ASINs from click history
   - For each: `text_flat.reconstruct(asin_to_idx[asin])` → 1024-dim BGE-M3
   - Get category ID via `category_encoder.get_category_id(asin)`
   - Zero-pad to `[1, 50, 1024]` (bge) and `[1, 50]` (cat), `lengths=[T]`
3. Forward pass: `model(bge_t, cat_t, len_t)` → `(_, intent [1, 512], cat_logits [1, T, num_cats])`
4. Sample 512 random negatives from `all_asins`, reconstruct their BGE-M3 vecs from FAISS
5. Sampled softmax loss (see Section 8)
6. Category auxiliary loss
7. Backprop + AdamW step + gradient clip (max_norm=1.0)
8. `_step += 1`, append loss to `loss_history`

**`agent.save_user(user_id, data_dir)`:**
Writes PyTorch checkpoint to `data/profiles/{user_id}_dif_sasrec.pt`.
The AdamW optimizer state is saved too — momentum and variance terms carry over across sessions,
meaning the per-user model keeps learning with accumulated gradient statistics.

### Response
```json
{"status": "ok", "reward": 1.0, "sasrec_loss": 0.087}
```

---

## 7. End-to-End: GET /recommend (Fetching Recommendations)

**Route file:** `app/api/routes/recommend.py`  
**Request:** `GET /recommend?user_id=...`

### Cold start check
```python
profile = await profile_manager.get_profile(user_id)
if len(profile.clicks) < COLD_START_THRESHOLD:  # < 5 clicks
    # Serve 20 random books from the Cleora catalog
    # 10 in "people_also_buy", 10 in "you_might_like", mode="cold_start"
    return _cold_start(retriever)
```

### Warm user path
```python
async with container.agent_pool.borrow() as agent:
    agent.load_user(user_id, settings.DATA_DIR)
    res = await recommend_engine.recommend_for_user(user_id, agent, top_k=10)
```

`recommend_for_user` runs two independent pipelines:

---

### 7.1 Pipeline A — People Also Buy (Cleora)

**Purpose:** Behaviorally related books via co-purchase graph embeddings.

**Step 1 — Cleora FAISS search:**
```python
query_vec = profile.cleora_profile.reshape(1, -1).astype("float32")
faiss.normalize_L2(query_vec)
D, I = retriever.cleora_index.search(query_vec, top_n=BEHAVIORAL_CANDIDATES)
candidates = [cleora_asins[i] for i in I[0]]
```
`cleora_index` is `IndexFlatIP` (inner product, but vectors are pre-normalized → cosine similarity).

**Step 2 — Seed expansion:**
Take last 5 items from `profile.recent_interactions`, call `get_behavioral_candidates(item_id)`
for each — adds more co-purchase neighbors. Union of all candidates, minus already-seen items.

**Step 3 — Content veto:**
For each candidate:
```python
item_text = text_flat.reconstruct(asin_to_idx[asin])   # [1024]
item_clip = clip_index.reconstruct(asin_to_idx[asin])  # [512]
text_sim   = float(profile.text_profile @ item_text)
visual_sim = float(profile.visual_profile @ item_clip)
if text_sim >= 0.3 or visual_sim >= 0.3:
    keep(asin)
```
Filters out behaviorally popular books that don't match the user's content preferences.

**Step 4 — Rank and return:**
Sort survivors by `text_score` descending, take top 10.
Return as `(asin, text_score, "Cleora + BGE-M3", {text_sim, img_sim})`.

---

### 7.2 Pipeline B — You Might Like (DIF-SASRec)

**Purpose:** Sequential intent-based recommendations. Zero dependency on Cleora.

**Step 1 — HNSW KNN retrieval (200 candidates):**
```python
candidates = retriever.get_content_candidates(
    profile.text_profile,        # [1024] un-normalized weighted mean of clicked BGE-M3 vecs
    top_n=200,
    exclude_asins=seen_items,
)
```
Queries `text_index` (BGE-M3 HNSW, 1.7M vectors) with the user's profile vector.
Retrieves 200 semantically similar unseen books. This is the coarse retrieval stage.

**Step 2 — Content veto (same as Pipeline A):**
Filter out candidates with both text_sim < 0.3 AND visual_sim < 0.3.
Ensures only content-relevant books survive.

**Step 3 — Fetch click sequence with categories:**
```python
asins, cat_ids = await profile_manager.get_click_sequence_with_categories(user_id)
# asins:   ordered list of up to 50 clicked ASINs (oldest first)
# cat_ids: corresponding integer category IDs from CategoryEncoder
```

**Step 4 — DIF-SASRec scoring:**
```python
scores = agent.get_candidate_scores(asins, cat_ids, candidate_asins)
# {asin: float_score} dict
```
Inside `get_candidate_scores`:
- `_build_tensors(asins, cat_ids)` → same tensor building as training
- `model.eval()` + `torch.no_grad()`
- Forward pass → `intent [1, 512]` (user's current sequential intent vector)
- For each surviving candidate: reconstruct its 1024-dim BGE-M3 from FAISS
- `model.score_candidates(intent, cand_t)`:
  - `candidate_proj(cand_bge)` → `[N, 512]`
  - `intent @ cand_proj.T` → `[1, N]` dot products
- Returns `{asin: float_score}`

**Step 5 — Normalize and return:**
```python
lo, hi = min(scores), max(scores)
normalized = {asin: (s - lo) / (hi - lo) for asin, s in scores.items()}
# Top 10 → [(asin, score, "DIF-SASRec")]
```

### Final assembly
- Pipeline A and B results combined (Pipeline B items already in A are deduplicated in `combined`)
- Each ASIN enriched with metadata from `metadata_repo.get_item(asin)` (title, author, genre, image URL from parquet)
- Recommendation event logged to `profile.recommendations` → MongoDB
- Return JSON with `people_also_buy`, `you_might_like`, `combined`, `user_id`, `mode`

### Two separate user representations, evolving in parallel

| | `text_profile` (MongoDB) | DIF-SASRec weights (disk) |
|---|---|---|
| What it captures | Long-term taste — decayed average of all liked books' semantic content | Short-term sequential intent — transformer trained to predict next click from recent sequence |
| Updated when | Every interaction (full recompute over all clicks) | Every click/cart (one gradient step on the new sequence → next_click example) |
| Used for | HNSW retrieval seed (coarse), content veto filter | Re-ranking the 200 HNSW candidates (fine) |
| Storage | 1024 floats in MongoDB | ~148 MB PyTorch checkpoint on disk |

**DIF-SASRec is a re-ranker, not a first-stage retriever.** The HNSW index does coarse retrieval
(3M → 200 candidates) using the averaged profile. DIF-SASRec then scores those 200 to surface the
10 that match where the user's reading interests are heading *right now*, based on the sequential
pattern of their recent clicks rather than just their all-time average.

---

## 8. Training Strategy: Sampled Softmax

### The problem
Full softmax over 3M items at every training step is computationally infeasible online:
- Would require projecting 3M BGE-M3 vectors through `candidate_proj` per click
- Each FAISS reconstruction is a memory-mapped I/O call

### The solution: treat it as 513-class classification
Sample 512 random negatives, compute softmax over 1 positive + 512 negatives = 513 items total.

### Step-by-step (single online training step)

**Setup:**
```
click_seq_before = [B0, B1, ..., B_{N-1}]   ← input sequence (before the click)
target = B_N                                  ← the book the user just clicked (positive)
```

**1. Get positive embedding:**
```python
target_vec = _get_asin_vec(target)   # [1024] BGE-M3 from FAISS flat index
```

**2. Sample 512 negatives:**
```python
neg_pool  = [a for a in all_asins if a != target]   # ~375k books
neg_asins = np.random.choice(neg_pool, size=512, replace=False)
neg_vecs  = [_get_asin_vec(a) for a in neg_asins]   # [512, 1024]
```
Negatives are drawn uniformly at random — **no guarantee they are truly "bad" books** for this
user. Some may be books the user would genuinely enjoy (false negatives). This introduces
irreducible noise into the training signal.

**3. Stack into [513, 1024] tensor:**
```python
all_t = cat([pos_t, neg_t], dim=0)   # positive is always at index 0
```

**4. Forward pass → intent vector:**
```
model(bge_t, cat_t, len_t) → intent [1, 512]
```

**5. Score all 513 candidates:**
```python
scores = model.score_candidates(intent, all_t)   # [513] dot products
# internally: candidate_proj(all_t) → [513, 512]; intent @ cand.T → [513]
```

**6. Sampled softmax loss:**
```python
target_idx   = torch.zeros(1, dtype=torch.long)   # positive = class 0
softmax_loss = F.cross_entropy(scores.unsqueeze(0), target_idx)
```

Expanded form:
```
loss = -log( exp(score_pos) / (exp(score_pos) + Σᵢ₌₁⁵¹² exp(score_neg_i)) )
     = -score_pos + log(exp(score_pos) + Σᵢ exp(score_neg_i))
```

For a well-trained model: `score_pos >> all score_neg_i` → `loss → 0`
For random model: all scores equal → `loss = log(513) ≈ 6.24`

**7. Category auxiliary loss (weight 0.1):**
```python
last_logit = cat_logits[0, T-1]         # [num_categories] — predicted genre at last position
cat_loss   = cross_entropy(last_logit, target_cat_id)
```
Encourages the model to predict the correct genre at the last sequence position. Provides an
additional regularization signal and speeds up convergence of the category attention stream.

**8. Total loss:**
```python
total_loss = softmax_loss + 0.1 * cat_loss
```

**9. Backprop:**
```python
optimizer.zero_grad()
total_loss.backward()
clip_grad_norm_(model.parameters(), max_norm=1.0)
optimizer.step()
```
Gradient clipping at max_norm=1.0 prevents a single extreme sample from causing catastrophic
weight updates. This is especially important in online learning where the model sees only one
example at a time.

---

## 9. Why the Loss is ~5.x and Why That is Expected

### The random baseline
With 1 positive and 512 negatives, the random-chance baseline is:
```
log(1 + 512) = log(513) ≈ 6.24
```
This is the loss if the model assigns exactly equal probability to all 513 items.

A loss of **5.x means the model is doing better than random** — it assigns approximately
`exp(-(5.x - 6.24)) = exp(1.x) ≈ 3–4×` higher probability to the positive than random chance.

### Four concrete reasons why 5.x is correct

**1. Online learning has minimal updates per user.**
Each click fires exactly ONE gradient step. A user with 23 clicks has had 23 online updates
on top of the pretrained model (which was trained for many epochs on 100k users). The per-user
fine-tuning is lightweight by design — it nudges the pretrained model toward this user's
preferences without extensive retraining. The loss not converging to near-zero is correct.

**2. False negatives contaminate the 512 negatives.**
Negatives are drawn randomly from ~375k books. Some will be books the user would genuinely enjoy
but hasn't clicked yet. The model gets penalized for scoring them highly. This introduces a floor
on the achievable loss regardless of model quality.

**3. Training loss ≠ recommendation quality.**
HR@10 = 0.7886 (78.86% of the time the actual next item appears in the top 10 retrieved from 3M).
This is measured on HNSW-retrieved candidates pre-filtered by the profile vector — not on 512
random books. The training loss and HR@10 measure completely different things.
A model with training loss 5.x can deliver excellent recommendations because:
- During inference, it only re-ranks 200 semantically pre-filtered candidates
- Those 200 are already in the relevant neighborhood of embedding space
- Random negatives are from the entire 3M catalog, most completely irrelevant

**4. The category auxiliary loss adds a small constant overhead.**
With e.g. 50 categories, random category baseline ≈ `log(50) ≈ 3.9`.
Contribution to total loss: `0.1 × 3.9 ≈ 0.4`. Minor but adds to the observed 5.x figure.

### One-line answer for council day
> "The random-chance baseline for this loss is log(513) = 6.24. A loss of 5.x means the model
> ranks the actual next item 3–4× above random chance. This is expected for online learning with
> one gradient step per click, 512 randomly sampled negatives that may contain false negatives,
> and a training task (rank 1 item among 513 random samples) that is harder than the inference
> task (rank 1 item among 200 pre-filtered candidates)."

---

## 10. Online Learning Dynamics: Loss Curve Behavior

### The full loss trajectory

**New user (cold start):** Loss ≈ 5.x. Pretrained generalist prior. Model knows broad genre
patterns from 100k pretraining users but nothing specific about this individual.

**After 8 consecutive manga/anime clicks:** Loss drops to ≈ 0.x.

**User clicks "Java Programming":** Loss spikes back to ≈ 5.x or higher.

**Continued programming clicks:** Loss gradually lowers again.

---

### Why loss drops to ~0.x after 8 consecutive manga clicks

**Geometrically:** BGE-M3 embeddings for manga/anime books cluster tightly together in 1024-dim
semantic space. After content projection to 512-dim, they remain clustered. After 4 transformer
blocks processing 8 similar items, the intent vector converges to a specific region of 512-dim
space that strongly points toward the manga cluster.

**In the scoring step:** `intent @ candidate_proj(next_manga)` produces a very high dot product
because both vectors are in the same cluster. The 512 random negatives: statistically maybe 5–10
are manga, 490+ are completely different genres. So `score_pos >> score_neg_i` for ~490+ negatives.

```
loss = -score_pos + log(exp(score_pos) + Σ exp(score_neg_i))
     → 0  when score_pos >> all negatives
```

**In the model weights:** 8 gradient steps have accumulated in the same direction — all Q/K/V
projection matrices, `alpha_logit`, and `category_emb` entries have been nudged to specialize
toward "manga sequence → predict manga." This is intentional: it is personalization working.

This is a form of **local overfitting to a highly regular pattern**. The model has learned to
complete [manga, manga, manga, ...] → manga with very high confidence.

---

### Why loss jumps when user clicks "Java Programming"

The sequence entering the model is `[manga₁ ... manga₈]`, target is `java_book`.

**The intent vector is manga-specialized.** The transformer has processed 8 manga items; the
512-dim intent vector firmly points into the manga cluster.

**The positive item is semantically distant.** BGE-M3 embeddings for Java programming books live
in a completely different region of 1024-dim space — different vocabulary, different semantic
content, far from the manga cluster. After projection through `candidate_proj`, Java's 512-dim
vector has a **low dot product** with the manga-specialized intent vector.

**The negatives become competitive.** Some random negatives (fantasy, light novels) may have
higher dot products with the manga intent than Java does.

```
score_pos (java)          ← low
score_neg (some books)    ← possibly higher than score_pos
→ loss spikes
```

This is **distribution shift** — the user's behavior deviates from what the model just specialized
in. The high loss is the mathematical expression of "the model did not expect this."

**Critical:** a high loss also means a **large gradient magnitude**. This is the most impactful
gradient step of the entire session — the model fires a large update in the direction of
"even from a manga sequence, cross-genre jumps to programming are possible."

This also demonstrates the **catastrophic forgetting** problem in online learning: the 8 gradient
steps toward manga partially overwrote the pretrained model's knowledge about cross-genre
transitions. The Java click begins to reverse this specialization.

---

### Why loss gradually lowers after continued programming clicks

**Sequence context shifts:**
```
[manga×8, java]          → target: java₂
[manga×7, java, java₂]   → target: java₃
...
```
The transformer can now look back at Java items in the sequence. The attention mechanism attends
to those positions. The intent vector starts incorporating the programming signal.

**Gradient steps accumulate in the new direction.** Each programming click updates the weights
saying "intent built from this mixed manga+programming sequence should point toward programming."
After a few steps, the model has partially adapted — it begins to encode the pattern
"manga reader who recently pivoted to Java → probably wants more Java."

**Loss lowers as model-user alignment is restored.**

---

### The loss curve as a real-time signal

```
5.x  → generalist prior (new user)
↓
0.x  → overspecialized to one niche (high confidence, low diversity)
↑
5.x+ → user surprises the model (largest gradient update of the session fires here)
↓
2-3.x → model adapts to multi-interest state, stabilizes
```

The loss is an implicit **surprise score**: low loss = model has converged on a local pattern and
predicts confidently; high loss = user did something unexpected = the learning signal that drives
fastest adaptation.

**The tradeoff:** fast specialization (low loss, good recommendations within a niche) comes at
the cost of being surprised by cross-genre pivots. The spike on "Java Programming" is not a
failure — it is the model discovering the user has multiple interests, and the large gradient
from that spike is what enables adaptation.

---

## 11. Key Design Clarifications and Common Misconceptions

### α fuses attention matrices, not embedding vectors
α does NOT compute: `fused = α * (512-dim category emb) + (1-α) * (512-dim content emb)`.
α computes: `A_fused = α * A_category + (1-α) * A_content` where both A are `[B, H, T, T]`
attention score matrices. The VALUES in attention are always from the content stream. Category
only shapes the attention pattern, never contributes values.

### category_emb is NOT from BGE-M3
`category_emb = nn.Embedding(num_categories, 512)` is a randomly initialized lookup table
trained from scratch during pretraining on 100k users. Categories are leaf labels parsed from
the `categories` column in `item_metadata.parquet` (e.g., "Books|Manga|Seinen" → "Seinen").

### The reward values (1.0 for click, 5.0 for cart) are currently dead variables
The `reward` field is computed and returned in the HTTP response but is NOT passed into any
training function, NOT used in any loss weighting, and NOT applied to the embedding aggregation.
Both click and cart call `log_click()` identically and trigger the same `train_step()` call with
no reward differentiation.
This is a leftover from an earlier DQN-based design (`sequential_dqn.py`, `rl_filter.py` still
exist in `app/services/`). The reward was never wired into the DIF-SASRec loss function.

### text_profile is NOT L2-normalized before HNSW search
`get_content_candidates()` passes `text_profile` directly to `text_index.search()` without
`faiss.normalize_L2()`. The profile is a weighted mean of unit vectors, not a unit vector.
Its magnitude encodes taste diversity (eclectic reader → lower magnitude).
The content veto dot products are therefore not true cosine similarities either.

### The pretrained .pt snapshot in CPU RAM never changes
`_pretrained_state = copy.deepcopy(self.model.state_dict())` is taken once at agent
initialization and never overwritten. All new users receive exactly the same pretrained
weights. Per-user fine-tuning modifies the agent's live model weights (and saves them to
the user's `.pt` file) but never touches `_pretrained_state`.

### DIF-SASRec is a re-ranker, not a first-stage retriever
It never searches the full 3M catalog. The HNSW index (`bge_index_hnsw.faiss`, 1.7M vectors)
does coarse retrieval using the averaged `text_profile` → 200 candidates. DIF-SASRec then
scores those 200 using the sequential intent vector. Final output: top 10.

### The optimizer state is saved and loaded per user
`agent.save_user()` saves `optimizer_state` in the `.pt` file. `agent.load_user()` restores it.
AdamW's momentum and variance (m and v) are user-specific and persist across sessions.
This means a returning user's model continues fine-tuning with pre-warmed gradient statistics,
not cold-started optimization. This is important for the stability of online learning.

### Each DIFSASRecBlock passes `category` unchanged
Only `content` (which carries the residual) evolves through the 4 blocks. The same `category`
tensor (output of `category_emb`) is fed into all 4 blocks identically. The category stream
provides a static conditioning signal; its influence on each block is mediated by the Q/K
projections and α, not by evolving the category tensor itself.
