import httpx
from fastapi import Request, APIRouter
from starlette.templating import Jinja2Templates

from .routes import verify_csrf
from ..security.role.role import IdentityRole
from ..security.jwt.jwt import get_payload, get_secret_payload
from ..security.authorization.authorization import required_roles, required_secret_role
from uuid import UUID

from ..model.admin import Status
from ..config.config import settings
import logging

logger = logging.getLogger(__name__)


INTERNAL_TOKEN = settings.internal_token
templates = Jinja2Templates(directory="app/templates_admin")
router = APIRouter()

@router.patch("/admin_panel/secret_api/all_customers/{identity_id}/block")
async def block_customer(request : Request, identity_id: UUID):
    payload = get_payload(request)
    required_secret_role(IdentityRole.SUPERADMIN, payload=payload)
    await verify_csrf(request)
    async with httpx.AsyncClient() as client:
        response = await client.patch("http://authentication-service:8000/edit_status",
                                      params={"identity_id" : str(identity_id), "status" : Status.BLOCKED.value},
                                      headers={"internal_token" : INTERNAL_TOKEN})
        response.raise_for_status()

@router.patch("/admin_panel/secret_api/all_customers/{identity_id}/unblock")
async def unblock_customer(request : Request, identity_id: UUID):
    payload = get_payload(request)
    required_secret_role(IdentityRole.SUPERADMIN, payload=payload)
    await verify_csrf(request)
    async with httpx.AsyncClient() as client:
        response = await client.patch("http://authentication-service:8000/edit_status",
                                      params={"identity_id" : str(identity_id), "status" : Status.ACTIVE.value},
                                      headers={"internal_token" : INTERNAL_TOKEN})
        response.raise_for_status()

@router.get("/admin_panel/secret_api")
async def super_admin_panel(request : Request):
    payload = get_secret_payload(request)
    required_secret_role(IdentityRole.SUPERADMIN, payload=payload)
    return templates.TemplateResponse("admin_panel_secret.html", {"request" : request})