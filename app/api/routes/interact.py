"""POST /interact — log user click/not_interested, train DIF-SASRec."""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.dependencies import require_ready
from app.api.schemas import InteractRequest
from app.config import settings
from app.core.container import AppContainer
from app.infrastructure.database import db

router = APIRouter()
log    = logging.getLogger("nba_api")

BLOCKED_KEY = "user:{user_id}:blocked"


@router.post("/interact")
async def interact(req: InteractRequest,
                   container: AppContainer = Depends(require_ready)):
    profile_manager  = container.profile_manager
    recommend_engine = container.recommend_engine

    if req.action == "not_interested":
        # Add item to per-user Redis blacklist so it won't appear in future recs
        try:
            if db.redis:
                key = BLOCKED_KEY.format(user_id=req.user_id)
                await db.redis.sadd(key, req.item_id)
        except Exception as e:
            log.error(f"Redis blocked-set write failed: {e}")
        return {"status": "ok", "sasrec_loss": None}

    # Capture s_t BEFORE profile update
    click_seq_before = await profile_manager.get_click_sequence(req.user_id)

    if req.action == "click":
        await profile_manager.log_click(req.user_id, req.item_id,
                                         source="web_ui", action="click")
    else:
        # "skip" or unknown — log as skip, no training
        profile = await profile_manager.get_profile(req.user_id)
        profile.purchases.append({
            "timestamp": datetime.now().isoformat(),
            "item_id":   req.item_id,
            "action":    "skip",
        })
        await profile_manager.save_profile(req.user_id)

    # Push to Redis for background logging
    try:
        if db.redis:
            log_entry = {
                "user_id":    req.user_id,
                "asin":       req.item_id,
                "action":     req.action,
                "timestamp":  datetime.now().isoformat(),
                "session_id": req.session_id,
                "source":     req.source,
                "is_guest":   req.user_id.startswith("guest_") or req.user_id == "web_user",
            }
            await db.redis.rpush("nba_interactions", json.dumps(log_entry))
    except Exception as e:
        log.error(f"Redis queue push failed: {e}")

    # Train the DIF-SASRec personal model on click interactions
    loss = None
    if click_seq_before and req.action == "click":
        async with container.agent_pool.borrow() as agent:
            agent.load_user(req.user_id, settings.DATA_DIR)
            loss = recommend_engine.train_personal(
                req.user_id, req.item_id, agent,
                click_seq_before=click_seq_before,
            )
            agent.save_user(req.user_id, settings.DATA_DIR)

    return {"status": "ok", "sasrec_loss": loss}
