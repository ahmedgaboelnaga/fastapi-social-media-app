from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Web Pages"])

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - Posts feed"""
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/create", response_class=HTMLResponse)
async def create_post_page(request: Request):
    """Create post page"""
    return templates.TemplateResponse("create_post.html", {"request": request})


@router.get("/edit", response_class=HTMLResponse)
async def edit_post_page(request: Request):
    """Edit post page"""
    return templates.TemplateResponse("edit_post.html", {"request": request})


@router.get("/my-posts", response_class=HTMLResponse)
async def my_posts_page(request: Request):
    """My posts page"""
    return templates.TemplateResponse("my_posts.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """User profile page"""
    return templates.TemplateResponse("profile.html", {"request": request})
