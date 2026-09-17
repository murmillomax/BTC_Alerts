import secrets

from dateutil.relativedelta import relativedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
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

PLANS = {
    "monthly": {
        "name": "Mensual",
        "months": 1,
        "price_usdt": 5,
        "price_bob": 60,
    },
    "semiannual": {
        "name": "Semestral",
        "months": 6,
        "price_usdt": 20,
        "price_bob": 240,
    },
    "annual": {
        "name": "Anual",
        "months": 12,
        "price_usdt": 30,
        "price_bob": 360,
    },
    "lifetime": {
        "name": "De por vida",
        "months": None,
        "price_usdt": 100,
        "price_bob": 1200,
    },
}

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


@app.get("/plans")
def get_plans():
    return PLANS

@app.get("/subscribe/{plan_id}")
def subscribe(plan_id: str, request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="No estás autenticado"
        )

    if plan_id not in PLANS:
        raise HTTPException(
            status_code=404,
            detail="Plan no encontrado"
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

        # Buscar una solicitud pendiente del mismo plan
        existing_payment = db.query(models.Payment).filter(
            models.Payment.user_id == user.id,
            models.Payment.plan_id == plan_id,
            models.Payment.status == "PENDING"
        ).order_by(
            models.Payment.id.desc()
        ).first()

        # Si ya existe, reutilizarla
        if existing_payment:
            payment = existing_payment

        else:
            # Si existe una solicitud pendiente de otro plan,
            # se cancela porque el usuario cambió de plan.
            pending_other_plan = db.query(models.Payment).filter(
                models.Payment.user_id == user.id,
                models.Payment.status == "PENDING",
                models.Payment.plan_id != plan_id
            ).all()

            for old_payment in pending_other_plan:
                old_payment.status = "CANCELLED"

            reference = None

            while reference is None:
                candidate = "".join(
                    secrets.choice(
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                    )
                    for _ in range(8)
                )

                existing_reference = db.query(
                    models.Payment
                ).filter(
                    models.Payment.reference == candidate
                ).first()

                if not existing_reference:
                    reference = candidate

            plan = PLANS[plan_id]

            payment = models.Payment(
                reference=reference,
                user_id=user.id,
                plan_id=plan_id,
                amount=plan["price_usdt"],
                currency="USDT",
                status="PENDING",
                created_at=utc_now()
            )

            db.add(payment)
            db.commit()
            db.refresh(payment)

        plan = PLANS[payment.plan_id]

        return templates.TemplateResponse(
            request=request,
            name="payment.html",
            context={
                "payment": {
                    "id": payment.id,
                    "reference": payment.reference,
                    "plan_id": payment.plan_id,
                    "plan": plan,
                    "status": payment.status,
                    "user_reported_paid": payment.user_reported_paid
                }
            }
        )

    finally:
        db.close()


@app.post("/payment/{payment_id}/report-paid")
def report_payment_paid(
    payment_id: int,
    request: Request
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="No estás autenticado"
        )

    db = SessionLocal()

    try:
        payment = db.query(models.Payment).filter(
            models.Payment.id == payment_id,
            models.Payment.user_id == user_id
        ).first()

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Pago no encontrado"
            )

        if payment.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="Este pago ya no está pendiente"
            )

        if payment.user_reported_paid:
            return RedirectResponse(
                url=f"/subscribe/{payment.plan_id}",
                status_code=303
            )

        payment.user_reported_paid = True
        payment.user_reported_paid_at = utc_now()

        db.commit()

        return RedirectResponse(
            url=f"/subscribe/{payment.plan_id}",
            status_code=303
        )

    finally:
        db.close()


@app.get("/admin/payments")
def admin_payments(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="No estás autenticado"
        )

    db = SessionLocal()

    try:
        admin = db.query(models.User).filter(
            models.User.id == user_id
        ).first()

        if not admin:
            request.session.clear()

            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )

        if not admin.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Acceso restringido a administradores"
            )

        payments = db.query(
            models.Payment,
            models.User
        ).join(
            models.User,
            models.Payment.user_id == models.User.id
        ).filter(
            models.Payment.status == "PENDING"
        ).order_by(
            models.Payment.created_at.desc()
        ).all()

        return templates.TemplateResponse(
            request=request,
            name="admin-payments.html",
            context={
                "payments": payments,
                "admin": admin,
                "plans": PLANS
            }
        )

    finally:
        db.close()


@app.post("/admin/payments/{payment_id}/approve")
def approve_payment(
    payment_id: int,
    request: Request
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="No estás autenticado"
        )

    db = SessionLocal()

    try:
        admin = db.query(models.User).filter(
            models.User.id == user_id
        ).first()

        if not admin:
            request.session.clear()

            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )

        if not admin.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Acceso restringido a administradores"
            )

        payment = db.query(models.Payment).filter(
            models.Payment.id == payment_id
        ).first()

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Pago no encontrado"
            )

        if payment.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="Este pago ya no está pendiente"
            )

        user = db.query(models.User).filter(
            models.User.id == payment.user_id
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario del pago no encontrado"
            )

        plan = PLANS.get(payment.plan_id)

        if not plan:
            raise HTTPException(
                status_code=400,
                detail="Plan no encontrado"
            )

        # El momento de aprobación es el inicio exacto
        # de la suscripción pagada.
        approved_at = utc_now()

        payment.status = "APPROVED"
        payment.approved_at = approved_at

        user.subscription_status = "ACTIVE"
        user.subscription_started = approved_at

        if plan["months"] is None:
            user.subscription_expires = None
        else:
            user.subscription_expires = (
                approved_at
                + relativedelta(months=plan["months"])
            )

        db.commit()

        return {
            "message": "Pago aprobado correctamente",
            "payment_id": payment.id,
            "reference": payment.reference,
            "user_email": user.email,
            "plan": plan["name"],
            "subscription_started": user.subscription_started,
            "subscription_expires": user.subscription_expires
        }

    finally:
        db.close()


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
