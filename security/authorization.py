from fastapi import HTTPException

from fastapi.params import Depends

from authentication_service.authentication_service.model.identity_model import IdentityRole
from .jwt import get_payload

def required_role(role : IdentityRole, payload : dict = Depends(get_payload)):
    if payload["role"] != role.value:
        raise HTTPException(status_code=403)
    return payload