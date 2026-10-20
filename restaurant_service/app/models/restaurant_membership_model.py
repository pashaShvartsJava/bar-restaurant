from sqlalchemy import Column, DateTime, String, Enum as SQLEnum, func, Integer, ForeignKey
from sqlalchemy.dialects.postgresql  import UUID
from enum import Enum

from sqlalchemy.orm import relationship

from ..database.database import Base

class MembershipRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    PENDING = "pending"
    FAILED = "failed"
    BLOCKED = "blocked"


class MembershipStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class RestaurantMembership(Base):
    __tablename__ = "restaurant_memberships"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    identity_id =  Column(UUID(as_uuid=True), nullable=False, index=True)
    role = Column(SQLEnum(MembershipRole, name="membership_role"), nullable=False, default=MembershipRole.OWNER)
    status = Column(SQLEnum(MembershipStatus, name="membership_status"), nullable=False, default=MembershipStatus.ACTIVE)

    restaurant = relationship("Restaurant", back_populates="memberships")