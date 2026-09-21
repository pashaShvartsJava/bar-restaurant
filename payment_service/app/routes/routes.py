from fastapi import APIRouter, Request, Depends

from ..schemas.payment_schema import PaymentDTO
from ..security.authorization.authorization import required_roles
from ..security.jwt.jwt import get_payload
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_payment_service_dependency
from ..service.payment_service import PaymentService

router = APIRouter()

@router.post("/payment/create")
async def create_payment(request : Request, data : PaymentDTO,
                         service : PaymentService = Depends(get_payment_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = payload["sub"]
    payment = await service.create_payment(data, client_id)
