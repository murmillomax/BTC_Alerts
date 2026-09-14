from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware

from . import models
from .database import Base, engine
from .auth import router as auth_router

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BTC Alerts",
    description="Plataforma de alertas de Bitcoin",
    version="0.1.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    SessionMiddleware,
    secret_key="CAMBIAR_ESTA_CLAVE_DESPUES",
    https_only=False,
    same_site="lax"
)

app.include_router(auth_router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/dashboard")
def dashboard(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="No estás autenticado"
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )
