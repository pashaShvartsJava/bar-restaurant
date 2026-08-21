from datetime import datetime, timedelta, timezone
from pathlib import Path
from ...config.config import settings
from ...model.identity_model import IdentityRole

import jwt

BASE_DIR = Path(__file__).resolve().parents[2]

PRIVATE_KEY_PATH = settings.jwt_private_key_path
PUBLIC_KEY_PATH = settings.jwt_public_key_path
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

def create_access_token(identity_id : str, role : IdentityRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload ={
        "sub" : identity_id,
        "role" : role,
        "expire" : expire
    }

    token = jwt.encode(payload, PRIVATE_KEY_PATH, ALGORITHM)

    return token

def decode_access_token(token : str) -> dict:
    payload = jwt.decode(token, PUBLIC_KEY_PATH, [ALGORITHM])
    return payload