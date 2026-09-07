from datetime import datetime, timedelta, timezone
from pathlib import Path

from ...config.config import settings
from ...model.identity_model import IdentityRole, Status

import jwt

PRIVATE_KEY_PATH = settings.jwt_private_key_path
PUBLIC_KEY_PATH = settings.jwt_public_key_path
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

def create_access_token(identity_id : str, role : IdentityRole, status : Status) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload ={
        "sub" : str(identity_id),
        "role" : role.value,
        "status" : status.value,
        "exp" : expire
    }
    private_key = Path(PRIVATE_KEY_PATH).read_text()

    token = jwt.encode(payload, private_key, ALGORITHM)

    return token

def decode_access_token(token : str) -> dict:
    public_key = Path(PUBLIC_KEY_PATH).read_text()
    payload = jwt.decode(token, public_key, [ALGORITHM])
    return payload