from collections import OrderedDict
from datetime import datetime
import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_payload
from app.schemas.subscription import SubscriptionResponse
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["subscription"])

PRODUCT_TIER_MAP = {
    "monthly": "maestro",
    "yearly": "maestro",
    "lifetime": "maestro",
    "apicultor_monthly": "apicultor",
    "apicultor_yearly": "apicultor",
    "maestro_monthly": "maestro",
    "maestro_yearly": "maestro",
}

PROCESSED_EVENT_CACHE_SIZE = 1024
_PROCESSED_REVENUECAT_EVENTS: OrderedDict[str, None] = OrderedDict()


def _get_webhook_secret() -> str:
    return os.getenv("REVENUECAT_WEBHOOK_SECRET", "").strip()


def _get_event_identity(event: dict) -> str | None:
    event_id = event.get("id")
    if event_id:
        return str(event_id)

    event_type = event.get("type")
    event_timestamp_ms = event.get("event_timestamp_ms")
    fallback_subject = (
        event.get("transaction_id")
        or event.get("original_transaction_id")
        or event.get("app_user_id")
        or event.get("original_app_user_id")
        or event.get("product_id")
    )
    if event_type and event_timestamp_ms and fallback_subject:
        return f"{event_type}:{fallback_subject}:{event_timestamp_ms}"
    return None


def _remember_processed_event(event_identity: str) -> None:
    if event_identity in _PROCESSED_REVENUECAT_EVENTS:
        _PROCESSED_REVENUECAT_EVENTS.move_to_end(event_identity)
        return

    _PROCESSED_REVENUECAT_EVENTS[event_identity] = None
    if len(_PROCESSED_REVENUECAT_EVENTS) > PROCESSED_EVENT_CACHE_SIZE:
        _PROCESSED_REVENUECAT_EVENTS.popitem(last=False)


def _extract_user_id(event: dict) -> int | None:
    candidate_ids = [
        event.get("app_user_id"),
        event.get("original_app_user_id"),
        *(event.get("aliases") or []),
    ]
    for candidate in candidate_ids:
        try:
            return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _resolve_tier(product_id: str) -> str:
    if not product_id:
        return "aprendiz"
    base_product_id = product_id.split(":")[0]
    return PRODUCT_TIER_MAP.get(product_id, PRODUCT_TIER_MAP.get(base_product_id, "aprendiz"))


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
    webhook_secret = _get_webhook_secret()
    if not webhook_secret:
        logger.error("RevenueCat webhook rejected because REVENUECAT_WEBHOOK_SECRET is missing")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )
    if authorization != webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    body = await request.json()
    event = body.get("event", {})
    event_type = event.get("type", "")
    user_id = _extract_user_id(event)
    if user_id is None:
        return {"status": "ignored", "reason": "invalid_app_user_id"}

    event_identity = _get_event_identity(event)
    if event_identity and event_identity in _PROCESSED_REVENUECAT_EVENTS:
        return {"status": "ignored", "reason": "duplicate_event"}

    service = SubscriptionService(db)
    event_timestamp_ms = event.get("event_timestamp_ms")
    if service.should_ignore_revenuecat_event(user_id, event_timestamp_ms):
        if event_identity:
            _remember_processed_event(event_identity)
        return {"status": "ignored", "reason": "stale_event"}

    product_id = event.get("product_id", "")
    tier = _resolve_tier(product_id)
    expires_at = None
    expiration_ts = event.get("expiration_at_ms")
    if expiration_ts:
        expires_at = datetime.utcfromtimestamp(expiration_ts / 1000)

    revenuecat_customer_id = event.get("app_user_id") or event.get("original_app_user_id")

    if event_type in ("INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION", "PRODUCT_CHANGE"):
        service.update_from_revenuecat(
            user_id=user_id,
            tier=tier,
            status="active",
            revenuecat_customer_id=revenuecat_customer_id,
            expires_at=expires_at,
        )
    elif event_type in ("CANCELLATION", "EXPIRATION", "BILLING_ISSUE"):
        service.update_from_revenuecat(
            user_id=user_id,
            tier="aprendiz",
            status="expired" if event_type == "EXPIRATION" else "cancelled",
            revenuecat_customer_id=revenuecat_customer_id,
            expires_at=expires_at,
        )
    else:
        return {"status": "ignored", "reason": "unsupported_event_type"}

    if event_identity:
        _remember_processed_event(event_identity)

    logger.info(f"RevenueCat webhook processed: type={event_type}, user={user_id}, tier={tier}")
    return {"status": "ok"}
