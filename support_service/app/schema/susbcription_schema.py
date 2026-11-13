from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubscriptionStatus(str, Enum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class Currency(str, Enum):
    EUR = "EUR"
    GEL = "GEL"
    USD = "USD"
    GBP = "GBP"
    CHF = "CHF"
    PLN = "PLN"

class PlanId(str, Enum):
    BASIC = "basic"
    ONLINE = "online"
    ADVANCED = "advanced"
    PROFESSIONAL = "professional"

class BillingPeriod(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class VatStatus(str, Enum):
    NONE = "none"
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"

class SubscriptionDataDTO(BaseModel):
    subscription_number: str
    restaurant_id: UUID
    email: str
    owner_id: UUID
    status: SubscriptionStatus
    plan_id: PlanId
    plan_name: Optional[str] = None
    billing_period: BillingPeriod
    trial_days: int
    price: Decimal
    order_commission_percent: Decimal
    currency: Currency

    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    last_payment_error: Optional[str] = None
    sub_idempotency_key: UUID

    vat_id: Optional[str] = None
    vat_status: VatStatus
    vat_checked_at: Optional[datetime] = None
    country: str

    model_config = ConfigDict(from_attributes=True)