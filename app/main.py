from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .routers import auth, post, user, vote, web


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan, docs_url="/api/docs", redoc_url="/api/redoc")

origins = ["http://localhost:8000", "http://127.0.0.1"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for CSS, JS, images
app.mount("/static", StaticFiles(directory="static"), name="static")

# API routes
app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)

# Web pages routes (Jinja2 templates)
app.include_router(web.router)


@app.get("/api")
async def root() -> dict[str, str]:
    return {"message": "This message was updated from the CI/CD pipeline!"}
