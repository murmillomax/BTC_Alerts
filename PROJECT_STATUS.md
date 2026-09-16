BTC Alerts — PROJECT STATUS

1. Estado del proyecto

Proyecto: BTC Alerts
Tipo: Plataforma web de alertas de Bitcoin
Stack: Python + FastAPI + SQLite + SQLAlchemy + Jinja2
Entorno actual: Desarrollo local
Ruta local:

D:\Python\BTC_Alerts

2. Arquitectura actual

La aplicación utiliza:

FastAPI

Uvicorn

SQLAlchemy

SQLite

Jinja2

bcrypt

Starlette SessionMiddleware

python-dotenv

SMTP Gmail para envío de correos

Base de datos:

btc_alerts.db

IMPORTANTE: btc_alerts.db no debe eliminarse, recrearse, resetearse ni reemplazarse durante el desarrollo.

3. Autenticación

Registro

Estado: COMPLETADO

Implementado:

Registro mediante email y contraseña.

Contraseña almacenada mediante hash bcrypt.

Verificación de email obligatoria.

Generación automática de código de verificación de 6 dígitos.

Código válido durante 15 minutos.

Usuario creado inicialmente con:

email_verified = False
subscription_status = PENDING

Verificación de email

Estado: COMPLETADO Y PROBADO

Endpoint:

POST /auth/verify-email

Página web:

/verify-email

Proceso:

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

Al verificar correctamente:

email_verified = True
subscription_status = TRIAL
subscription_expires = fecha de verificación + 3 meses
verification_code = None
verification_expires = None

La fecha de expiración del trial utiliza meses calendario mediante relativedelta.

4. Email SMTP

Estado: COMPLETADO Y PROBADO

Proveedor actual:

Gmail SMTP

Configuración:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM=...

Las credenciales se encuentran en:

.env

El archivo .env no debe publicarse en GitHub.

SMTP probado correctamente:

Conectando a Gmail SMTP...
STARTTLS correcto.
Autenticación correcta.
Correo enviado correctamente.
PRUEBA SMTP COMPLETADA.

Se comprobó posteriormente el envío real de códigos de verificación.

Observación

Hotmail puede clasificar el correo de BTC Alerts como Spam.

Esto no representa actualmente un fallo del sistema SMTP: el correo fue recibido correctamente en la carpeta Spam.

5. Login

Estado: COMPLETADO Y PROBADO

Endpoint:

POST /auth/login

La autenticación:

Busca el usuario por email.

Comprueba la contraseña mediante bcrypt.

Crea la sesión mediante SessionMiddleware.

Guarda user_id en la sesión.

Prueba realizada correctamente.

Respuesta:

{
  "message": "Login correcto",
  "user_id": 5,
  "email": "daltonmax_42@hotmail.com",
  "subscription_status": "TRIAL"
}

6. Sesiones

Estado: FUNCIONANDO

Actualmente se utiliza:

Starlette SessionMiddleware

La sesión almacena:

user_id

Logout:

POST /auth/logout

Al cerrar sesión:

request.session.clear()

7. Endpoint /auth/me

Estado: COMPLETADO Y PROBADO

Endpoint:

GET /auth/me

Devuelve actualmente:

{
  "user_id": 5,
  "email": "daltonmax_42@hotmail.com",
  "subscription_status": "TRIAL",
  "subscription_expires": "2026-12-15T17:50:44.089681",
  "alerts_enabled": true
}

8. Dashboard

Estado: FUNCIONANDO

Página:

/dashboard

El dashboard actualmente muestra:

Email del usuario

ID del usuario

Estado de suscripción

Fecha de vencimiento

Estado de alertas

Estado de Telegram

Última señal BTC/USDT

Historial de señales

Actualmente algunos datos de señales todavía son datos de demostración.

Ejemplo actual:

Precio BTC: $73,025.15
Señal: ↓ BAJA
Probabilidad: 78.03%

Estos datos deberán posteriormente conectarse con el sistema real de señales BTC.

9. Protección del Dashboard

Estado: COMPLETADO Y PROBADO

El backend ya verifica la sesión y consulta al usuario en la base de datos antes de entregar el dashboard.

Flujo actual:

/dashboard
      ↓
¿Existe sesión?
      │
      ├── NO → HTTP 401
      │
      └── SÍ
           ↓
     ¿Existe usuario?
           │
           ├── NO → cerrar sesión → HTTP 401
           │
           └── SÍ
                ↓
        ¿Email verificado?
                │
                ├── NO → verify-email.html
                │
                └── SÍ → dashboard.html

Prueba realizada con usuario no verificado:

email_verified = False
subscription_status = PENDING

Resultado:

/dashboard
      ↓
Verifica tu email

Prueba realizada con usuario verificado:

email_verified = True
subscription_status = TRIAL

Resultado:

/dashboard
      ↓
Dashboard correctamente

10. Estados actuales de suscripción

Estados definidos:

PENDING
TRIAL
ACTIVE
EXPIRED

PENDING

Usuario registrado pero email todavía no verificado.

TRIAL

Email verificado y período de prueba de 3 meses activado. Tiene acceso al dashboard mientras no haya vencido.

ACTIVE

Estado previsto para una suscripción de pago activa. La activación mediante pagos todavía no está implementada.

EXPIRED

Cuando subscription_expires ha pasado y el estado es TRIAL o ACTIVE, el backend cambia automáticamente el estado a EXPIRED.

11. Validación de vencimiento de suscripción

Estado: COMPLETADO Y PROBADO A NIVEL DE LÓGICA

El backend comprueba la sesión, la existencia del usuario, el email verificado y la fecha de vencimiento usando utc_now().

Lógica implementada:

TRIAL + fecha vencida → EXPIRED
ACTIVE + fecha vencida → EXPIRED

La transición se ejecuta cuando subscription_expires < utc_now() y el estado actual es TRIAL o ACTIVE.

Prueba realizada

Se comprobó la transición:

¿VENCIDA?: True
ANTES: TRIAL
DESPUES: EXPIRED

El usuario real ID 5 fue comprobado y permaneció intacto.

Próxima mejora

Restringir el acceso de los usuarios EXPIRED y dirigirlos a la página de planes.

12. Base de datos

Archivo:

btc_alerts.db

Tabla principal:

users

Campos actuales:

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

No realizar:

DELETE btc_alerts.db

No recrear la base de datos para resolver problemas de desarrollo.

13. Modelo User

Archivo:

app/models.py

Estado actual:

subscription_status
default = "PENDING"

El cambio fue realizado para que nuevos usuarios comiencen correctamente en estado:

PENDING

El registro actualmente establece explícitamente:

subscription_status = "PENDING"
subscription_expires = None

Después de verificar el email:

subscription_status = "TRIAL"
subscription_expires = +3 meses

14. Archivos principales

Backend

app/main.py
app/auth.py
app/models.py
app/database.py
app/email.py
app/time_utils.py

Templates

templates/index.html
templates/login.html
templates/verify-email.html
templates/dashboard.html

Configuración

.env

Base de datos

btc_alerts.db

15. Funciones completadas

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
[OK] SMTP Gmail
[OK] Envío real de emails
[OK] Página /verify-email
[OK] Verificación de email
[OK] PENDING → TRIAL
[OK] Trial de 3 meses
[OK] Protección del dashboard para emails no verificados
[OK] Dashboard para usuarios verificados
[OK] UTC centralizado mediante app/time_utils.py
[OK] Detección automática de vencimiento
[OK] TRIAL → EXPIRED
[OK] ACTIVE → EXPIRED (lógica implementada)

16. Próximos pasos

Prioridad 1 — Página de planes

Definir e implementar:

PENDING
TRIAL
ACTIVE
EXPIRED

y las reglas de acceso correspondientes.

Especialmente:

subscription_expires < fecha actual

→ suscripción vencida.

Prioridad 2 — Planes

Implementar página de planes:

/plans

Definir:

Trial

Plan mensual

Plan anual

Precio

Duración

Estado de suscripción

Prioridad 3 — Pagos

Definir posteriormente el sistema de pagos y la activación automática de:

ACTIVE

Prioridad 4 — Alertas BTC

Conectar el dashboard con el sistema real de señales BTC.

Actualmente la señal mostrada en el dashboard es estática/de demostración.

Debe sustituirse posteriormente por:

Precio actual

Dirección de señal

Probabilidad

Fecha/hora

Historial real

Estado de alertas

Prioridad 5 — Telegram

Implementar:

Conectar Telegram

y posteriormente:

Vinculación de cuenta

Activación/desactivación

Envío de alertas

Estado de conexión

17. Seguridad pendiente

Antes de producción:

Mover SessionMiddleware.secret_key a .env.

Utilizar una clave secreta segura.

Mantener .env fuera de GitHub.

Revisar configuración HTTPS.

Revisar cookies de sesión.

Revisar protección CSRF donde corresponda.

Revisar límites de intentos de login.

Revisar recuperación de contraseña.

Revisar seguridad del sistema de verificación de email.

18. Estado actual resumido

BTC Alerts
│
├── Registro                  ✅
├── Email verification       ✅
├── SMTP                      ✅
├── Login                     ✅
├── Logout                    ✅
├── Sessions                  ✅
├── Dashboard                 ✅
├── Protección dashboard      ✅
│
├── Estados de suscripción   ✅
├── UTC centralizado         ✅
├── Expiración suscripción   ✅
├── Planes                    ⏳ PENDIENTE
├── Pagos                     ⏳ PENDIENTE
├── Alertas reales            ⏳ PENDIENTE
├── Telegram                  ⏳ PENDIENTE
└── Seguridad producción      ⏳ PENDIENTE

19. Última prueba realizada

Usuario de prueba:

ID: 5
Email: daltonmax_42@hotmail.com

Estado después de verificación:

email_verified = True
subscription_status = TRIAL
subscription_expires = 2026-12-15
alerts_enabled = True

Resultado:

Login                 ✅
/auth/me              ✅
/dashboard            ✅
Protección PENDING    ✅
Verificación email    ✅
Trial 3 meses         ✅
Detección EXPIRED     ✅

20. Regla de continuidad del proyecto

No modificar ni eliminar funcionalidades que ya fueron probadas sin necesidad.

Antes de realizar cambios importantes:

Revisar este PROJECT_STATUS.md.

Identificar exactamente qué parte se va a modificar.

Mantener intacta la base de datos existente.

Probar el cambio.

Actualizar este documento con el nuevo estado.

Última actualización: 16/09/2026