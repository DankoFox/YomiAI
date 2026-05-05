"""
Smoke-test for the Cleora delta-refit pipeline — no UI clicks required.

Steps:
  1. Pull a handful of real ASINs from data/asins.csv (or accept --asins CLI arg).
  2. Insert fake click interactions into MongoDB for a synthetic test user.
  3. Reset delta_last_run.txt so the export picks them up.
  4. Run export_delta_hyperedges.py  →  run_cleora.py --augment.
  5. Print pass/fail and clean up test documents.

Usage
-----
    python scripts/test_refit_pipeline.py
    python scripts/test_refit_pipeline.py --asins B001 B002 B003
    python scripts/test_refit_pipeline.py --keep   # skip cleanup (inspect results)
"""
import argparse
import asyncio
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient

_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, ".."))
DATA_DIR      = os.path.join(_PROJECT_ROOT, "data")

MONGO_URL        = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME          = "nba_logs"
TEST_USER_ID     = "__test_refit_smoke__"
LAST_RUN_FILE    = os.path.join(DATA_DIR, "delta_last_run.txt")
DELTA_PATH       = os.path.join(DATA_DIR, "delta_hyperedges.txt")
EXPORT_SCRIPT    = os.path.join(_SCRIPT_DIR, "export_delta_hyperedges.py")
CLEORA_SCRIPT    = os.path.join(_SCRIPT_DIR, "data", "run_cleora.py")


def _pick_asins(n: int = 10) -> list[str]:
    asins_path = os.path.join(DATA_DIR, "asins.csv")
    if not os.path.exists(asins_path):
        raise FileNotFoundError(f"asins.csv not found at {asins_path}")
    df = pd.read_csv(asins_path, header=None)
    return df[0].astype(str).dropna().sample(n=n, random_state=42).tolist()


async def _insert_interactions(asins: list[str]) -> list:
    client = AsyncIOMotorClient(MONGO_URL)
    coll   = client[DB_NAME]["interactions"]
    now    = datetime.now(timezone.utc)
    docs   = [
        {
            "user_id":   TEST_USER_ID,
            "asin":      asin,
            "action":    "click",
            "timestamp": (now - timedelta(seconds=i)).isoformat(),
            "is_guest":  False,
            "_test":     True,
        }
        for i, asin in enumerate(asins)
    ]
    result = await coll.insert_many(docs)
    client.close()
    return result.inserted_ids


async def _cleanup(ids: list):
    client = AsyncIOMotorClient(MONGO_URL)
    coll   = client[DB_NAME]["interactions"]
    await coll.delete_many({"_id": {"$in": ids}})
    client.close()


def _reset_last_run():
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with open(LAST_RUN_FILE, "w") as f:
        f.write(past)
    print(f"[setup] Reset delta_last_run.txt → {past}")


def _run(label: str, cmd: list[str]) -> bool:
    print(f"\n{'='*60}")
    print(f"[{label}] {' '.join(cmd)}")
    print('='*60)
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = result.stdout.decode("utf-8", errors="replace").strip()
    print(output)
    ok = result.returncode == 0
    print(f"\n[{label}] {'PASSED' if ok else 'FAILED'} (exit {result.returncode})")
    return ok


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asins", nargs="+", help="ASINs to use (default: 10 random from asins.csv)")
    parser.add_argument("--keep",  action="store_true", help="Skip cleanup of test MongoDB docs")
    args = parser.parse_args()

    asins = args.asins or _pick_asins(10)
    print(f"[setup] Using {len(asins)} ASINs: {asins[:5]}{'...' if len(asins) > 5 else ''}")

    print("[setup] Inserting fake interactions into MongoDB ...")
    inserted_ids = await _insert_interactions(asins)
    print(f"[setup] Inserted {len(inserted_ids)} documents (user={TEST_USER_ID})")

    _reset_last_run()

    ok1 = _run("export", [sys.executable, EXPORT_SCRIPT])
    if not ok1:
        print("\n[ABORT] Delta export failed — skipping Cleora step.")
    else:
        if not os.path.exists(DELTA_PATH):
            print(f"\n[ABORT] {DELTA_PATH} not created — nothing to refit.")
            ok1 = False
        else:
            ok2 = _run("cleora", [sys.executable, CLEORA_SCRIPT, "--augment", DELTA_PATH])
            print(f"\n{'[PASS]' if ok2 else '[FAIL]'} Full refit pipeline {'succeeded' if ok2 else 'FAILED'}.")

    if not args.keep:
        print("\n[cleanup] Removing test documents from MongoDB ...")
        await _cleanup(inserted_ids)
        print("[cleanup] Done.")
    else:
        print(f"\n[keep] Left {len(inserted_ids)} test docs in MongoDB (user={TEST_USER_ID}).")


if __name__ == "__main__":
    asyncio.run(main())
