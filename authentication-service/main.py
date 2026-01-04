from fastapi import FastAPI
from authx  import AuthX, AuthXConfig

app = FastAPI()
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"


