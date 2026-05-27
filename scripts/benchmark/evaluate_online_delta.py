"""
scripts/benchmark/evaluate_online_delta.py

Measures the in-session HR@K uplift from one online fine-tuning step (Phase 2).

Experiment design (per user):
  prefix           = train_clicks[:-1]   # history before the simulated in-session click
  in_session_click = train_clicks[-1]    # user clicks this item during the session
  test_target      = test_clicks[0]      # next item to predict

  Cold  : score test_target using pretrained DIF-SASRec(prefix)           [no update]
  Warm  : call train_step(prefix → in_session_click), then
          score test_target using updated DIF-SASRec(prefix + [in_session_click])
  Delta : HR@K_warm - HR@K_cold

Outputs:
  - Mean HR@K cold / warm / delta
  - % of users who improved / degraded / unchanged
  - evaluation/online_delta_result.json  (paste delta into chapter5_holistic.tex)

Usage:
    python scripts/benchmark/evaluate_online_delta.py
    python scripts/benchmark/evaluate_online_delta.py --max-users 2000 --seed 42
    python scripts/benchmark/evaluate_online_delta.py --max-users 10000 --negatives 99
"""
import argparse
import copy
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import numpy as np
import torch
import torch.optim as optim

from app.config import settings
from app.repository.faiss_repo import Retriever
from app.services.category_encoder import CategoryEncoder
from app.services.dif_sasrec import DIFSASRecAgent

DATA_DIR  = settings.DATA_DIR
EVAL_PATH = os.path.join(ROOT, "evaluation", "eval_users.json")
OUT_PATH  = os.path.join(ROOT, "evaluation", "online_delta_result.json")


# ─── Metrics ──────────────────────────────────────────────────────────────────

def hit_at_k(ranked: list, target: str, k: int) -> float:
    return 1.0 if target in ranked[:k] else 0.0


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="In-session HR@K delta evaluation")
    p.add_argument("--max-users",       type=int,   default=5000,
                   help="Users to evaluate (default 5000; use 10000+ for final numbers)")
    p.add_argument("--negatives",       type=int,   default=99,
                   help="Evaluation negatives per user (default 99, same as main eval)")
    p.add_argument("--k",               type=int,   default=10,
                   help="Hit-rate cutoff (default 10)")
    p.add_argument("--seed",            type=int,   default=42)
    p.add_argument("--pretrained-path", type=str,   default=None,
                   help="Path to DIF-SASRec checkpoint (default: data/dif_sasrec_pretrained.pt)")
    p.add_argument("--neg-pool-size",   type=int,   default=200_000,
                   help="Size of the random negative pool (default 200k)")
    p.add_argument("--lr",             type=float, default=1e-5,
                   help="Learning rate for the single online step (default 1e-5). "
                        "The live system uses a warm AdamW (46k steps of accumulated moments) "
                        "which makes the effective step size ~100x smaller than the raw LR. "
                        "lr=1e-5 approximates this warm-optimizer behavior.")
    return p.parse_args()


# ─── Embedding cache ──────────────────────────────────────────────────────────

def build_cache(retriever, eval_users: list, all_asins: list,
                neg_pool_size: int):
    """
    Pre-load into RAM every embedding needed for the experiment:
      - All train + test ASINs across all eval users
      - A shared random negative pool for both evaluation and training negatives

    Returns:
        cache          {asin: np.ndarray[1024]}
        neg_pool_asins list[str]   — filtered to those present in cache
        neg_pool_vecs  np.ndarray  — shape [M, 1024], for fast train_step path
    """
    needed = set()
    for u in eval_users:
        needed.update(u.get("train_clicks", []))
        needed.update(u.get("test_clicks",  []))
    needed = {a for a in needed if a in retriever.asin_to_idx}

    # Negative pool: draw from all ASINs in the FAISS flat index
    raw_neg_pool   = random.sample(all_asins, min(neg_pool_size, len(all_asins)))
    neg_pool_set   = {a for a in raw_neg_pool if a in retriever.asin_to_idx}

    to_load = needed | neg_pool_set
    n       = len(to_load)
    cache   = {}
    t0      = time.time()
    print(f"Pre-loading {n:,} embeddings into RAM ...")
    for i, asin in enumerate(to_load):
        idx          = retriever.asin_to_idx[asin]
        cache[asin]  = retriever.text_flat.reconstruct(idx)
        if (i + 1) % 50_000 == 0 or i + 1 == n:
            pct = (i + 1) / n * 100
            print(f"  {i+1:>7,}/{n:,}  ({pct:.0f}%)  {time.time()-t0:.0f}s", flush=True)

    neg_pool_asins = [a for a in raw_neg_pool if a in cache]
    neg_pool_vecs  = np.array([cache[a] for a in neg_pool_asins], dtype=np.float32)
    print(f"Cache ready: {len(cache):,} ASINs  "
          f"neg pool: {len(neg_pool_asins):,}  "
          f"neg_pool_vecs shape: {neg_pool_vecs.shape}  "
          f"({time.time()-t0:.1f}s)\n")
    return cache, neg_pool_asins, neg_pool_vecs


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    # ── Load infrastructure ───────────────────────────────────────────────────
    print("Loading FAISS retriever ...")
    cleora_data = np.load(os.path.join(DATA_DIR, "cleora_embeddings.npz"))
    retriever   = Retriever(DATA_DIR, cleora_data)
    print(f"  Retriever: {len(retriever.asins):,} ASINs\n")

    cat_encoder    = CategoryEncoder()
    cat_vocab_path = os.path.join(DATA_DIR, "category_vocab.json")
    if os.path.exists(cat_vocab_path):
        cat_encoder.load(cat_vocab_path)
    else:
        cat_encoder.build_from_parquet(os.path.join(DATA_DIR, "item_metadata.parquet"))
    print(f"CategoryEncoder: {cat_encoder.num_categories} categories\n")

    pretrained_path = (args.pretrained_path
                       or os.path.join(DATA_DIR, "dif_sasrec_pretrained.pt"))
    if not os.path.exists(pretrained_path):
        print(f"ERROR: checkpoint not found at {pretrained_path}")
        sys.exit(1)

    print(f"Loading DIF-SASRec from {pretrained_path} ...")
    agent = DIFSASRecAgent(retriever, cat_encoder, pretrained_path)
    print(f"  Agent ready  step={agent._step}\n")

    # ── Load eval users ───────────────────────────────────────────────────────
    if not os.path.exists(EVAL_PATH):
        print(f"ERROR: {EVAL_PATH} not found. Run scripts/setup_dif_sasrec.py first.")
        sys.exit(1)

    with open(EVAL_PATH) as f:
        eval_users = json.load(f)

    if args.max_users:
        eval_users = eval_users[:args.max_users]
    print(f"Eval users: {len(eval_users):,}  (seed={args.seed})\n")

    all_asins = list(retriever.asin_to_idx.keys())

    # ── Pre-cache embeddings ──────────────────────────────────────────────────
    cache, neg_pool_asins, neg_pool_vecs = build_cache(
        retriever, eval_users, all_asins, args.neg_pool_size
    )

    # Inject cache into agent so _get_asin_vec is served from RAM
    agent.set_embedding_cache(cache)

    # ── Snapshot pretrained model weights for per-user reset ─────────────────
    # We intentionally do NOT restore optimizer state between users.
    # Reason: (1) the pretrained AdamW has 46k steps of accumulated moments
    # which would suppress the gradient update and understate the delta;
    # (2) restoring saved optimizer state causes shape-mismatch errors in
    # PyTorch's _multi_tensor_adam when parameter ordering differs between
    # the training run and inference.  A fresh optimizer per user gives a
    # clean, unbiased single-step gradient update — exactly what we want.
    pretrained_state = copy.deepcopy(agent.model.state_dict())

    def reset_to_pretrained():
        agent.model.load_state_dict(pretrained_state)
        agent.optimizer = optim.AdamW(
            agent.model.parameters(),
            lr=args.lr,
            weight_decay=settings.SASREC_WEIGHT_DECAY,
        )
        agent._step = 0
        agent.model.eval()

    # Initialise clean optimizer before the first user (same as between-user reset)
    reset_to_pretrained()

    # ── Evaluate ──────────────────────────────────────────────────────────────
    cold_hits: list[float] = []
    warm_hits: list[float] = []
    deltas:    list[float] = []
    skipped = 0
    t0      = time.time()

    print("-" * 68)
    print(f"  Running delta evaluation  "
          f"negatives={args.negatives}  k={args.k}  users={len(eval_users):,}")
    print("-" * 68)

    for i, user in enumerate(eval_users):
        train = user.get("train_clicks", [])
        test  = user.get("test_clicks",  [])

        # Need ≥2 train clicks: [prefix..., in_session_click] + test target
        if len(train) < 2 or not test:
            skipped += 1
            continue

        prefix           = train[:-1]          # context before the simulated in-session click
        in_session_click = train[-1]           # what the user "clicks" during the session
        test_target      = test[0]             # the next item we're trying to predict

        # Both the in-session click and the test target must be in the embedding cache
        # (cache covers all ASINs in the FAISS flat index; non-indexed ASINs can't be scored)
        if test_target not in cache or in_session_click not in cache:
            skipped += 1
            continue

        # ── Evaluation candidate pool: test_target + n_neg random negatives ──
        seen = set(train) | {test_target}
        negs = [a for a in random.sample(neg_pool_asins,
                                         min(args.negatives * 3, len(neg_pool_asins)))
                if a not in seen][:args.negatives]
        if len(negs) < args.negatives // 2:
            skipped += 1
            continue

        candidates = [test_target] + negs

        # ── Cold pass: pretrained weights, prefix only ────────────────────────
        prefix_cats = cat_encoder.encode_sequence(prefix)
        cold_scores = agent.get_candidate_scores(prefix, prefix_cats, candidates)
        cold_ranked = sorted(candidates, key=lambda a: cold_scores.get(a, 0.0), reverse=True)
        cold_hit    = hit_at_k(cold_ranked, test_target, args.k)

        # ── One online training step: prefix → in_session_click ──────────────
        # train_step modifies agent.model weights in-place.
        # neg_pool_vecs enables the fast path (no per-step FAISS reads for negatives).
        target_cat = cat_encoder.get_category_id(in_session_click)
        agent.train_step(
            prefix,
            in_session_click,
            target_cat,
            neg_pool_asins,
            neg_pool_vecs,     # fast path: sample from pre-loaded numpy array
        )

        # ── Warm pass: updated weights, prefix + in_session_click ────────────
        warm_seq    = prefix + [in_session_click]
        warm_cats   = cat_encoder.encode_sequence(warm_seq)
        warm_scores = agent.get_candidate_scores(warm_seq, warm_cats, candidates)
        warm_ranked = sorted(candidates, key=lambda a: warm_scores.get(a, 0.0), reverse=True)
        warm_hit    = hit_at_k(warm_ranked, test_target, args.k)

        cold_hits.append(cold_hit)
        warm_hits.append(warm_hit)
        deltas.append(warm_hit - cold_hit)

        # ── Reset model to pretrained baseline for next user ──────────────────
        # Must happen after each user — train_step modifies weights in-place and
        # we never want one user's gradient step to influence the next user's cold pass.
        reset_to_pretrained()

        if (i + 1) % 500 == 0 or i + 1 == len(eval_users):
            n_done   = len(deltas) or 1
            elapsed  = time.time() - t0
            est_total = elapsed / (i + 1) * len(eval_users)
            print(f"  [{i+1:>5,}/{len(eval_users):,}]  "
                  f"cold HR@{args.k}={sum(cold_hits)/n_done:.4f}  "
                  f"warm HR@{args.k}={sum(warm_hits)/n_done:.4f}  "
                  f"delta={sum(deltas)/n_done:+.4f}  "
                  f"{elapsed:.0f}s / ~{est_total:.0f}s total")

    # ── Final results ─────────────────────────────────────────────────────────
    n = len(deltas) or 1
    mean_cold    = sum(cold_hits) / n
    mean_warm    = sum(warm_hits) / n
    mean_delta   = sum(deltas)    / n
    pct_improved = sum(1 for d in deltas if d > 0) / n * 100
    pct_degraded = sum(1 for d in deltas if d < 0) / n * 100
    pct_same     = 100 - pct_improved - pct_degraded
    elapsed      = time.time() - t0

    print()
    print("=" * 68)
    print(f"  In-Session Online Fine-Tuning: Delta Evaluation")
    print(f"  Users evaluated : {n:,}   skipped: {skipped:,}")
    print(f"  Negatives/user  : {args.negatives}   k={args.k}   seed={args.seed}")
    print()
    print(f"  HR@{args.k} cold  (pretrained, prefix only)       : {mean_cold:.4f}")
    print(f"  HR@{args.k} warm  (1 grad step, prefix + click)   : {mean_warm:.4f}")
    print(f"  Delta  (warm - cold)                              : {mean_delta:+.4f}")
    print()
    print(f"  Direction breakdown:")
    print(f"    Improved  : {pct_improved:5.1f}% of users")
    print(f"    No change : {pct_same:5.1f}% of users")
    print(f"    Degraded  : {pct_degraded:5.1f}% of users")
    print(f"  Elapsed: {elapsed:.1f}s")
    print("=" * 68)
    print()

    # ── LaTeX-ready insert ────────────────────────────────────────────────────
    sign = "+" if mean_delta >= 0 else ""
    print("LaTeX insert for chapter5_holistic.tex line ~41:")
    print()
    print(f'  Replace [DELTA\\_RESULT] with:')
    print(f'  "{sign}{mean_delta*100:.2f}~pp"')
    print()
    print(f'  Full sentence example:')
    print(f'  "...yielding an in-session HR@10 delta of {sign}{mean_delta*100:.2f}~pp')
    print(f'  (HR@10: {mean_cold:.4f} \\to {mean_warm:.4f}, {n:,} users)..."')
    print()

    # ── Save JSON result ──────────────────────────────────────────────────────
    result = {
        "experiment":    "in_session_online_delta",
        "n_users":       n,
        "skipped":       skipped,
        "negatives":     args.negatives,
        "k":             args.k,
        "seed":          args.seed,
        "pretrained_path": pretrained_path,
        "hr_k_cold":     round(mean_cold,  4),
        "hr_k_warm":     round(mean_warm,  4),
        "delta":         round(mean_delta, 4),
        "delta_pp":      round(mean_delta * 100, 2),
        "pct_improved":  round(pct_improved, 1),
        "pct_degraded":  round(pct_degraded, 1),
        "pct_same":      round(pct_same,     1),
        "elapsed_s":     round(elapsed, 1),
        "latex_insert":  f"{sign}{mean_delta*100:.2f}~pp",
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Result saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
