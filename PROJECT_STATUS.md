BTC Alerts — PROJECT STATUS

Última actualización: 16/09/2026
Estado: Desarrollo local
Ruta: D:\Python\BTC_Alerts

1. Información general
Elemento	Valor
Proyecto	BTC Alerts
Tipo	Plataforma web de alertas de Bitcoin
Stack	Python + FastAPI + SQLite + SQLAlchemy + Jinja2
Entorno	Desarrollo local
Base de datos	btc_alerts.db
Servidor	Uvicorn
Autenticación	bcrypt + SessionMiddleware
Email	Gmail SMTP
Regla crítica de desarrollo

La base de datos existente debe conservarse.

NO hacer:

DELETE btc_alerts.db

Tampoco:

eliminar la base de datos
recrearla
resetearla
reemplazarla
borrar registros históricos de pagos
2. Arquitectura
BTC Alerts
│
├── FastAPI
├── Uvicorn
├── SQLAlchemy
├── SQLite
├── Jinja2
├── bcrypt
├── Starlette SessionMiddleware
├── python-dotenv
└── Gmail SMTP
Archivos principales
app/
├── main.py
├── auth.py
├── models.py
├── database.py
├── email.py
├── time_utils.py
└── payments/
    └── bybit.py
Templates
templates/
├── index.html
├── login.html
├── verify-email.html
├── dashboard.html
├── plans.html
└── payment.html
Recursos QR
static/qr/
├── bcp_monthly.jpg
├── bcp_semiannual.jpg
├── bcp_annual.jpg
└── bcp_lifetime.jpg
Configuración
.env

El .env contiene credenciales y NO debe publicarse en GitHub.

3. Autenticación
3.1 Registro

Estado: COMPLETADO Y PROBADO

Implementado:

Registro mediante email y contraseña
Hash de contraseña mediante bcrypt
Verificación obligatoria del email
Código de verificación de 6 dígitos
Código válido durante 15 minutos

Estado inicial del usuario:

email_verified = False
subscription_status = PENDING
subscription_expires = None
3.2 Verificación de email

Estado: COMPLETADO Y PROBADO

Endpoint:

POST /auth/verify-email

Página:

/verify-email

Flujo:

Registro
   ↓
PENDING
   ↓
Código de 6 dígitos
   ↓
Email
   ↓
/verify-email
   ↓
Código correcto
   ↓
email_verified = True
   ↓
subscription_status = TRIAL
   ↓
Trial de 3 meses

Después de verificar:

email_verified = True
subscription_status = TRIAL
subscription_expires = fecha de verificación + 3 meses
verification_code = None
verification_expires = None

La expiración del trial utiliza meses calendario mediante relativedelta.

4. Email SMTP

Estado: COMPLETADO Y PROBADO

Proveedor:

Gmail SMTP

Configuración:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM=...

Las credenciales están almacenadas en:

.env
Prueba SMTP
Conectando a Gmail SMTP...
STARTTLS correcto.
Autenticación correcta.
Correo enviado correctamente.
PRUEBA SMTP COMPLETADA.

También se comprobó el envío real de códigos de verificación.

Observación

Hotmail puede clasificar los mensajes de BTC Alerts como Spam.

El envío SMTP funciona correctamente; el problema observado corresponde a la clasificación del correo por parte del proveedor receptor.

5. Login y sesiones
5.1 Login

Estado: COMPLETADO Y PROBADO

Endpoint:

POST /auth/login

Proceso:

Email
   ↓
Buscar usuario
   ↓
Verificar contraseña con bcrypt
   ↓
Crear sesión
   ↓
Guardar user_id
5.2 Sesiones

Estado: FUNCIONANDO

Tecnología:

Starlette SessionMiddleware

La sesión almacena:

user_id

Logout:

POST /auth/logout

Al cerrar sesión:

request.session.clear()
6. Endpoint /auth/me

Estado: COMPLETADO Y PROBADO

Endpoint:

GET /auth/me

Devuelve información del usuario autenticado:

user_id
email
subscription_status
subscription_expires
alerts_enabled
7. Dashboard

Estado: FUNCIONANDO

Página:

/dashboard

Actualmente muestra:

Email
ID de usuario
Estado de suscripción
Fecha de vencimiento
Estado de alertas
Estado de Telegram
Última señal BTC/USDT
Historial de señales
Señales BTC

Actualmente algunos datos todavía son de demostración.

Ejemplo:

Precio BTC: $73,025.15
Señal: ↓ BAJA
Probabilidad: 78.03%

Posteriormente deberán conectarse al sistema real de señales BTC.

8. Protección del Dashboard

Estado: COMPLETADO Y PROBADO

El backend verifica:

1. Existencia de sesión
2. Existencia del usuario
3. Verificación del email
4. Vencimiento de la suscripción

Flujo:

/dashboard
     │
     ├── Sin sesión
     │      └── HTTP 401
     │
     └── Con sesión
            │
            ├── Usuario inexistente
            │      └── Cerrar sesión → HTTP 401
            │
            └── Usuario existente
                   │
                   ├── Email no verificado
                   │      └── verify-email.html
                   │
                   └── Email verificado
                          └── dashboard.html

Pruebas realizadas:

PENDING / email no verificado → Verificación de email
TRIAL / email verificado      → Dashboard
9. Estados de suscripción

Estados actuales:

PENDING
TRIAL
ACTIVE
EXPIRED
PENDING

Usuario registrado pero email no verificado.

TRIAL

Email verificado y trial de 3 meses activado.

ACTIVE

Suscripción de pago activa.

La activación administrativa todavía está pendiente.

EXPIRED

La suscripción o trial ha vencido.

10. Expiración de suscripciones

Estado: COMPLETADO Y PROBADO A NIVEL DE LÓGICA

La aplicación utiliza:

utc_now()

ubicado en:

app/time_utils.py

Transiciones implementadas:

TRIAL  + fecha vencida → EXPIRED
ACTIVE + fecha vencida → EXPIRED

Condición:

subscription_expires < utc_now()

si el estado actual es:

TRIAL

o:

ACTIVE
Prueba realizada
¿VENCIDA?: True
ANTES: TRIAL
DESPUES: EXPIRED

El usuario real ID 5 fue comprobado y permaneció intacto.

Pendiente
EXPIRED → /plans

Los usuarios expirados deberán ser enviados a la página de planes y no podrán utilizar las funciones protegidas.

11. Sistema de planes

Estado: COMPLETADO

Página:

/plans
Planes actuales
Plan	ID	Duración	USDT	Bs
Mensual	monthly	1 mes	5	60
Semestral	semiannual	6 meses	20	240
Anual	annual	12 meses	30	360
De por vida	lifetime	Sin vencimiento	100	1.200

Tipo de cambio utilizado:

1 USDT = 12 Bs
Configuración

Archivo:

app/main.py
PLANS = {
    "monthly": {
        "name": "Mensual",
        "months": 1,
        "price_usdt": 5,
        "price_bob": 60
    },
    "semiannual": {
        "name": "Semestral",
        "months": 6,
        "price_usdt": 20,
        "price_bob": 240
    },
    "annual": {
        "name": "Anual",
        "months": 12,
        "price_usdt": 30,
        "price_bob": 360
    },
    "lifetime": {
        "name": "De por vida",
        "months": None,
        "price_usdt": 100,
        "price_bob": 1200
    }
}

Endpoint:

GET /plans
12. Solicitudes de pago

Estado: IMPLEMENTADO Y PROBADO

Cada solicitud genera una referencia única de:

8 caracteres

Formato:

A-Z
0-9

Ejemplo:

X7K2P9QM

La referencia identifica internamente la solicitud.

12.1 Datos de payments
id
reference
user_id
plan_id
amount
currency
status
created_at
expires_at
paid_at

Estado inicial:

PENDING
12.2 Expiración de pagos

Las solicitudes de pago NO expiran automáticamente.

Si el usuario no paga:

PENDING

permanece almacenado.

El historial de pagos es permanente.

13. Regla de solicitudes pendientes

Estado: COMPLETADO Y PROBADO

Un usuario puede tener como máximo:

1 solicitud PENDING
Mismo plan

Si el usuario vuelve a seleccionar el mismo plan:

PENDING existente
       ↓
Reutilizar

No se crea:

Nueva referencia
Nuevo registro
Nuevo pago
Cambio de plan

Si el usuario selecciona otro plan:

PENDING anterior
       ↓
CANCELLED
       ↓
Nueva solicitud
       ↓
PENDING

La nueva solicitud obtiene:

Nuevo plan
Nuevo monto
Nueva referencia
Objetivo

Evitar:

múltiples pagos pendientes
referencias simultáneas
confusión entre planes
activación accidental del plan incorrecto
14. Página de pago

Estado: COMPLETADA Y PROBADA VISUALMENTE

Ruta:

/subscribe/{plan_id}

Ejemplo:

/subscribe/monthly

La página muestra:

Nombre del plan
Duración
Precio USDT
Equivalente Bs
Referencia
QR
Estado del pago
Instrucciones
Botón Dashboard

Los usuarios en TRIAL pueden acceder correctamente.

15. QR BCP

Estado: COMPLETADO Y PROBADO

Proveedor actual:

BCP

Ubicación:

D:\Python\BTC_Alerts\static\qr

Archivos:

bcp_monthly.jpg
bcp_semiannual.jpg
bcp_annual.jpg
bcp_lifetime.jpg

Correspondencia:

monthly
    → /static/qr/bcp_monthly.jpg

semiannual
    → /static/qr/bcp_semiannual.jpg

annual
    → /static/qr/bcp_annual.jpg

lifetime
    → /static/qr/bcp_lifetime.jpg

La selección se realiza automáticamente mediante:

plan_id

El QR se muestra alineado a la izquierda dentro de la tarjeta de pago.

Limitación

El QR BCP no permite introducir nuestra referencia de 8 caracteres como referencia editable.

Por lo tanto:

Referencia BTC Alerts
        ↓
Identificador interno
16. Pagos realizados por terceros

El sistema debe permitir:

Usuario A
    ↓
Genera solicitud
    ↓
Referencia X7K2P9QM
    ↓
Persona B realiza el pago
    ↓
Administrador verifica
    ↓
Usuario A recibe la suscripción

El pagador no tiene que ser el propietario de la cuenta.

Por esta razón:

El usuario se identifica mediante la solicitud.
La referencia identifica la solicitud cuando el banco la permite.
El comprobante puede utilizarse para verificación manual.
El nombre del pagador no se utilizará como identificador automático.
17. Bancos evaluados
Banco Ganadero

Estado: EVALUADO

Permite introducir una referencia durante el pago.

Puede utilizarse la referencia de BTC Alerts:

X7K2P9QM

Actualmente no está integrado en la página de pago.

Banco Bisa

Estado: EVALUADO

El flujo probado no permite introducir una referencia personalizada.

Por lo tanto, la referencia no puede ser el único mecanismo de identificación.

La comprobación deberá realizarse mediante:

Pago recibido
+
Comprobante
+
Datos de la transacción
18. Base de datos

Archivo:

btc_alerts.db
Tabla users
id
email
email_verified
verification_code
verification_expires
password_hash
created_at
subscription_status
subscription_expires
alerts_enabled
Tabla payments
id
reference
user_id
plan_id
amount
currency
status
created_at
expires_at
paid_at
Reglas
NO eliminar btc_alerts.db
NO recrear la base de datos
NO borrar historial de pagos
NO resetear datos durante el desarrollo
19. Modelo User

Archivo:

app/models.py

Estado inicial:

subscription_status = PENDING
subscription_expires = None

Después de verificar email:

subscription_status = TRIAL
subscription_expires = +3 meses
20. Modelo Payment

Archivo:

app/models.py

Modelo:

Payment

Campos:

id
reference
user_id
plan_id
amount
currency
status
created_at
expires_at
paid_at

Estado inicial:

PENDING

La referencia es única:

reference UNIQUE
21. Funcionalidades completadas
[OK] FastAPI
[OK] SQLite
[OK] SQLAlchemy
[OK] Registro
[OK] bcrypt
[OK] Login
[OK] Logout
[OK] Sesiones
[OK] /auth/me
[OK] Código de verificación de 6 dígitos
[OK] Expiración del código a 15 minutos
[OK] Gmail SMTP
[OK] Envío real de emails
[OK] /verify-email
[OK] Verificación de email
[OK] PENDING → TRIAL
[OK] Trial de 3 meses
[OK] Protección del dashboard
[OK] UTC centralizado
[OK] Detección de vencimiento
[OK] TRIAL → EXPIRED
[OK] ACTIVE → EXPIRED
[OK] /plans
[OK] 4 planes
[OK] Solicitudes de pago
[OK] Referencia única de 8 caracteres
[OK] Estado PENDING
[OK] Reutilización de PENDING
[OK] Cancelación al cambiar de plan
[OK] Historial permanente
[OK] /subscribe/{plan_id}
[OK] QR BCP por plan
[OK] Visualización del QR
[OK] Pruebas visuales de página de pago
22. Próximos pasos
Prioridad 1 — Confirmación administrativa de pagos

Estado: PENDIENTE

Crear una interfaz administrativa donde el administrador introduzca:

Referencia de 8 caracteres

El sistema debe mostrar:

Usuario
Email
Plan
Monto
Moneda
Referencia
Estado

Antes de confirmar.

Confirmación

Después de verificar manualmente el pago:

Payment.status = PAID
Payment.paid_at = utc_now()

Usuario:

subscription_status = ACTIVE
Duración
Mensual      → +1 mes
Semestral    → +6 meses
Anual        → +12 meses
De por vida  → subscription_expires = None

Importante: el mecanismo de autorización del administrador todavía debe definirse. No existe actualmente un sistema administrativo implementado.

Prioridad 2 — Restricción EXPIRED

Estado: PENDIENTE

Cuando:

subscription_status = EXPIRED

el usuario deberá ser dirigido a:

/plans

y no podrá utilizar funciones protegidas.

Prioridad 3 — Historial administrativo

Estado: PENDIENTE

Crear una vista para consultar:

Pagos pendientes
Pagos pagados
Pagos cancelados
Usuario
Email
Plan
Monto
Referencia
Fecha de creación
Fecha de pago

Los registros históricos no deben eliminarse.

Prioridad 4 — Pagos automáticos

Estado: PENDIENTE

Después de validar completamente el sistema manual:

Evaluar proveedor
       ↓
Evaluar QR con referencia/glosa
       ↓
Evaluar webhooks
       ↓
Evaluar Bybit
       ↓
Automatizar confirmación

La integración automática no debe implementarse antes de validar el flujo manual.

Prioridad 5 — Alertas BTC reales

Estado: PENDIENTE

Sustituir los datos de demostración por:

Precio actual
Dirección de señal
Probabilidad
Fecha/hora
Historial real
Estado de alertas
Prioridad 6 — Telegram

Estado: PENDIENTE

Implementar:

Conectar Telegram
Vincular cuenta
Activar/desactivar alertas
Enviar alertas
Mostrar estado de conexión
23. Seguridad pendiente

Antes de producción:

[ ] Mover SessionMiddleware.secret_key a .env
[ ] Generar clave secreta segura
[ ] Mantener .env fuera de GitHub
[ ] Configurar HTTPS
[ ] Revisar cookies de sesión
[ ] Revisar protección CSRF
[ ] Limitar intentos de login
[ ] Implementar recuperación de contraseña
[ ] Revisar seguridad del email verification
[ ] Implementar autorización administrativa
[ ] Proteger endpoints administrativos
[ ] Revisar endpoints de pagos
24. Estado general del proyecto
BTC Alerts
│
├── AUTENTICACIÓN
│   ├── Registro                  ✅
│   ├── Email verification        ✅
│   ├── SMTP                      ✅
│   ├── Login                     ✅
│   ├── Logout                    ✅
│   └── Sessions                  ✅
│
├── USUARIOS
│   ├── /auth/me                  ✅
│   ├── Dashboard                 ✅
│   ├── Protección dashboard      ✅
│   ├── Trial 3 meses             ✅
│   └── Expiración                ✅
│
├── SUSCRIPCIONES
│   ├── Estados                   ✅
│   ├── Planes                    ✅
│   ├── TRIAL → EXPIRED           ✅
│   ├── ACTIVE → EXPIRED          ✅
│   └── EXPIRED → /plans          ⏳
│
├── PAGOS
│   ├── Solicitudes               ✅
│   ├── Referencia 8 caracteres   ✅
│   ├── PENDING                   ✅
│   ├── Reutilización             ✅
│   ├── Cancelación por cambio    ✅
│   ├── Historial permanente      ✅
│   ├── QR BCP                    ✅
│   ├── Página de pago            ✅
│   ├── Confirmación admin        ⏳
│   └── Activación ACTIVE         ⏳
│
├── FUNCIONES BTC
│   ├── Datos reales              ⏳
│   ├── Alertas                   ⏳
│   └── Historial real            ⏳
│
├── TELEGRAM
│   ├── Vinculación                ⏳
│   └── Alertas                    ⏳
│
└── PRODUCCIÓN
    ├── Seguridad                  ⏳
    ├── HTTPS                      ⏳
    └── Pagos automáticos          ⏳
25. Última prueba realizada

Usuario de prueba:

ID: 5
Email: daltonmax_42@hotmail.com

Estado:

email_verified = True
subscription_status = TRIAL
subscription_expires = 2026-12-15
alerts_enabled = True

Pruebas realizadas:

Login                         ✅
/auth/me                      ✅
/dashboard                    ✅
Protección PENDING            ✅
Verificación email            ✅
Trial 3 meses                 ✅
Detección EXPIRED             ✅
/plans                        ✅
Creación solicitud de pago    ✅
Referencia 8 caracteres       ✅
Reutilización PENDING         ✅
Cambio de plan                ✅
Cancelación PENDING           ✅
/subscribe/monthly            ✅
QR BCP mensual                ✅
QR BCP por plan               ✅
Visualización QR              ✅
26. Regla de continuidad del proyecto

Antes de realizar cambios importantes:

1. Revisar PROJECT_STATUS.md
2. Identificar exactamente qué se modificará
3. Mantener intacta la base de datos
4. No eliminar datos históricos
5. Realizar cambios pequeños
6. Probar cada cambio
7. Actualizar PROJECT_STATUS.md
Regla principal

No modificar ni eliminar funcionalidades que ya fueron probadas sin necesidad.

27. Próximo trabajo
SIGUIENTE TAREA:

Implementar confirmación administrativa de pagos.

Flujo previsto:

Admin
  ↓
Introduce referencia
  ↓
Buscar Payment
  ↓
Mostrar datos del pago
  ↓
Verificar manualmente
  ↓
Confirmar
  ↓
Payment = PAID
  ↓
User = ACTIVE
  ↓
Calcular vencimiento

Estado actual del proyecto:

Sistema de registro       → COMPLETADO
Sistema de suscripción    → COMPLETADO
Sistema de solicitudes    → COMPLETADO
Sistema QR                → COMPLETADO
Confirmación de pagos     → SIGUIENTE TAREA