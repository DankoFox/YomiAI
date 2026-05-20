"""GET /recommend and GET /rl_metrics."""
import random

from fastapi import APIRouter, Depends

from app.api.dependencies import require_ready
from app.config import settings
from app.core.container import AppContainer
from app.infrastructure.database import db

router = APIRouter()

COLD_START_THRESHOLD = settings.COLD_START_THRESHOLD


@router.get("/recommend")
async def recommend(user_id: str, container: AppContainer = Depends(require_ready)):
    """
    Mode 2: 3-Layer NBA Funnel.
    Cold-start users receive random catalogue items.
    Warm users go through Cleora → Veto → DIF-SASRec.
    """
    retriever        = container.retriever
    profile_manager  = container.profile_manager
    recommend_engine = container.recommend_engine

    profile = await profile_manager.get_profile(user_id)

    if len(profile.clicks) < COLD_START_THRESHOLD:
        rec_dict, mode = _cold_start(retriever)
    else:
        async with container.agent_pool.borrow() as agent:
            agent.load_user(user_id, settings.DATA_DIR)
            res = await recommend_engine.recommend_for_user(user_id, agent, top_k=10)
        if res is None:
            rec_dict, mode = _cold_start(retriever)
        else:
            rec_dict, mode = res, "personalized"

    # Fetch per-user blocked set from Redis and filter before enrichment
    blocked: set[str] = set()
    try:
        if db.redis:
            raw = await db.redis.smembers(f"user:{user_id}:blocked")
            blocked = {m.decode() if isinstance(m, bytes) else m for m in (raw or [])}
    except Exception:
        pass

    if blocked:
        rec_dict["people_also_buy"] = [r for r in rec_dict["people_also_buy"] if r[0] not in blocked]
        rec_dict["you_might_like"]  = [r for r in rec_dict["you_might_like"]  if r[0] not in blocked]
        rec_dict["combined"]        = [r for r in rec_dict.get("combined", []) if r[0] not in blocked]

    all_rec_ids = (
        [rec[0] for rec in rec_dict["people_also_buy"]]
        + [rec[0] for rec in rec_dict["you_might_like"]]
    )
    await profile_manager.log_recommendation(user_id, all_rec_ids)

    meta_repo = container.metadata_repo

    def enrich_list(recs):
        enriched = []
        for rec in recs:
            asin, score, layer = rec[0], rec[1], rec[2]
            extras = rec[3] if len(rec) > 3 else {}
            if meta_repo.df is not None and len(meta_repo.df) > 0 and asin not in meta_repo.df.index:
                continue
            details          = meta_repo.get_item(asin)
            details["score"] = float(score)
            details["layer"] = layer
            details.update(extras)
            enriched.append(details)
        return enriched

    return {
        "people_also_buy": enrich_list(rec_dict["people_also_buy"]),
        "you_might_like":  enrich_list(rec_dict["you_might_like"]),
        "combined":        enrich_list(rec_dict.get("combined", [])),
        "user_id":         user_id,
        "mode":            mode,
    }


def _cold_start(retriever):
    pool   = [a for a in retriever.cleora_asins if a in retriever.asin_to_idx]
    sample = random.sample(pool, min(20, len(pool)))
    pab    = [(a, 1.0, "Discovery") for a in sample[:10]]
    yml    = [(a, 1.0, "Discovery") for a in sample[10:]]
    rec_dict = {
        "people_also_buy": pab,
        "you_might_like":  yml,
        "combined":        pab + yml,
    }
    return rec_dict, "cold_start"


@router.get("/rl_metrics")
async def rl_metrics(user_id: str, container: AppContainer = Depends(require_ready)):
    """Return real-time DIF-SASRec model metrics."""
    async with container.agent_pool.borrow() as agent:
        agent.load_user(user_id, settings.DATA_DIR)
        return {
            "user_id":      user_id,
            "loss_history": list(agent.loss_history),
            "step":         agent._step,
            "arch":         "DIF-SASRec",
        }
