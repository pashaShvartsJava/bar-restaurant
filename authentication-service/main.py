from authx  import AuthX, AuthXConfig

from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates_auth")
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"


