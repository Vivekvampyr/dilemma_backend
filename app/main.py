from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database import engine, Base
from app.routers import auth, users, posts, comments, communities, votes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create upload dir if using local storage
    if settings.MEDIA_STORAGE == "local":
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Reddit-style dilemma sharing platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (local media uploads) ────────────────────────────────────────
if settings.MEDIA_STORAGE == "local":
    app.mount("/media", StaticFiles(directory=settings.UPLOAD_DIR), name="media")

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix="/api/v1/auth",        tags=["Auth"])
app.include_router(users.router,       prefix="/api/v1/users",       tags=["Users"])
app.include_router(communities.router, prefix="/api/v1/communities", tags=["Communities"])
app.include_router(posts.router,       prefix="/api/v1/posts",       tags=["Posts"])
app.include_router(comments.router,    prefix="/api/v1/comments",    tags=["Comments"])
app.include_router(votes.router,       prefix="/api/v1/votes",       tags=["Votes"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}