from fastapi import Request, APIRouter
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates_auth")
router = APIRouter()


@router.get("/admin/login", response_class=HTMLResponse)
def authentication(request: Request):
    return templates.TemplateResponse("login.html", {"request" : request})