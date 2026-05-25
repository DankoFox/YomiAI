"""
scripts/train_sasrec_content.py — Train a pure content-based SASRec from scratch.

Architecture: DIFSASRecModel(content_only=True)
  - No category embedding, no category attention stream, no auxiliary loss.
  - Only BGE-M3 content embeddings + causal self-attention (standard SASRec).

Purpose: produces a defensible external-comparison row in the benchmark table.
  A committee member can legitimately compare this against DIF-SASRec because:
  - Trained from scratch (no shared weights with DIF-SASRec)
  - Same BGE-M3 embeddings, same data, same training protocol
  - Same sampled-softmax evaluation protocol

Output: data/sasrec_content_pretrained.pt  (arch="sasrec_content_v1")

Usage:
    python scripts/train_sasrec_content.py               # 30 epochs
    python scripts/train_sasrec_content.py --epochs 5    # quick smoke test
    python scripts/train_sasrec_content.py --batch-size 1024  # if VRAM is tight
"""
import argparse
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np

from app.config import settings
from app.repository.faiss_repo import Retriever
from app.services.category_encoder import CategoryEncoder
from app.services.dif_sasrec import DIFSASRecAgent

DATA_DIR           = settings.DATA_DIR
CAT_VOCAB_PATH     = os.path.join(DATA_DIR, "category_vocab.json")
EVAL_PATH          = os.path.join(ROOT, "evaluation", "eval_users.json")
OUTPUT_PATH        = os.path.join(DATA_DIR, "sasrec_content_pretrained.pt")
CLEORA_PATH        = os.path.join(DATA_DIR, "cleora_embeddings.npz")


def parse_args():
    p = argparse.ArgumentParser(
        description="Train content-only SASRec from scratch (no category stream)"
    )
    p.add_argument("--epochs",       type=int, default=30)
    p.add_argument("--min-clicks",   type=int, default=6)
    p.add_argument("--batch-size",   type=int, default=2048)
    p.add_argument("--output",       type=str, default=OUTPUT_PATH)
    p.add_argument("--resume-from",  type=str, default=None,
                   help="Resume from a checkpoint (e.g. sasrec_content_pretrained_epoch5.pt)")
    p.add_argument("--start-epoch",  type=int, default=1,
                   help="Epoch to start from when resuming (e.g. 6 after epoch-5 checkpoint)")
    p.add_argument("--log-file",     type=str, default=None,
                   help="Tee all output to this file in addition to stdout")
    return p.parse_args()


class _Tee:
    """Write to multiple streams simultaneously, flushing each immediately."""
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()
    def flush(self):
        for s in self.streams:
            s.flush()
    def reconfigure(self, **kwargs):
        pass  # satisfy callers that check for this method


def main():
    args = parse_args()

    log_fh = None
    if args.log_file:
        os.makedirs(os.path.dirname(os.path.abspath(args.log_file)), exist_ok=True)
        log_fh = open(args.log_file, "a", buffering=1, encoding="utf-8")
        sys.stdout = _Tee(sys.__stdout__, log_fh)
        sys.stderr = _Tee(sys.__stderr__, log_fh)
    else:
        sys.stdout.reconfigure(line_buffering=True)

    print("\nSASRec Content-Only Training")
    print(f"  Data dir:    {DATA_DIR}")
    print(f"  Eval users:  {EVAL_PATH}")
    print(f"  Vocab:       {CAT_VOCAB_PATH}")
    print(f"  Output:      {args.output}")
    print(f"  Epochs:      {args.epochs}  |  batch={args.batch_size}  |  min_clicks={args.min_clicks}")

    # ── Prerequisites check ──────────────────────────────────────────────────
    for path, label in [(EVAL_PATH, "eval_users.json"),
                        (CAT_VOCAB_PATH, "category_vocab.json"),
                        (CLEORA_PATH, "cleora_embeddings.npz")]:
        if not os.path.exists(path):
            print(f"\nERROR: {label} not found at {path}")
            print("       Run scripts/setup_dif_sasrec.py first.")
            sys.exit(1)

    # ── Load infrastructure ──────────────────────────────────────────────────
    print("\nLoading infrastructure ...")
    cleora_data = np.load(CLEORA_PATH)
    retriever   = Retriever(DATA_DIR, cleora_data)
    print(f"  Retriever ready — {len(retriever.asins):,} ASINs")

    cat_encoder = CategoryEncoder()
    cat_encoder.load(CAT_VOCAB_PATH)
    print(f"  Category vocab: {cat_encoder.num_categories} categories")

    # ── Load eval users ──────────────────────────────────────────────────────
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        eval_users = json.load(f)

    eligible = [u for u in eval_users
                if len(u.get("train_clicks", [])) >= args.min_clicks]
    print(f"  Users: {len(eval_users):,} total, {len(eligible):,} eligible")

    # ── Pre-cache embeddings into RAM ────────────────────────────────────────
    print("\nPre-loading embeddings into RAM ...")
    t0 = time.time()
    unique_asins = [a for a in {a for u in eligible for a in u["train_clicks"]}
                    if a in retriever.asin_to_idx]

    emb_cache: dict = {}
    n = len(unique_asins)
    for i, asin in enumerate(unique_asins):
        idx = retriever.asin_to_idx[asin]
        emb_cache[asin] = retriever.text_flat.reconstruct(idx)
        if (i + 1) % 50_000 == 0 or i + 1 == n:
            print(f"  {i+1:>7,}/{n:,}  ({(i+1)/n*100:.0f}%)  {time.time()-t0:.0f}s", end="\r")

    print(f"\n  Cached {len(emb_cache):,} ASINs  "
          f"({len(emb_cache)*1024*4/1e6:.0f} MB)  in {time.time()-t0:.0f}s")

    NEG_POOL_SIZE    = min(50_000, len(emb_cache))
    all_cache_asins  = list(emb_cache.keys())

    # ── Build training examples ──────────────────────────────────────────────
    print("\nBuilding training examples ...")
    all_examples = []
    for user in eligible:
        tc = user.get("train_clicks", [])
        for t in range(2, len(tc)):
            all_examples.append((
                tc[:t],
                tc[t],
                cat_encoder.get_category_id(tc[t]),
            ))
    print(f"  {len(all_examples):,} (seq, target, cat) examples")

    # ── Instantiate content-only agent ───────────────────────────────────────
    agent = DIFSASRecAgent(retriever, cat_encoder, content_only=True)
    agent.set_embedding_cache(emb_cache)
    param_count = sum(p.numel() for p in agent.model.parameters())
    print(f"\n  Model: content_only=True  |  {param_count:,} params  |  device={agent.device}")

    if args.resume_from:
        if not os.path.exists(args.resume_from):
            print(f"ERROR: --resume-from path not found: {args.resume_from}")
            sys.exit(1)
        agent.load(args.resume_from)
        print(f"  Resumed from {args.resume_from} (step={agent._step})")

    BATCH_SIZE = args.batch_size
    n_batches  = (len(all_examples) + BATCH_SIZE - 1) // BATCH_SIZE
    LOG_EVERY  = max(1, n_batches // 10)

    remaining_epochs = args.epochs - args.start_epoch + 1
    total_steps  = n_batches * remaining_epochs + agent._step
    warmup_steps = n_batches * settings.SASREC_WARMUP_EPOCHS
    agent.configure_scheduler(total_steps, warmup_steps)
    # Fast-forward scheduler to match already-completed steps
    if agent._step > 0:
        for _ in range(agent._step):
            agent.scheduler.step()

    t_start = time.time()
    print(f"\n  Training epochs {args.start_epoch}-{args.epochs}  |  batches/epoch={n_batches:,}  "
          f"AMP={'on' if agent._amp_enabled else 'off'}\n")
    print(f"  {'Epoch':>5}  {'Batch':>8}  {'Avg Loss':>10}  {'LR':>10}  {'Elapsed':>9}")
    print("  " + "-" * 50)

    for epoch in range(args.start_epoch, args.epochs + 1):
        random.shuffle(all_examples)

        neg_pool_asins = random.sample(all_cache_asins, NEG_POOL_SIZE)
        neg_pool_vecs  = np.array([emb_cache[a] for a in neg_pool_asins], dtype=np.float32)

        total_loss     = 0.0
        n_batches_done = 0
        t_epoch        = time.time()

        for b_start in range(0, len(all_examples), BATCH_SIZE):
            batch    = all_examples[b_start : b_start + BATCH_SIZE]
            seqs     = [e[0] for e in batch]
            targets  = [e[1] for e in batch]
            cat_ids  = [e[2] for e in batch]

            loss = agent.train_step_batch(seqs, targets, cat_ids, neg_pool_vecs)
            if loss is not None:
                total_loss     += loss
                n_batches_done += 1

            if n_batches_done > 0 and n_batches_done % LOG_EVERY == 0:
                avg    = total_loss / n_batches_done
                pct    = b_start / len(all_examples) * 100
                cur_lr = agent.optimizer.param_groups[0]["lr"]
                print(f"  {epoch:>5}  {n_batches_done:>5,}/{n_batches:,} "
                      f"({pct:4.0f}%)  {avg:>10.4f}  {cur_lr:>10.2e}  "
                      f"{time.time()-t_epoch:>7.0f}s")

        avg     = total_loss / max(n_batches_done, 1)
        cur_lr  = agent.optimizer.param_groups[0]["lr"]
        elapsed = time.time() - t_start
        print(f"  Epoch {epoch:>2} done  avg_loss={avg:.4f}  lr={cur_lr:.2e}  "
              f"epoch_time={time.time()-t_epoch:.0f}s  total={elapsed:.0f}s")

        if epoch % 5 == 0:
            ckpt = args.output.replace(".pt", f"_epoch{epoch}.pt")
            agent.save(ckpt)
            print(f"  [checkpoint] -> {ckpt}")

    agent.save(args.output)
    print(f"\nDone in {time.time()-t_start:.0f}s -> {args.output}")
    print("Next: python scripts/benchmark/evaluate_recommendation.py")


if __name__ == "__main__":
    main()
