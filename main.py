import os
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
import logger
from contextlib import asynccontextmanager
import  redis.asyncio as redis


@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.redis=redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True        
    )
    yield
    app.state.redis.close()


from routers import users , files
load_dotenv()

app=FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    same_site="lax"
)
app.include_router(files.router)
app.include_router(users.router)
