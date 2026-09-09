from enum import Enum

class IdentityRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"