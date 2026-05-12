from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.schemas.subscription import TIER_AI_ACCESS, TIER_AI_MONTHLY_LIMIT, TIER_APIARY_LIMITS

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get_existing(self, user_id: int) -> Subscription | None:
        return self.db.query(Subscription).filter(Subscription.userId == user_id).first()

    def get_or_create(self, user_id: int) -> Subscription:
        sub = self.get_existing(user_id)
        if not sub:
            sub = Subscription(userId=user_id, tier="aprendiz", status="active")
            self.db.add(sub)
            self.db.commit()
            self.db.refresh(sub)
        return sub

    def is_active_subscription(self, sub: Subscription) -> bool:
        if sub.status != "active":
            return False
        if sub.expiresAt and sub.expiresAt <= datetime.utcnow():
            return False
        return True

    def get_effective_tier_for_subscription(self, sub: Subscription) -> str:
        if not self.is_active_subscription(sub):
            return "aprendiz"
        return sub.tier

    def get_effective_status_for_subscription(self, sub: Subscription) -> str:
        if sub.status != "active":
            return sub.status
        if sub.expiresAt and sub.expiresAt <= datetime.utcnow():
            return "expired"
        return sub.status

    def get_tier(self, user_id: int) -> str:
        sub = self.get_or_create(user_id)
        return self.get_effective_tier_for_subscription(sub)

    def check_apiary_limit(self, user_id: int, current_apiary_count: int) -> bool:
        """Retorna True si puede crear mÃ¡s apiarios."""
        tier = self.get_tier(user_id)
        limit = TIER_APIARY_LIMITS.get(tier)
        if limit is None:
            return True
        return current_apiary_count < limit

    def can_use_ai(self, user_id: int) -> bool:
        tier = self.get_tier(user_id)
        return TIER_AI_ACCESS.get(tier, False)

    def should_ignore_revenuecat_event(self, user_id: int, event_timestamp_ms: int | None) -> bool:
        if not event_timestamp_ms:
            return False

        sub = self.get_existing(user_id)
        if not sub or not sub.revenuecatCustomerId or not sub.updatedAt:
            return False

        current_updated_ms = int(sub.updatedAt.timestamp() * 1000)
        return event_timestamp_ms <= current_updated_ms

    def get_expiring_subscriptions(
        self,
        reference_time: datetime | None = None,
        within_days: int = 7,
    ) -> list[Subscription]:
        now = reference_time or datetime.utcnow()
        return (
            self.db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.expiresAt.isnot(None),
                Subscription.expiresAt > now,
                Subscription.expiresAt <= now + timedelta(days=within_days),
                Subscription.tier != "aprendiz",
            )
            .all()
        )

    def reconcile_expired_subscriptions(self, reference_time: datetime | None = None) -> int:
        now = reference_time or datetime.utcnow()
        expired_subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.expiresAt.isnot(None),
                Subscription.expiresAt <= now,
            )
            .all()
        )

        updated = 0
        for subscription in expired_subscriptions:
            subscription.status = "expired"
            subscription.tier = "aprendiz"
            updated += 1

        if updated:
            self.db.commit()

        return updated

    def update_from_revenuecat(
        self,
        user_id: int,
        tier: str,
        status: str,
        revenuecat_customer_id: str = None,
        expires_at: datetime = None,
    ) -> Subscription:
        sub = self.get_or_create(user_id)
        sub.tier = tier
        sub.status = status
        if revenuecat_customer_id is not None:
            sub.revenuecatCustomerId = revenuecat_customer_id
        if expires_at is not None:
            sub.expiresAt = expires_at
        self.db.commit()
        self.db.refresh(sub)
        logger.info(f"Subscription updated for user {user_id}: tier={tier}, status={status}")
        return sub

    def build_response(self, sub: Subscription) -> dict:
        tier = self.get_effective_tier_for_subscription(sub)
        status = self.get_effective_status_for_subscription(sub)
        return {
            "id": sub.id,
            "userId": sub.userId,
            "tier": tier,
            "status": status,
            "expiresAt": sub.expiresAt,
            "createdAt": sub.createdAt,
            "apiaryLimit": TIER_APIARY_LIMITS.get(tier),
            "aiAccess": TIER_AI_ACCESS.get(tier, False),
            "aiMonthlyLimit": TIER_AI_MONTHLY_LIMIT.get(tier),
        }
