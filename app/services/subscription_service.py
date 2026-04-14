from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.schemas.subscription import TIER_APIARY_LIMITS, TIER_AI_ACCESS, TIER_AI_MONTHLY_LIMIT
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, user_id: int) -> Subscription:
        sub = self.db.query(Subscription).filter(Subscription.userId == user_id).first()
        if not sub:
            sub = Subscription(userId=user_id, tier="aprendiz", status="active")
            self.db.add(sub)
            self.db.commit()
            self.db.refresh(sub)
        return sub

    def get_tier(self, user_id: int) -> str:
        sub = self.get_or_create(user_id)
        if sub.status != "active":
            return "aprendiz"
        if sub.expiresAt and sub.expiresAt < datetime.utcnow():
            return "aprendiz"
        return sub.tier

    def check_apiary_limit(self, user_id: int, current_apiary_count: int) -> bool:
        """Retorna True si puede crear más apiarios."""
        tier = self.get_tier(user_id)
        limit = TIER_APIARY_LIMITS.get(tier)
        if limit is None:
            return True
        return current_apiary_count < limit

    def can_use_ai(self, user_id: int) -> bool:
        tier = self.get_tier(user_id)
        return TIER_AI_ACCESS.get(tier, False)

    def update_from_revenuecat(self, user_id: int, tier: str, status: str,
                                revenuecat_customer_id: str = None,
                                expires_at: datetime = None) -> Subscription:
        sub = self.get_or_create(user_id)
        sub.tier = tier
        sub.status = status
        if revenuecat_customer_id:
            sub.revenuecatCustomerId = revenuecat_customer_id
        if expires_at:
            sub.expiresAt = expires_at
        self.db.commit()
        self.db.refresh(sub)
        logger.info(f"Subscription updated for user {user_id}: tier={tier}, status={status}")
        return sub

    def build_response(self, sub: Subscription) -> dict:
        tier = sub.tier if sub.status == "active" else "aprendiz"
        return {
            "id": sub.id,
            "userId": sub.userId,
            "tier": tier,
            "status": sub.status,
            "expiresAt": sub.expiresAt,
            "createdAt": sub.createdAt,
            "apiaryLimit": TIER_APIARY_LIMITS.get(tier),
            "aiAccess": TIER_AI_ACCESS.get(tier, False),
            "aiMonthlyLimit": TIER_AI_MONTHLY_LIMIT.get(tier),
        }
