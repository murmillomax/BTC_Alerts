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

from .email import (
    send_verification_email,
    send_login_code_email,
    send_password_reset_email,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

CODE_MINUTES = 15
REQUEST_COOLDOWN_SECONDS = 60
MAX_CODE_ATTEMPTS = 5
PASSWORD_COOLDOWN_HOURS = 24


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- Validaciones compartidas ----------------

def validate_new_password(password: str, confirmation: str):
    if password != confirmation:
        raise HTTPException(
            status_code=400,
            detail="Las nuevas contraseñas no coinciden"
        )

    password_bytes = password.encode("utf-8")

    if len(password_bytes) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 8 bytes"
        )

    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="La contraseña supera el límite de 72 bytes"
        )

    return password_bytes


def check_password_cooldown(user: User):
    if user.password_changed_at is None:
        return

    now = utc_now()
    elapsed = now - user.password_changed_at
    cooldown = timedelta(hours=PASSWORD_COOLDOWN_HOURS)

    if elapsed < cooldown:
        remaining = cooldown - elapsed
        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        raise HTTPException(
            status_code=429,
            detail=(
                "Por seguridad, no puedes cambiar ni restablecer "
                "la contraseña durante las 24 horas posteriores "
                "al último cambio. "
                f"Tiempo restante aproximado: {hours} h {minutes} min."
            )
        )


def code_is_valid(code: str | None, expires) -> bool:
    return bool(
        code
        and expires
        and utc_now() <= expires
    )


def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


# ---------------- Modelos de solicitud ----------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmailRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str


class CodeLoginRequest(BaseModel):
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str
    confirm_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


# ---------------- Cambiar contraseña con sesión ----------------

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión para cambiar tu contraseña"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado. Inicia sesión nuevamente"
        )

    try:
        password_ok = bcrypt.checkpw(
            data.current_password.encode("utf-8"),
            user.password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        password_ok = False

    if not password_ok:
        raise HTTPException(
            status_code=400,
            detail="La contraseña actual es incorrecta"
        )

    check_password_cooldown(user)

    password_bytes = validate_new_password(
        data.new_password,
        data.confirm_password
    )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe ser diferente"
        )

    user.password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    ).decode("utf-8")

    user.password_changed_at = utc_now()

    db.commit()

    return {"message": "Contraseña actualizada correctamente"}


# ---------------- Registro ----------------

@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        if existing_user.email_verified:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El email ya está registrado. "
                    "Inicia sesión o recupera tu contraseña."
                )
            )

        # La cuenta existe, pero todavía no verificó el correo.
        # No cambiar la contraseña ni crear otra cuenta.
        generic_message = (
            "La cuenta ya existe y necesita verificar su correo. "
            "Si corresponde, recibirás un nuevo código."
        )

        now = utc_now()

        # Respetar el límite de 60 segundos desde la solicitud anterior.
        if existing_user.verification_expires:
            previous_request = (
                existing_user.verification_expires
                - timedelta(minutes=CODE_MINUTES)
            )

            if now - previous_request < timedelta(
                seconds=REQUEST_COOLDOWN_SECONDS
            ):
                return {"message": generic_message}

        verification_code = generate_code()
        existing_user.verification_code = verification_code
        existing_user.verification_expires = (
            now + timedelta(minutes=CODE_MINUTES)
        )

        db.commit()

        try:
            send_verification_email(
                recipient=existing_user.email,
                verification_code=verification_code
            )
        except Exception:
            existing_user.verification_code = None
            existing_user.verification_expires = None
            db.commit()

            raise HTTPException(
                status_code=500,
                detail="No se pudo enviar el correo de verificación"
            )

        return {
            "message": generic_message,
            "email": existing_user.email
        }

    password_bytes = data.password.encode("utf-8")

    if len(password_bytes) < 8 or len(password_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener entre 8 y 72 bytes"
        )

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    ).decode("utf-8")

    verification_code = generate_code()
    verification_expires = utc_now() + timedelta(minutes=CODE_MINUTES)

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
    except Exception:
        db.delete(user)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el correo de verificación"
        )

    return {
        "message": (
            "Usuario registrado correctamente. "
            "Revisa tu correo para verificar tu cuenta."
        ),
        "user_id": user.id,
        "email": user.email
    }
# ---------------- Verificar correo ----------------

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

    if not user.verification_code or not user.verification_expires:
        raise HTTPException(
            status_code=400,
            detail="No existe un código de verificación válido"
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
        "message": (
            "Email verificado correctamente. "
            "Tu período de prueba de 3 meses ha sido activado."
        ),
        "user_id": user.id,
        "email": user.email,
        "subscription_status": user.subscription_status,
        "subscription_expires": user.subscription_expires
    }

# ---------------- Reenviar código de verificación ----------------

@router.post("/resend-verification")
def resend_verification(
    data: EmailRequest,
    db: Session = Depends(get_db)
):
    generic_message = (
        "Si la cuenta existe y necesita verificar su correo, "
        "recibirás un nuevo código."
    )

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or user.email_verified:
        return {"message": generic_message}

    now = utc_now()

    # Evitar solicitudes repetidas durante 60 segundos.
    if user.verification_expires:
        previous_request = (
            user.verification_expires
            - timedelta(minutes=CODE_MINUTES)
        )

        if now - previous_request < timedelta(
            seconds=REQUEST_COOLDOWN_SECONDS
        ):
            return {"message": generic_message}

    code = generate_code()

    user.verification_code = code
    user.verification_expires = (
        now + timedelta(minutes=CODE_MINUTES)
    )

    db.commit()

    try:
        send_verification_email(
            recipient=user.email,
            verification_code=code
        )
    except Exception:
        user.verification_code = None
        user.verification_expires = None
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el código. Inténtalo más tarde."
        )

    return {"message": generic_message}

# ---------------- Login con contraseña ----------------

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

    try:
        password_ok = bcrypt.checkpw(
            data.password.encode("utf-8"),
            user.password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        password_ok = False

    if not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos"
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Debes verificar tu correo antes de iniciar sesión"
        )

    request.session["user_id"] = user.id

    return {
        "message": "Login correcto",
        "user_id": user.id,
        "email": user.email,
        "subscription_status": user.subscription_status
    }


# ---------------- Solicitar código de acceso ----------------

@router.post("/request-login-code")
def request_login_code(
    data: EmailRequest,
    db: Session = Depends(get_db)
):
    generic_message = (
        "Si la cuenta existe y está verificada, "
        "recibirás un código por correo."
    )

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not user.email_verified:
        return {"message": generic_message}

    now = utc_now()

    if (
        user.login_requested_at
        and now - user.login_requested_at
        < timedelta(seconds=REQUEST_COOLDOWN_SECONDS)
    ):
        return {"message": generic_message}

    code = generate_code()

    user.login_code = code
    user.login_code_expires = now + timedelta(minutes=CODE_MINUTES)
    user.login_requested_at = now
    user.login_attempts = 0

    db.commit()

    try:
        send_login_code_email(user.email, code)
    except Exception:
        user.login_code = None
        user.login_code_expires = None
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el código. Inténtalo más tarde."
        )

    return {"message": generic_message}


# ---------------- Entrar con código ----------------

@router.post("/login-with-code")
def login_with_code(
    data: CodeLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not user.email_verified:
        raise HTTPException(
            status_code=400,
            detail="Código inválido o expirado"
        )

    if user.login_attempts >= MAX_CODE_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Solicita un código nuevo más tarde."
        )

    if not code_is_valid(user.login_code, user.login_code_expires):
        user.login_code = None
        user.login_code_expires = None
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Código inválido o expirado. Solicita uno nuevo."
        )

    if not secrets.compare_digest(data.code, user.login_code):
        user.login_attempts += 1

        if user.login_attempts >= MAX_CODE_ATTEMPTS:
            user.login_code = None
            user.login_code_expires = None

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Código inválido o expirado"
        )

    user.login_code = None
    user.login_code_expires = None
    user.login_attempts = 0
    db.commit()

    request.session["user_id"] = user.id

    return {
        "message": "Login correcto",
        "user_id": user.id,
        "email": user.email,
        "subscription_status": user.subscription_status
    }


# ---------------- Solicitar recuperación ----------------

@router.post("/request-password-reset")
def request_password_reset(
    data: EmailRequest,
    db: Session = Depends(get_db)
):
    generic_message = (
        "Si la cuenta existe y está verificada, "
        "recibirás instrucciones por correo."
    )

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not user.email_verified:
        return {"message": generic_message}

    now = utc_now()

    if (
        user.reset_requested_at
        and now - user.reset_requested_at
        < timedelta(seconds=REQUEST_COOLDOWN_SECONDS)
    ):
        return {"message": generic_message}

    code = generate_code()

    user.reset_code = code
    user.reset_code_expires = now + timedelta(minutes=CODE_MINUTES)
    user.reset_requested_at = now
    user.reset_attempts = 0

    db.commit()

    try:
        send_password_reset_email(user.email, code)
    except Exception:
        user.reset_code = None
        user.reset_code_expires = None
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el código. Inténtalo más tarde."
        )

    return {"message": generic_message}


# ---------------- Restablecer contraseña ----------------

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not user.email_verified:
        raise HTTPException(
            status_code=400,
            detail="Código inválido o expirado"
        )

    if user.reset_attempts >= MAX_CODE_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Solicita un código nuevo más tarde."
        )

    if not code_is_valid(user.reset_code, user.reset_code_expires):
        user.reset_code = None
        user.reset_code_expires = None
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Código inválido o expirado. Solicita uno nuevo."
        )

    if not secrets.compare_digest(data.code, user.reset_code):
        user.reset_attempts += 1

        if user.reset_attempts >= MAX_CODE_ATTEMPTS:
            user.reset_code = None
            user.reset_code_expires = None

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Código inválido o expirado"
        )

    # El bloqueo se comprueba después de validar el código.
    check_password_cooldown(user)

    password_bytes = validate_new_password(
        data.new_password,
        data.confirm_password
    )

    if bcrypt.checkpw(
        password_bytes,
        user.password_hash.encode("utf-8")
    ):
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe ser diferente"
        )

    user.password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    ).decode("utf-8")

    user.password_changed_at = utc_now()
    user.reset_code = None
    user.reset_code_expires = None
    user.reset_attempts = 0

    db.commit()

    return {
        "message": (
            "Contraseña restablecida correctamente. "
            "Ya puedes iniciar sesión con tu nueva contraseña."
        )
    }


# ---------------- Usuario actual ----------------

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


# ---------------- Cerrar sesión ----------------

@router.post("/logout")
def logout(request: Request):
    request.session.clear()

    return {"message": "Sesión cerrada correctamente"}