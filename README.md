# BTC Alerts — Estado del proyecto

**Fecha:** 13-09-2026

## 1. Estado actual

**Proyecto:** `D:\Python\BTC_Alerts`

Actualmente se encuentra implementado y funcionando:

* FastAPI configurado y funcionando.
* SQLite configurado y funcionando.
* Sistema de registro de usuarios.
* Sistema de inicio y cierre de sesión.
* Dashboard de usuario.
* Sistema de sesiones mediante `SessionMiddleware`.
* Contraseñas protegidas mediante `bcrypt`.
* Generación automática de códigos de verificación de 6 dígitos.
* Código de verificación con una validez de 15 minutos.
* Los datos de verificación se almacenan correctamente en la base de datos.
* Los nuevos usuarios se registran inicialmente con estado `PENDING`.
* El período de prueba de 3 meses todavía no se activa durante el registro.

## 2. Usuario de prueba actual

Usuario:

```text
Email: prueba2@example.com
```

Estado actual:

```text
Código de verificación: 010152
Verificación de email: Pendiente
Suscripción: PENDING
Trial: No iniciado
```

> Este usuario es únicamente un usuario de prueba del entorno local.

## 3. Próximo paso

Configurar **Gmail SMTP** para enviar automáticamente al usuario el código de verificación generado durante el registro.

Después se implementará la verificación completa del correo electrónico.

## 4. Flujo previsto de registro y suscripción

```text
Registro del usuario
        ↓
Generación del código de verificación
        ↓
Envío del código por email
        ↓
Usuario introduce el código
        ↓
Email verificado
        ↓
Activación del TRIAL de 3 meses
        ↓
Acceso al Dashboard
        ↓
Planes de suscripción
        ↓
Plan mensual / Plan trimestral
        ↓
Integración de pagos
```

## 5. Período de prueba

El período de prueba será de **3 meses**.

El trial comenzará **únicamente después de que el usuario verifique correctamente su dirección de email**.

Antes de la verificación:

```text
subscription_status = PENDING
subscription_expires = NULL
```

Después de la verificación:

```text
email_verified = TRUE
subscription_status = TRIAL
subscription_expires = fecha de verificación + 3 meses
```

## 6. Base de datos

La base de datos actual debe conservarse.

**No borrar, eliminar ni recrear `btc_alerts.db`.**

La base de datos contiene actualmente los datos utilizados durante el desarrollo y las pruebas.

## 7. Archivos que NO deben subirse a GitHub

Los siguientes archivos y carpetas deben permanecer fuera del repositorio:

```text
.env
btc_alerts.db
.venv/
```

### `.env`

Se utilizará posteriormente para almacenar información sensible, como:

* Credenciales SMTP de Gmail.
* Claves secretas de la aplicación.
* API keys.
* Otras variables sensibles de configuración.

### `btc_alerts.db`

Contiene la base de datos local y datos de usuarios. No debe publicarse en GitHub.

### `.venv/`

Es el entorno virtual de Python utilizado únicamente en el equipo local.

## 8. Continuidad del proyecto

Cuando se retome el desarrollo, continuar desde:

**Configuración de Gmail SMTP y envío automático del código de verificación.**

No repetir pasos ya completados y **no recrear la base de datos existente**.

La frase de continuidad es:

> **"Continuemos con BTC_Alerts."**
