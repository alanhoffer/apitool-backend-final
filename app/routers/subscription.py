from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_payload
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import SubscriptionResponse
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["subscription"])

REVENUECAT_WEBHOOK_SECRET = os.getenv("REVENUECAT_WEBHOOK_SECRET", "")

# Mapeo de product IDs de RevenueCat a tiers
PRODUCT_TIER_MAP = {
    "apicultor_monthly": "apicultor",
    "apicultor_yearly": "apicultor",
    "maestro_monthly": "maestro",
    "maestro_yearly": "maestro",
}


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    user_id = int(payload.get("sub"))
    service = SubscriptionService(db)
    sub = service.get_or_create(user_id)
    return service.build_response(sub)


@router.post("/webhook")
async def revenuecat_webhook(
    request: Request,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    # Validar secret del webhook
    if REVENUECAT_WEBHOOK_SECRET and authorization != REVENUECAT_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    body = await request.json()
    event = body.get("event", {})
    event_type = event.get("type", "")
    app_user_id = event.get("app_user_id")  # Debe ser el user_id de nuestra app

    if not app_user_id:
        return {"status": "ignored", "reason": "no app_user_id"}

    try:
        user_id = int(app_user_id)
    except (ValueError, TypeError):
        return {"status": "ignored", "reason": "invalid app_user_id"}

    service = SubscriptionService(db)
    product_id = event.get("product_id", "")
    tier = PRODUCT_TIER_MAP.get(product_id, "aprendiz")
    expires_at = None

    expiration_ts = event.get("expiration_at_ms")
    if expiration_ts:
        expires_at = datetime.utcfromtimestamp(expiration_ts / 1000)

    if event_type in ("INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION", "PRODUCT_CHANGE"):
        service.update_from_revenuecat(
            user_id=user_id,
            tier=tier,
            status="active",
            revenuecat_customer_id=event.get("id"),
            expires_at=expires_at,
        )
    elif event_type in ("CANCELLATION", "EXPIRATION", "BILLING_ISSUE"):
        service.update_from_revenuecat(
            user_id=user_id,
            tier="aprendiz",
            status="expired" if event_type == "EXPIRATION" else "cancelled",
            expires_at=expires_at,
        )

    logger.info(f"RevenueCat webhook processed: type={event_type}, user={user_id}, tier={tier}")
    return {"status": "ok"}
