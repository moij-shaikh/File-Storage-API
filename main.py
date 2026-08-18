import os
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
import logger
import database

from routers import users , files
load_dotenv()

app=FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    same_site="lax"
)
app.include_router(files.router)
app.include_router(users.router)
