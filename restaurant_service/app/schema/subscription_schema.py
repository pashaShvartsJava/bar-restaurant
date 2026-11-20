from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID


from enum import Enum

class PlanId(str, Enum):
    BASIC = "basic"
    ONLINE = "online"
    ADVANCED = "advanced"
    PROFESSIONAL = "professional"

class BillingPeriod(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Currency(str, Enum):
    EUR = "EUR"
    GEL = "GEL"
    USD = "USD"
    GBP = "GBP"
    CHF = "CHF"
    PLN = "PLN"

PLANS = {
    PlanId.BASIC: {
        "name": "Basic",
        "monthly": Decimal("39.99"),
        "yearly": Decimal("419.99"),
        "trial_days": 3,
        "currency": Currency.EUR,
        "order_commission_percent": 0,
    },
    PlanId.ONLINE: {
        "name": "Online",
        "monthly": Decimal("59.99"),
        "yearly": Decimal("629.99"),
        "trial_days": 3,
        "currency": Currency.EUR,
        "order_commission_percent": 9,
    },
    PlanId.ADVANCED: {
        "name": "Advanced",
        "monthly": Decimal("119.99"),
        "yearly": Decimal("1259.99"),
        "trial_days": 7,
        "currency": Currency.EUR,
        "order_commission_percent": 5,
    },
    PlanId.PROFESSIONAL: {
        "name": "Professional Business",
        "monthly": Decimal("199.99"),
        "yearly": Decimal("2099.99"),
        "trial_days": 14,
        "currency": Currency.EUR,
        "order_commission_percent": 1,
    },
}

class VatStatus(str, Enum):
    NONE = "none"
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"

class AccessStatus(str, Enum):
    ENABLED = "enabled"
    SUSPENDED = "suspended"

class SubscriptionCheckoutDTO(BaseModel):
    user_id: UUID
    restaurant_id: UUID
    sub_idempotency_key: UUID
    email: EmailStr
    plan_id: str
    billing_period: str
    trial_days: int
    price: Decimal
    order_commission_percent: Decimal = Decimal("0")
    currency: str = "EUR"
    key: str

class SubscriptionStatus(str, Enum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELLED = "cancelled"
    PAUSED = "paused"

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
    access_status: AccessStatus

    model_config = ConfigDict(from_attributes=True)
