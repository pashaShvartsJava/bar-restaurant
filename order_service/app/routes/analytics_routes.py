from datetime import date
from fastapi import APIRouter, Request, Depends
from starlette.templating import Jinja2Templates

from ..dependencies.dependencies import get_order_service_dependency
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole

from ..service.order_service import OrderService
from ..config.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates/analytics")
INTERNAL_TOKEN=settings.internal_token

@router.get("/analytics")
async def show_analytics_page(request : Request,
                              date_from : date | None = None,
                              date_to : date | None = None,
                              service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, payload=payload)
    analytics = await service.get_analytics(date_from, date_to)
    return templates.TemplateResponse("analytics.html", {"request" : request,"analytics" : analytics, **analytics})