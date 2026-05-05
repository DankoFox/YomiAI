import argparse
import os

import numpy as np
from pycleora import SparseMatrix

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"
)


def _iter_hyperedges(base_path: str, augment_path: str | None, augment_weight: int):
    """
    Yield hyperedge lines: base file first, then delta lines repeated augment_weight times.

    Repeating the delta block N times gives recent interactions N× the influence
    of any single historical user in the Markov propagation.
    """
    with open(base_path, "r", encoding="utf-8") as f:
        yield from f

    if augment_path and os.path.exists(augment_path):
        with open(augment_path, "r", encoding="utf-8") as f:
            delta = [line for line in f if line.strip()]
        print(f"Augmenting: {len(delta)} delta hyperedges × {augment_weight} ...")
        for _ in range(augment_weight):
            yield from delta


def run_cleora(augment_path: str | None = None, augment_weight: int = 10):
    hyperedge_path = os.path.join(_DATA_DIR, "hyperedges_cleora.txt")
    if not os.path.exists(hyperedge_path):
        print(f"Error: {hyperedge_path} not found.")
        return

    print(f"Loading hyperedges from {hyperedge_path} ...")
    mat = SparseMatrix.from_iterator(
        _iter_hyperedges(hyperedge_path, augment_path, augment_weight),
        columns="complex::reflexive::product",
    )
    print(f"Entities found: {len(mat.entity_ids)}")

    DIM = 1024
    print(f"Initializing {DIM}-dim embeddings ...")
    embeddings = mat.initialize_deterministically(DIM)

    NUM_WALKS = 8
    print(f"Running {NUM_WALKS} Markov propagation walks ...")
    for i in range(NUM_WALKS):
        print(f"  Walk {i + 1}/{NUM_WALKS} ...")
        embeddings = mat.left_markov_propagate(embeddings)
        embeddings /= np.linalg.norm(embeddings, axis=-1, keepdims=True)

    output_path = os.path.join(_DATA_DIR, "cleora_embeddings.npz")
    np.savez(output_path, asins=mat.entity_ids, embeddings=embeddings)
    print(f"Saved embeddings for {len(mat.entity_ids)} items -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Cleora behavioral embeddings.")
    parser.add_argument(
        "--augment",
        metavar="PATH",
        help="Delta hyperedge file produced by scripts/export_delta_hyperedges.py",
    )
    parser.add_argument(
        "--augment-weight",
        type=int,
        default=10,
        metavar="N",
        help="Repeat delta rows N× for recency up-weighting (default: 10)",
    )
    args = parser.parse_args()
    run_cleora(augment_path=args.augment, augment_weight=args.augment_weight)
