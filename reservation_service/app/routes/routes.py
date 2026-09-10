from fastapi import APIRouter, Request, Form
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from fastapi.params import Depends
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_table_service_dependency
from ..service.table_service import TableService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/tables")
async def show_tables_page(request : Request, table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    tables = await table_service.find_all_tables()
    return templates.TemplateResponse("all_tables.html", {"request" : request, "tables" : tables})

@router.get("/tables/add_table")
async def add_table_page(request : Request):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    return templates.TemplateResponse("add_table.html", {"request" : request})

@router.post("/tables/add_table")
async def add_table(request : Request,
                    table_number : int = Form(..., min=1),
                    capacity : int = Form(..., min=1),
                    table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await table_service.create_table(table_number, capacity)
    return RedirectResponse(url="/tables", status_code=303)