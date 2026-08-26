from fastapi import HTTPException

from fastapi.params import Depends

from ..role.roles import IdentityRole
from user_service.app.security.jwt.jwt import get_payload

def required_role(role : IdentityRole, payload : dict = Depends(get_payload)):
    if payload["role"] != role.value:
        raise HTTPException(status_code=403, detail="Forbidden")
    return payload