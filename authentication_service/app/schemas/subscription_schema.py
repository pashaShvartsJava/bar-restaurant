from decimal import Decimal
from zoneinfo import ZoneInfoNotFoundError, ZoneInfo
from pydantic import BaseModel, EmailStr
from uuid import UUID


from enum import Enum

class PlanId(str, Enum):
    STARTER = "starter"
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
    PlanId.STARTER: {
        "monthly": Decimal("39.99"),
        "yearly": Decimal("419.99"),
        "trial_days": 3,
        "currency": Currency.EUR,
    },
    PlanId.ADVANCED: {
        "monthly": Decimal("119.99"),
        "yearly": Decimal("1259.99"),
        "trial_days": 7,
        "currency": Currency.EUR,
    },
    PlanId.PROFESSIONAL: {
        "monthly": Decimal("199.99"),
        "yearly": Decimal("2099.99"),
        "trial_days": 14,
        "currency": Currency.EUR,
    },
}

class SubscriptionDTO(BaseModel):
    plan_id: str
    billing_period: BillingPeriod
    trial_days: int
    price: Decimal
    currency: str = "EUR"
    order_commission_percent: Decimal = Decimal("0")

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
