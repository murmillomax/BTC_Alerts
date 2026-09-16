import bcrypt
import secrets

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from .time_utils import utc_now

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User

from .email import send_verification_email

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#--------------- Register ----------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
#--------------- Login ----------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
#--------------- Register ----------------------
@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )

    password_hash = bcrypt.hashpw(
        data.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    verification_code = f"{secrets.randbelow(1000000):06d}"

    verification_expires = (
        utc_now() + timedelta(minutes=15)
    )

    user = User(
        email=data.email,
        password_hash=password_hash,
        email_verified=False,
        verification_code=verification_code,
        verification_expires=verification_expires,
        subscription_status="PENDING",
        subscription_expires=None
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        send_verification_email(
            recipient=user.email,
            verification_code=verification_code
        )
    except Exception as e:
        db.delete(user)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"No se pudo enviar el correo de verificación: {str(e)}"
        )

    return {
        "message": "Usuario registrado correctamente. Revisa tu correo para verificar tu cuenta.",
        "user_id": user.id,
        "email": user.email
    }

#--------------- Verify Email ----------------------

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str


@router.post("/verify-email")
def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=400,
            detail="El email ya está verificado"
        )

    if not user.verification_code:
        raise HTTPException(
            status_code=400,
            detail="No existe un código de verificación"
        )

    if not user.verification_expires:
        raise HTTPException(
            status_code=400,
            detail="El código de verificación no tiene fecha de expiración"
        )

    if utc_now() > user.verification_expires:
        raise HTTPException(
            status_code=400,
            detail="El código de verificación ha expirado"
        )

    if data.verification_code != user.verification_code:
        raise HTTPException(
            status_code=400,
            detail="Código de verificación incorrecto"
        )

    user.email_verified = True

    user.subscription_status = "TRIAL"

    user.subscription_expires = (
        utc_now() + relativedelta(months=3)
    )

    user.verification_code = None
    user.verification_expires = None

    db.commit()
    db.refresh(user)

    return {
        "message": "Email verificado correctamente. Tu período de prueba de 3 meses ha sido activado.",
        "user_id": user.id,
        "email": user.email,
        "subscription_status": user.subscription_status,
        "subscription_expires": user.subscription_expires
    }

#--------------- Login -----------------------------
@router.post("/login")
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos"
        )

    password_ok = bcrypt.checkpw(
        data.password.encode("utf-8"),
        user.password_hash.encode("utf-8")
    )

    if not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos"
        )

    request.session["user_id"] = user.id

    return {
        "message": "Login correcto",
        "user_id": user.id,
        "email": user.email,
        "subscription_status": user.subscription_status
    }
#--------------- Me -----------------------------
@router.get("/me")
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="No estás autenticado"
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado"
        )

    return {
        "user_id": user.id,
        "email": user.email,
        "subscription_status": user.subscription_status,
        "subscription_expires": user.subscription_expires,
        "alerts_enabled": user.alerts_enabled
    }
#--------------- Logout -----------------------------
@router.post("/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "message": "Sesión cerrada correctamente"
    }