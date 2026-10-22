import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, UUID, Enum as SQLEnum, DECIMAL, DateTime, func, Boolean, Text, text
from enum import Enum

from ..database.database import Base

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
    STARTER = "starter"
    ADVANCED = "advanced"
    PROFESSIONAL = "professional"

class BillingPeriod(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Subscription(Base):

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_number = Column(String(14), nullable=False, unique=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    email = Column(String, nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.INCOMPLETE)
    plan_id = Column(SQLEnum(PlanId), nullable=False)
    plan_name = Column(String, nullable=True)
    billing_period = Column(SQLEnum(BillingPeriod), nullable=False)
    trial_days = Column(Integer, nullable=False, default=0)
    price = Column(DECIMAL(10, 2), nullable=False)
    order_commission_percent = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True, index=True)
    stripe_checkout_session_id = Column(String, nullable=True, index=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    last_payment_error = Column(Text, nullable=True)
    sub_idempotency_key = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)