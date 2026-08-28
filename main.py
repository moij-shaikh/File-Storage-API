import  redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logger

from routers import users , files

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.redis=redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True        
    )
    yield
    await app.state.redis.close()

app=FastAPI(lifespan=lifespan)
app.include_router(files.router)
app.include_router(users.router)
