from fastapi import APIRouter, Request, Form, Depends
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from ..service.dish_service import MenuService
from ..dependencies.dependencies import get_menu_service

router = APIRouter()
templates = Jinja2Templates(directory="menu_service/templates_menu")

@router.get("/menu_page", response_class=HTMLResponse)
def get_menu_page(request: Request, menu_service : MenuService = Depends(get_menu_service)):
    all_dishes = menu_service.get_all_dishes()
    return templates.TemplateResponse("menu.html", {"request":request, "all_dishes" : all_dishes})
