from fastapi import Request, APIRouter
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="booking_service/templates")

router = APIRouter()

@router.get("/bar_name", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse("main_page.html", context={"request": request})