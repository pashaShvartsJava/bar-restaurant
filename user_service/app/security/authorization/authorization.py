from fastapi import HTTPException

from fastapi.params import Depends

from ..role.roles import IdentityRole
from ..jwt.jwt import get_payload

def required_role(role : IdentityRole, payload : dict = Depends(get_payload)):
    if payload["role"] != role.value:
        raise HTTPException(status_code=403, detail="Forbidden")
    return payload

def required_roles(*roles: IdentityRole, payload: dict):
    if payload["role"] not in [role.value for role in roles]:
        raise HTTPException(status_code=403, detail="Forbidden")