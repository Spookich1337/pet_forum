import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from ..database.DBconfig import engine
from ..database.DBmodels import Base
from ..database.Redisconfig import broadcast

from .routers import user, post, authorization
from .util.sockermanger import SocketManager

# from .celery import new_post_notification


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await broadcast.connect()
    yield
    await broadcast.disconnect()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


app.include_router(user.router)
app.include_router(post.router)
app.include_router(authorization.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


current_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(current_dir, "index.html")


@app.get("/")
async def root():
    return FileResponse(html_path)
