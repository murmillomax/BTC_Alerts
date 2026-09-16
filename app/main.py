from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware

from . import models
from .database import Base, engine, SessionLocal
from .auth import router as auth_router
from .time_utils import utc_now

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


@app.get("/verify-email")
def verify_email_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="verify-email.html"
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

    db = SessionLocal()

    try:
        user = db.query(models.User).filter(
            models.User.id == user_id
        ).first()

        if not user:
            request.session.clear()

            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )

        if not user.email_verified:
            return templates.TemplateResponse(
                request=request,
                name="verify-email.html"
            )

        # Comprobar vencimiento de la suscripción
        if (
            user.subscription_expires is not None
            and user.subscription_expires < utc_now()
            and user.subscription_status in ["TRIAL", "ACTIVE"]
        ):
            user.subscription_status = "EXPIRED"
            db.commit()
            db.refresh(user)

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html"
        )

    finally:
        db.close()
