
from fastapi import FastAPI, Request
from starlette.requests import Request

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get('/bar_name', response_class=HTMLResponse)
def get_main_page(request: Request):
    return templates.TemplateResponse("main_page.html", {"request" : request} )