import hmac
import secrets
from typing import Annotated

from fastapi import Request, APIRouter, HTTPException, Form
import bcrypt
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from ..schemas.admin_schema import AdminLogin
from ..security.rate_limit import check_login_rate_limit, reset_login_rate_limit
from ..config.config import settings
import datetime
import jwt

templates = Jinja2Templates(directory="app/templates_auth")
router = APIRouter()
INTERNAL_TOKEN = settings.internal_token

PLATFORM_ADMIN_LOGIN = settings.PLATFORM_ADMIN_LOGIN
PLATFORM_ADMIN_PASSWORD_HASH = settings.PLATFORM_ADMIN_PASSWORD_HASH
PLATFORM_ADMIN_KEY_HASH = settings.PLATFORM_ADMIN_KEY_HASH
PLATFORM_ADMIN_JWT_SECRET = settings.PLATFORM_ADMIN_JWT_SECRET
SUPER_ADMIN_SUB = settings.SUPER_ADMIN_SUB

def create_platform_admin_token() -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(SUPER_ADMIN_SUB),
        "role": "superadmin",
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(hours=1)).timestamp())}
    return jwt.encode(payload, PLATFORM_ADMIN_JWT_SECRET, algorithm="HS256")


@router.get("/admin/login/secret_api", response_class=HTMLResponse)
def admin_login(request : Request):
    return templates.TemplateResponse("platform_login.html", {"request" : request})

@router.post("/admin/login/secret_api")
async def admin_login(data: Annotated[AdminLogin, Form()]):
    if not (PLATFORM_ADMIN_LOGIN and PLATFORM_ADMIN_PASSWORD_HASH and PLATFORM_ADMIN_KEY_HASH):
        raise HTTPException(status_code=500, detail="Platform admin is not configured")
    await check_login_rate_limit(str(data.email))
    email_ok = hmac.compare_digest(str(data.email).strip().lower(), PLATFORM_ADMIN_LOGIN.strip().lower())
    password_ok = False
    if email_ok:
        password_ok = bcrypt.checkpw(data.password.encode("utf-8"), PLATFORM_ADMIN_PASSWORD_HASH.encode("utf-8"))
    else:
        bcrypt.checkpw(b"dummy", PLATFORM_ADMIN_PASSWORD_HASH.encode("utf-8"))
    print("LOGIN CHECK:", email_ok, password_ok)
    if not (email_ok and password_ok):
        raise HTTPException(status_code=401, detail=[{"loc": ["body", "email"], "msg": "Неверный email или пароль"}])
    key_ok = bcrypt.checkpw(data.authentication_key.encode("utf-8"), PLATFORM_ADMIN_KEY_HASH.encode("utf-8"))
    print("KEY CHECK:", key_ok)
    if not key_ok:
        raise HTTPException(status_code=401, detail=[{"loc": ["body", "authentication_key"], "msg": "Неверный специальный ключ"}])
    await reset_login_rate_limit(str(data.email))
    token = create_platform_admin_token()
    redirect = RedirectResponse(url="/admin_panel/secret_api", status_code=303)
    csrf_token = secrets.token_urlsafe(32)
    redirect.set_cookie(key="access_token", value=token, httponly=True, secure=True, max_age=3600, samesite="lax")
    redirect.set_cookie(key="csrf_token", value=csrf_token, httponly=False, secure=True, max_age=3600, samesite="lax")
    return redirect