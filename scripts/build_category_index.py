"""
scripts/build_category_index.py — Build a category → ASIN lookup index.

Reads every ASIN from item_metadata.parquet, maps it to a category_id via
CategoryEncoder, and groups those that exist in the FAISS retriever
(retriever.asin_to_idx) into a dict:

    {cat_id (str): [asin, asin, ...]}

Output: data/category_asins.json

Used by: scripts/benchmark/evaluate_recommendation.py --hard-negatives
"""
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd

from app.config import settings
from app.repository.faiss_repo import Retriever
from app.services.category_encoder import CategoryEncoder

DATA_DIR       = settings.DATA_DIR
METADATA_PATH  = os.path.join(DATA_DIR, "item_metadata.parquet")
CAT_VOCAB_PATH = os.path.join(DATA_DIR, "category_vocab.json")
CLEORA_PATH    = os.path.join(DATA_DIR, "cleora_embeddings.npz")
OUTPUT_PATH    = os.path.join(DATA_DIR, "category_asins.json")


def main():
    # ── Prerequisites ────────────────────────────────────────────────────────
    for path, label in [
        (METADATA_PATH,  "item_metadata.parquet"),
        (CAT_VOCAB_PATH, "category_vocab.json"),
        (CLEORA_PATH,    "cleora_embeddings.npz"),
    ]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found at {path}")
            sys.exit(1)

    # ── Load retriever (asin_to_idx is the ground truth of valid ASINs) ──────
    print("Loading retriever ...")
    cleora_data = np.load(CLEORA_PATH)
    retriever   = Retriever(DATA_DIR, cleora_data)
    valid_asins = retriever.asin_to_idx
    print(f"  {len(valid_asins):,} ASINs in retriever index")

    # ── Load category encoder ─────────────────────────────────────────────────
    print("Loading category encoder ...")
    cat_encoder = CategoryEncoder()
    cat_encoder.load(CAT_VOCAB_PATH)
    print(f"  {cat_encoder.num_categories} categories (incl. PAD + UNK)")

    # ── Load metadata to enumerate ASINs ─────────────────────────────────────
    print("Loading item_metadata.parquet ...")
    df = pd.read_parquet(METADATA_PATH, columns=["parent_asin"])
    all_meta_asins = df["parent_asin"].astype(str).unique()
    print(f"  {len(all_meta_asins):,} unique ASINs in metadata")

    # ── Build index ──────────────────────────────────────────────────────────
    print("Building category index ...")
    cat_index: dict[int, list] = defaultdict(list)
    skipped_no_vector = 0
    skipped_unk       = 0

    for asin in all_meta_asins:
        if asin not in valid_asins:
            skipped_no_vector += 1
            continue
        cat_id = cat_encoder.get_category_id(asin)
        if cat_id == CategoryEncoder.UNK_ID:
            skipped_unk += 1
            continue
        cat_index[cat_id].append(asin)

    print(f"  Skipped (no FAISS vector): {skipped_no_vector:,}")
    print(f"  Skipped (UNK category):    {skipped_unk:,}")

    # ── Write output ─────────────────────────────────────────────────────────
    print(f"Writing {OUTPUT_PATH} ...")
    output = {str(cat_id): asins for cat_id, asins in cat_index.items()}
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"  Written: {os.path.getsize(OUTPUT_PATH) / 1024 / 1024:.1f} MB")

    # ── Summary ──────────────────────────────────────────────────────────────
    counts = [len(v) for v in cat_index.values()]
    total_indexed = sum(counts)

    print("\n-- Category Index Summary ------------------------------------------")
    print(f"  Total categories:  {len(cat_index):,}")
    print(f"  Total ASINs indexed: {total_indexed:,}")
    print(f"  Items per category — mean: {total_indexed / len(counts):.0f} "
          f"| min: {min(counts):,} | max: {max(counts):,}")

    top5 = sorted(cat_index.items(), key=lambda kv: len(kv[1]), reverse=True)[:5]
    print("\n  Top 5 categories by size:")
    for cat_id, asins in top5:
        name = cat_encoder.get_category_name(cat_id)
        print(f"    [{cat_id:4d}] {name:<40s}  {len(asins):,} items")


if __name__ == "__main__":
    main()
