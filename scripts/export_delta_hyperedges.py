"""
Export delta hyperedges from MongoDB interactions since the last run.

For each authenticated user, their click + cart interactions are grouped
into one hyperedge row (deduplicated ASINs). The output file is passed to
run_cleora.py --augment to augment the base co-purchase graph.

Usage
-----
    python scripts/export_delta_hyperedges.py
    python scripts/export_delta_hyperedges.py --since 2026-01-01T00:00:00
    python scripts/export_delta_hyperedges.py --out data/my_delta.txt

Workflow
--------
    1. python scripts/export_delta_hyperedges.py
    2. python scripts/data/run_cleora.py --augment data/delta_hyperedges.txt
    3. Restart the API (or hot-reload) to pick up the new cleora_embeddings.npz
"""
import argparse
import asyncio
import os
from datetime import datetime, timedelta

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "data"))
MONGO_URL   = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME     = "nba_logs"

LAST_RUN_FILE = os.path.join(DATA_DIR, "delta_last_run.txt")


def _load_last_run() -> datetime:
    """Return the timestamp of the previous export, defaulting to 7 days ago."""
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE) as f:
            return datetime.fromisoformat(f.read().strip())
    return datetime.now() - timedelta(days=7)


def _save_last_run(dt: datetime):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(dt.isoformat())


def _load_valid_asins() -> set[str]:
    """Load the catalog ASIN whitelist used by filter_hyperedges.py."""
    asins_path = os.path.join(DATA_DIR, "asins.csv")
    if not os.path.exists(asins_path):
        print("Warning: asins.csv not found — delta will not be filtered to catalog.")
        return set()
    valid = set(pd.read_csv(asins_path, header=None)[0].astype(str))
    print(f"Loaded {len(valid):,} catalog ASINs from asins.csv.")
    return valid


async def export_delta(since: datetime, out_path: str) -> int:
    valid_asins = _load_valid_asins()

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print(f"Querying interactions since {since.isoformat()} ...")
    cursor = db["interactions"].find({
        "action":    {"$in": ["click", "cart"]},
        "timestamp": {"$gt": since.isoformat()},
        "is_guest":  {"$ne": True},           # skip anonymous sessions
    })

    user_items: dict[str, set[str]] = {}
    total = 0
    async for doc in cursor:
        uid  = doc.get("user_id")
        asin = doc.get("asin")
        if not uid or not asin:
            continue
        if valid_asins and asin not in valid_asins:
            continue                           # filter to catalog, same as filter_hyperedges.py
        user_items.setdefault(uid, set()).add(asin)
        total += 1

    client.close()
    print(f"Found {total} valid interactions from {len(user_items)} users.")

    if not user_items:
        print("No new interactions — delta file not written.")
        return 0

    with open(out_path, "w", encoding="utf-8") as f:
        for asins in user_items.values():
            f.write(" ".join(asins) + "\n")

    print(f"Wrote {len(user_items)} hyperedge lines -> {out_path}")
    return len(user_items)


async def main():
    parser = argparse.ArgumentParser(
        description="Export delta hyperedges from MongoDB for Cleora augmentation."
    )
    parser.add_argument(
        "--since",
        help="ISO datetime lower bound (default: timestamp of last run, or 7 days ago)",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(DATA_DIR, "delta_hyperedges.txt"),
        help="Output hyperedge file (default: data/delta_hyperedges.txt)",
    )
    args = parser.parse_args()

    since     = datetime.fromisoformat(args.since) if args.since else _load_last_run()
    run_start = datetime.now()

    written = await export_delta(since, args.out)
    if written:
        _save_last_run(run_start)
        print(f"Last-run timestamp saved -> {run_start.isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
