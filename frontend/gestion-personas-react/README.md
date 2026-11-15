# Interfaz de prueba: Roble + FastAPI + PostgreSQL

Interfaz React de desarrollo conectada a:

- `autenticacion` en `127.0.0.1:8001` (`/auth/login`, `/auth/yo`, `/auth/logout`).
- `consultar_persona` en `127.0.0.1:8000` (`/personas/{tipo_documento}/{numero_documento}`).

## Cómo usarla

Con PostgreSQL, túnel SSH, y los dos servicios FastAPI encendidos, desde PowerShell:

```powershell
cd 'C:\Github\PROYECTO_FINAL_DISE-O\frontend\gestion-personas-react'
npm install
npm run dev
```

Abrir **http://127.0.0.1:5173** (NO `localhost`).

1. Entrar con una cuenta del contrato Roble del proyecto, previamente registrada y verificada.
2. Consultar `Cédula` y el documento sintético `9999999999`.
3. El mensaje «Persona no encontrada» demuestra una consulta autorizada (HTTP 404); revisar el evento `CONSULTAR` con usuario `roble:...` y `ERROR` en `auditoria`.
4. Cerrar sesión y verificar que el formulario de consulta quede deshabilitado.

El proxy en `vite.config.js` transforma `/api/auth/...` en `http://127.0.0.1:8001/auth/...` y `/api/personas/...` en `http://127.0.0.1:8000/personas/...`.

No se almacena contraseña ni token de sesión en `localStorage`. La cookie `HttpOnly` es responsabilidad del backend.

**Solo desarrollo local.** No desplegar públicamente hasta tener HTTPS, controles CSRF en operaciones de escritura, limitación de intentos, autorización por roles y seguridad de producción. No usar información personal real en las pruebas.
