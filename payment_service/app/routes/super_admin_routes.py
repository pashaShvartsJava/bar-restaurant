from datetime import datetime, timezone

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from ..config.config import settings
from ..dependencies.dependencies import get_subscription_service_dependency
from ..models.subscriptions import AccessStatus
from ..security.authorization.authorization import required_role
from ..security.jwt.jwt import get_secret_payload

from ..security.role.role import IdentityRole
from ..service.subscription_service import SubscriptionService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
INTERNAL_TOKEN=settings.internal_token

@router.get("/subscriptions/secret_api")
async def subscriptions_page(request : Request, service : SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_secret_payload(request)
    required_role(IdentityRole.SUPERADMIN, payload)
    subscriptions = await service.get_subscriptions()
    return templates.TemplateResponse("subscriptions.html", {"request" : request, "subscriptions" : subscriptions})

@router.post("/subscriptions/secret_api/{subscription_id}/access")
async def update_subscription_access(subscription_id: int,
                                     request: Request,
                                     access_status: AccessStatus = Form(...),
                                     suspended_reason: str | None = Form(None),
                                     service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_secret_payload(request)
    required_role(IdentityRole.SUPERADMIN, payload)
    async with service.subscription_repository.db.begin():
        subscription = await service.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        if access_status == AccessStatus.SUSPENDED:
            if not suspended_reason or not suspended_reason.strip():
                raise HTTPException(status_code=400, detail="Suspension reason is required")
            subscription.access_status = AccessStatus.SUSPENDED
            subscription.suspended_reason = suspended_reason.strip()
            subscription.suspended_at = datetime.now(timezone.utc)
            subscription.suspended_by = str(payload.get("sub", "SUPERADMIN"))
        elif access_status == AccessStatus.ENABLED:
            subscription.access_status = AccessStatus.ENABLED
            subscription.suspended_reason = None
            subscription.suspended_at = None
            subscription.suspended_by = None
        else:
            raise HTTPException(status_code=400, detail="Invalid access status")
        await service.update_subscription(subscription)
        return RedirectResponse(url="/subscriptions/secret_api", status_code=303)
