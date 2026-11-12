from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr
from uuid import UUID


from enum import Enum

STRIPE_PRICE_IDS = {
    "basic": "price_1Ub39rEBszTkRGCJJDTd6TE2",
    "online": "price_1Ub3AdEBszTkRGCJmN37jyvq",
    "advanced": "price_1Ub3B3EBszTkRGCJnyvZe6sf",
    "professional": "price_1Ub3BnEBszTkRGCJxVmKKtCX"
}

PRICE_TO_PLAN = {v: k for k, v in STRIPE_PRICE_IDS.items()}

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
        "order_commission_percent": 11,
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
    vat_id: str | None = None
    vat_verified: str
    vat_checked_at: datetime
    country: str
