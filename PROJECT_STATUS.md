BTC Alerts — PROJECT STATUS
Última actualización: 17/09/2026
Estado: Desarrollo local
Ruta: D:\Python\BTC_Alerts
________________________________________
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
•	DELETE btc_alerts.db
•	eliminar la base de datos
•	recrearla
•	resetearla
•	reemplazarla
•	borrar registros históricos de pagos
________________________________________
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
├── payment.html
└── admin-payments.html
Recursos QR
static/qr/
├── bcp_monthly.jpg
├── bcp_semiannual.jpg
├── bcp_annual.jpg
└── bcp_lifetime.jpg
Configuración
.env
El .env contiene credenciales y NO debe publicarse en GitHub.
________________________________________
3. Autenticación
3.1 Registro
Estado: COMPLETADO Y PROBADO
Implementado:
•	Registro mediante email y contraseña
•	Hash de contraseña mediante bcrypt
•	Verificación obligatoria del email
•	Código de verificación de 6 dígitos
•	Código válido durante 15 minutos
Estado inicial:
email_verified = False
subscription_status = PENDING
subscription_expires = None
________________________________________
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
________________________________________
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
________________________________________
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
________________________________________
6. Endpoint /auth/me
Estado: COMPLETADO Y PROBADO
Endpoint:
GET /auth/me
Devuelve información del usuario autenticado:
•	user_id
•	email
•	subscription_status
•	subscription_expires
•	alerts_enabled
________________________________________
7. Dashboard
Estado: FUNCIONANDO
Página:
/dashboard
Actualmente muestra:
•	Email
•	ID de usuario
•	Estado de suscripción
•	Fecha de vencimiento
•	Estado de alertas
•	Estado de Telegram
•	Última señal BTC/USDT
•	Historial de señales
•	Señales BTC
Actualmente algunos datos todavía son de demostración.
Ejemplo:
Precio BTC: $73,025.15
Señal: ↓ BAJA
Probabilidad: 78.03%
Posteriormente deberán conectarse al sistema real de señales BTC.
________________________________________
8. Protección del Dashboard
Estado: COMPLETADO Y PROBADO
El backend verifica:
1.	Existencia de sesión
2.	Existencia del usuario
3.	Verificación del email
4.	Vencimiento de la suscripción
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
________________________________________
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
La activación se realiza mediante aprobación administrativa.
EXPIRED
La suscripción o trial ha vencido.
________________________________________
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
________________________________________
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
Configuración en:
app/main.py
Endpoint:
GET /plans
________________________________________
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
________________________________________
12.1 Modelo Payment
Archivo:
app/models.py
Campos actuales:
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
user_reported_paid
user_reported_paid_at
approved_at
Estado inicial:
PENDING
La referencia es única:
reference UNIQUE
________________________________________
12.2 Expiración de pagos
Las solicitudes de pago NO expiran automáticamente.
Si el usuario no paga:
PENDING
permanece almacenado.
El historial de pagos es permanente.
________________________________________
13. Regla de solicitudes pendientes
Estado: IMPLEMENTADO
Actualmente:
Mismo plan
Si el usuario vuelve a seleccionar el mismo plan:
PENDING existente
       ↓
Reutilizar
No se crea:
•	Nueva referencia
•	Nuevo registro
•	Nuevo pago
Cambio de plan
Actualmente el sistema todavía realiza:
PENDING anterior
       ↓
CANCELLED
       ↓
Nueva solicitud
       ↓
PENDING
Esto funcionaba correctamente en las pruebas iniciales.
Cambio necesario
Esta lógica debe modificarse porque ahora existe el estado:
user_reported_paid = True
Si el usuario ya declaró haber realizado el pago, no se debe cancelar automáticamente esa solicitud al intentar cambiar de plan.
Nuevo comportamiento pendiente
Usuario tiene PENDING
       ↓
Usuario reportó pago
       ↓
Intenta cambiar de plan
       ↓
NO cancelar automáticamente
       ↓
Mostrar advertencia
       ↓
Solicitar confirmación explícita
El usuario deberá poder indicar explícitamente que NO realizó el pago antes de liberar/cancelar esa solicitud.
________________________________________
14. Página de pago
Estado: COMPLETADA Y PROBADA
Ruta:
/subscribe/{plan_id}
Ejemplo:
/subscribe/monthly
La página muestra:
•	Nombre del plan
•	Duración
•	Precio USDT
•	Equivalente Bs
•	Referencia
•	QR
•	Estado del pago
•	Instrucciones
•	Botón Dashboard
•	Estado de confirmación del usuario
________________________________________
15. Reporte manual de pago por el usuario
Estado: COMPLETADO Y PROBADO
Se implementó el botón:
YA REALICÉ EL PAGO
El usuario puede declarar que ya realizó el pago.
Endpoint:
POST /payment/{payment_id}/report-paid
Comportamiento
Cuando el usuario pulsa el botón:
user_reported_paid = True
user_reported_paid_at = utc_now()
El pago permanece:
status = PENDING
El sistema NO aprueba automáticamente el pago.
Después del reporte:
Botón YA REALICÉ EL PAGO
        ↓
desaparece
        ↓
Mensaje:
"Has indicado que realizaste el pago.
El administrador debe verificarlo."
Prueba realizada
Pago:
ID: 3
Referencia: BPLGZY0P
Usuario: 5
Plan: monthly
Estado: PENDING
user_reported_paid: 1
user_reported_paid_at: 2026-09-17 14:10:54.887743
approved_at: None
Resultado:
Funcionando correctamente.
________________________________________
16. QR BCP
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
________________________________________
17. Pagos realizados por terceros
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
•	El usuario se identifica mediante la solicitud.
•	La referencia identifica la solicitud cuando el banco la permite.
•	El comprobante puede utilizarse para verificación manual.
•	El nombre del pagador no se utilizará como identificador automático.
________________________________________
18. Bancos evaluados
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
________________________________________
19. Base de datos
Archivo:
btc_alerts.db
Tabla users
Campos principales:
id
email
email_verified
verification_code
verification_expires
password_hash
created_at
subscription_status
subscription_started
subscription_expires
alerts_enabled
is_admin
Tabla payments
Campos actuales:
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
user_reported_paid
user_reported_paid_at
approved_at
Reglas
NO eliminar btc_alerts.db
NO recrear la base de datos
NO borrar historial de pagos
NO resetear datos durante el desarrollo
Las modificaciones de estructura se realizan mediante migraciones.
________________________________________
20. Modelo User
Archivo:
app/models.py
Estado inicial:
subscription_status = PENDING
subscription_expires = None
Después de verificar email:
subscription_status = TRIAL
subscription_expires = +3 meses
Campos adicionales actualmente implementados:
subscription_started
is_admin
________________________________________
21. Modelo Payment
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
user_reported_paid
user_reported_paid_at
approved_at
Estados utilizados actualmente:
PENDING
CANCELLED
APPROVED
La referencia es única:
reference UNIQUE
________________________________________
22. Panel administrativo
Estado: IMPLEMENTADO Y PROBADO
Página:
/admin/payments
El acceso requiere:
is_admin = True
El panel muestra actualmente:
•	Referencia
•	Usuario
•	Plan
•	Monto
•	Fecha
•	Estado
•	Si el usuario reportó el pago
•	Acción de aprobación
Ejemplo actual:
Referencia: BPLGZY0P
Usuario: daltonmax_42@hotmail.com
Plan: Mensual
Monto: 5 USDT / 60 Bs
Estado: PENDING
Usuario reportó pago: SÍ
Administrador probado
daltonmax24@gmail.com
con:
is_admin = True
________________________________________
23. Aprobación administrativa de pagos
Estado: IMPLEMENTADO Y PROBADO A NIVEL DE FLUJO
Endpoint:
POST /admin/payments/{payment_id}/approve
El endpoint verifica:
1.	Existencia de sesión.
2.	Existencia del administrador.
3.	is_admin = True.
4.	Existencia del pago.
5.	Estado PENDING.
6.	Existencia del usuario.
7.	Existencia del plan.
Al aprobar:
approved_at = utc_now()
payment.status = APPROVED
Usuario:
subscription_status = ACTIVE
subscription_started = approved_at
Duración:
Mensual      → +1 mes
Semestral    → +6 meses
Anual        → +12 meses
De por vida  → subscription_expires = None
Importante
El reporte del usuario:
user_reported_paid = True
NO equivale a aprobación administrativa.
La aprobación continúa siendo manual.
Flujo:
Usuario realiza pago
        ↓
Usuario pulsa
"YA REALICÉ EL PAGO"
        ↓
PENDING
        ↓
Administrador verifica el pago
        ↓
Administrador aprueba
        ↓
APPROVED
        ↓
Usuario = ACTIVE
________________________________________
24. Historial de pagos
Estado: PARCIALMENTE IMPLEMENTADO
La base de datos conserva permanentemente los registros.
Actualmente se conservan estados como:
PENDING
CANCELLED
APPROVED
Ejemplo real comprobado:
(3, 'BPLGZY0P', 5, 'monthly', 'PENDING', 1,
 '2026-09-17 14:10:54.887743', None)

(2, 'KLC3QN7X', 5, 'annual', 'CANCELLED', 0,
 None, None)

(1, '4KAPLZFO', 5, 'monthly', 'CANCELLED', 0,
 None, None)
Pendiente
Crear una vista administrativa completa para consultar:
•	Pagos pendientes
•	Pagos aprobados
•	Pagos cancelados
•	Usuario
•	Email
•	Plan
•	Monto
•	Referencia
•	Fecha de creación
•	Fecha de reporte
•	Fecha de aprobación
________________________________________
25. Funcionalidades completadas
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
[OK] Historial permanente
[OK] /subscribe/{plan_id}
[OK] QR BCP por plan
[OK] Visualización del QR
[OK] Reporte "YA REALICÉ EL PAGO"
[OK] Registro user_reported_paid
[OK] Registro user_reported_paid_at
[OK] Panel administrativo
[OK] Identificación de administrador
[OK] Visualización SÍ/NO de reporte de pago
[OK] Endpoint de aprobación administrativa
[OK] Activación ACTIVE al aprobar
________________________________________
26. Próximos pasos
Prioridad 1 — Protección ante cambio de plan
Estado: SIGUIENTE TAREA
Problema actual:
Usuario tiene:
PENDING + user_reported_paid = True
Si actualmente intenta seleccionar otro plan, la lógica existente puede cancelar la solicitud anterior.
Esto debe cambiar.
Nuevo flujo previsto:
Usuario
   ↓
Tiene pago PENDING
   ↓
¿Reportó pago?
   │
   ├── NO
   │     ↓
   │   Puede solicitar cambio
   │
   └── SÍ
         ↓
   No cancelar automáticamente
         ↓
   Mostrar advertencia
         ↓
   Confirmación explícita
         ↓
   Usuario confirma que NO realizó el pago
         ↓
   Cancelar solicitud
         ↓
   Permitir nuevo plan
Objetivo:
Evitar que un usuario pueda perder accidentalmente una solicitud que ya declaró como pagada.
________________________________________
Prioridad 2 — Restricción EXPIRED
Estado: PENDIENTE
Cuando:
subscription_status = EXPIRED
el usuario deberá ser dirigido a:
/plans
y no podrá utilizar funciones protegidas.
________________________________________
Prioridad 3 — Historial administrativo
Estado: PENDIENTE
Crear una vista para consultar:
Pagos pendientes
Pagos aprobados
Pagos cancelados
Usuario
Email
Plan
Monto
Referencia
Fecha de creación
Fecha de reporte
Fecha de aprobación
Los registros históricos no deben eliminarse.
________________________________________
Prioridad 4 — Email de confirmación de pago
Estado: PENDIENTE
Después de que el administrador apruebe un pago:
Payment = APPROVED
        ↓
User = ACTIVE
        ↓
Enviar email de confirmación
El correo deberá informar:
•	Plan adquirido
•	Monto
•	Fecha de activación
•	Fecha de vencimiento, cuando corresponda
________________________________________
Prioridad 5 — Pagos automáticos
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
________________________________________
Prioridad 6 — Alertas BTC reales
Estado: PENDIENTE
Sustituir los datos de demostración por:
•	Precio actual
•	Dirección de señal
•	Probabilidad
•	Fecha/hora
•	Historial real
•	Estado de alertas
________________________________________
Prioridad 7 — Telegram
Estado: PENDIENTE
Implementar:
•	Conectar Telegram
•	Vincular cuenta
•	Activar/desactivar alertas
•	Enviar alertas
•	Mostrar estado de conexión
________________________________________
27. Seguridad pendiente
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
[ ] Revisar autorización administrativa
[ ] Proteger endpoints administrativos
[ ] Revisar endpoints de pagos
________________________________________
28. Estado general del proyecto
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
│   ├── Historial permanente      ✅
│   ├── QR BCP                    ✅
│   ├── Página de pago            ✅
│   ├── Reporte usuario           ✅
│   ├── Panel administrativo      ✅
│   ├── Aprobación admin          ✅
│   ├── Activación ACTIVE         ✅
│   └── Protección cambio plan    ⏳
│
├── FUNCIONES BTC
│   ├── Datos reales              ⏳
│   ├── Alertas                   ⏳
│   └── Historial real            ⏳
│
├── TELEGRAM
│   ├── Vinculación               ⏳
│   └── Alertas                   ⏳
│
└── PRODUCCIÓN
    ├── Seguridad                ⏳
    ├── HTTPS                    ⏳
    └── Pagos automáticos        ⏳
________________________________________
29. Última prueba realizada
Usuario de prueba:
ID: 5
Email: daltonmax_42@hotmail.com
Estado conocido:
email_verified = True
subscription_status = TRIAL
subscription_expires = 2026-12-15
alerts_enabled = True
Pruebas realizadas
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
Reporte de pago usuario       ✅
Registro user_reported_paid   ✅
Panel administrativo          ✅
Aprobación administrativa     ✅
Última solicitud comprobada
ID: 3
Referencia: BPLGZY0P
Usuario: 5
Plan: monthly
Estado: PENDING
user_reported_paid: 1
user_reported_paid_at: 2026-09-17 14:10:54.887743
approved_at: None
Resultado:
Usuario reportó pago → SÍ
Administrador puede verificar → SÍ
Pago aprobado automáticamente → NO
________________________________________
30. Regla de continuidad del proyecto
Antes de realizar cambios importantes:
1.	Revisar PROJECT_STATUS.md
2.	Identificar exactamente qué se modificará
3.	Mantener intacta la base de datos
4.	No eliminar datos históricos
5.	Realizar cambios pequeños
6.	Probar cada cambio
7.	Actualizar PROJECT_STATUS.md
Regla principal
No modificar ni eliminar funcionalidades que ya fueron probadas sin necesidad.
________________________________________
31. Próximo trabajo
SIGUIENTE TAREA:
Proteger el cambio de plan cuando existe un pago reportado
Situación actual:
Usuario
   ↓
Tiene solicitud PENDING
   ↓
Pulsa "YA REALICÉ EL PAGO"
   ↓
user_reported_paid = True
   ↓
Administrador ve "SÍ"
El siguiente desarrollo debe impedir que esa solicitud sea cancelada automáticamente si el usuario intenta seleccionar otro plan.
Flujo previsto:
Usuario
  ↓
Selecciona otro plan
  ↓
Existe PENDING de otro plan
  ↓
¿user_reported_paid = True?
  │
  ├── SÍ
  │     ↓
  │   Advertencia
  │     ↓
  │   Confirmación explícita
  │     ↓
  │   "NO REALICÉ EL PAGO"
  │     ↓
  │   Cancelar solicitud
  │     ↓
  │   Crear nuevo PENDING
  │
  └── NO
        ↓
      Confirmar cambio
        ↓
      Cancelar solicitud anterior
        ↓
      Crear nuevo PENDING
No se debe eliminar ninguna solicitud histórica de la base de datos.


---

# 32. Actualización del proyecto — 13/10/2026

## 32.1 Autenticación y seguridad de cuentas

Estado: IMPLEMENTADO Y PROBADO LOCALMENTE

Se añadieron o ajustaron las siguientes funciones:

- Inicio de sesión mediante código enviado por correo.
- Recuperación de contraseña mediante código de correo.
- Cambio y restablecimiento de contraseña sujetos a una espera de 24 horas.
- Códigos con validez de 15 minutos.
- Límite de 60 segundos entre solicitudes de código.
- Máximo de 5 intentos de código.
- Reenvío de código de verificación mediante POST /auth/resend-verification.
- Botón para reenviar el código en verify-email.html.

Archivo principal:
app/auth.py

Archivos relacionados:
app/email.py
templates/login.html
templates/verify-email.html

## 32.2 Registro de cuentas existentes

Estado: IMPLEMENTADO Y PROBADO LOCALMENTE

Se modificó la función register() en app/auth.py.

Comportamiento actual:

- Correo nuevo: crea una cuenta y envía el código de verificación.
- Correo existente verificado: rechaza el registro e indica iniciar sesión o recuperar la contraseña.
- Correo existente sin verificar: reutiliza la cuenta y permite solicitar otro código respetando el límite de 60 segundos.
- No cambia la contraseña de una cuenta existente durante un nuevo intento de registro.
- No crea usuarios duplicados.
- Conserva los datos existentes de usuario y suscripción.

Comprobación:
python -m py_compile .\app\auth.py

Resultado: sin errores de sintaxis.

## 32.3 Interfaz de registro

Estado: PENDIENTE

Situación comprobada:

- Los enlaces «Registrarse» aparecen en la interfaz.
- GET /register devuelve 404.
- No existe templates/register.html.
- El registro se ha realizado mediante POST /auth/register en /docs.

Trabajo pendiente:

Crear la ruta GET /register y la plantilla de registro con:

- Nombre.
- Apellido.
- Correo electrónico.
- Contraseña.
- Confirmación de contraseña.

La interfaz debe utilizar el endpoint existente POST /auth/register y mostrar mensajes comprensibles para el usuario.

Antes de añadir nombre y apellido al modelo User, revisar app/models.py y preparar una migración compatible con la base de datos existente.

No recrear la base de datos.

## 32.4 Cuentas de prueba

Se identificaron las cuentas:

ID 1: prueba@example.com
ID 2: prueba2@example.com

Ambas eran cuentas de prueba sin pagos asociados y sin acceso a los correos.

Se eliminaron mediante una operación controlada después de comprobar que no tenían pagos asociados.

La copia de seguridad de la base de datos creada antes de esa eliminación es:

btc_alerts.before_test_cleanup.db

Se conservaron los ID restantes. No renumerar usuarios.

## 32.5 Estado de las cuentas después de la limpieza

Según el último inventario realizado:

ID 3: daltonmax29@gmail.com — verificado, TRIAL.
ID 4: daltonmax_29@hotmail.com — verificado, TRIAL.
ID 5: daltonmax_42@hotmail.com — verificado, TRIAL.
ID 6: app.btc.alerts@gmail.com — verificado, administrador, TRIAL.
ID 7: daltonmax24@gmail.com — verificado, administrador, TRIAL.
ID 8: daltonmax_24@hotmail.com — pendiente de verificación, PENDING.

Verificar nuevamente estos datos antes de realizar operaciones futuras sobre cuentas.

## 32.6 Copias de seguridad creadas

Archivo de autenticación anterior al ajuste del registro:

app/auth.py.before_register_fix.bak

Copia adicional de autenticación:

app/auth.py.before_register_fix_second.bak

Copia de la base de datos anterior a la eliminación de cuentas de prueba:

btc_alerts.before_test_cleanup.db

Copia de este documento antes de la actualización:

PROJECT_STATUS.before_2026-10-13.bak

No borrar estas copias sin una decisión explícita.

## 32.7 Próximas tareas

Prioridad funcional original:

1. Proteger el cambio de plan cuando exista un pago PENDING con user_reported_paid = True.
2. Restringir correctamente las funciones para suscripciones EXPIRED.
3. Completar el historial administrativo de pagos.
4. Enviar correo de confirmación tras la aprobación administrativa de un pago.

Siguiente mejora de interfaz:

5. Crear la página /register con nombre y apellido, correo, contraseña y confirmación.
6. Revisar el modelo User y aplicar una migración segura para los campos nuevos, si corresponde.

Mantener el orden de prioridades y no eliminar el historial de pagos.

## 32.8 Reglas de continuidad

- No eliminar ni recrear btc_alerts.db.
- No reiniciar los ID de usuarios.
- No borrar el historial de pagos.
- Crear copias de seguridad antes de cambios importantes.
- Realizar cambios pequeños y probarlos.
- Mantener las funciones previamente probadas.
- Actualizar PROJECT_STATUS.md después de cada avance importante.

