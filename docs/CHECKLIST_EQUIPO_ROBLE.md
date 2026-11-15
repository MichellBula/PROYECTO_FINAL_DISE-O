# Entrega técnica al equipo — Roble + PostgreSQL

## Estado verificado por pruebas locales (15 noviembre 2026)

- Registro y verificación de email con Roble: correcto.
- Login, consulta de perfil y logout con Roble: correctos.
- Microservicio `autenticacion` FastAPI: `GET /preparado` HTTP 200, PostgreSQL y tablas de sesión accesibles.
- Sesión persistente en PostgreSQL tras reiniciar Uvicorn: correcto.
- `consultar_persona` sin cookie: HTTP 401; auditoría `NO_AUTENTICADO` y `DENEGADO`.
- `consultar_persona` con cookie válida de Roble: HTTP 404 en documento inexistente; auditoría `roble:{id}` y `ERROR`.
- Integración React del presente paquete: **pendiente de ejecutar en el equipo principal**.

## Inicio local de cada sesión de desarrollo

1. En CotesPC encender WSL, Docker Engine y PostgreSQL, sin destruir volúmenes.
2. Desde Windows principal conectar el túnel SSH existente a `127.0.0.1:15432`.
3. Abrir terminal independiente: iniciar `autenticacion` en `127.0.0.1:8001`.
4. Abrir otra terminal: iniciar `consultar_persona` en `127.0.0.1:8000`.
5. Abrir una tercera terminal: en `frontend/gestion-personas-react`, ejecutar `npm install` (primera vez) y `npm run dev`.
6. Navegar a `http://127.0.0.1:5173` e iniciar sesión.

## Integración en nuevos servicios

- Instalar la biblioteca local `backend/shared` en cada entorno virtual.
- Para cada ruta protegida, usar `Depends(exigir_usuario)` de `gestion_seguridad`, o el middleware `proteger_app` tras revisar las rutas públicas.
- Cargar las variables PostgreSQL desde el `.env` PRIVADO de cada servicio antes de validar la sesión.
- Registrar TODAS las operaciones en `auditoria`, incluidos intentos denegados y errores. `auth_eventos` solo registra login/logout.
- No confiar en datos enviados desde React para determinar usuario/roles.

## Alta de compañeras

- Agregar como colaboradoras al repositorio GitHub (acceso autorizado).
- Cada una crea y verifica una **cuenta Roble individual** en el contrato del proyecto; no compartir cuentas.
- Si ejecutarán FastAPI contra PostgreSQL de CotesPC, cada integrante requiere clave SSH personal autorizada y su propio túnel. Deben estar en LAN o VPN autorizada.
- Compartir configuración por `.env.example`, **nunca claves privadas, secretos ni contraseñas**.
- `gestion_api` funciona en esta fase local; antes de producción, credenciales diferentes por servicio y privilegios mínimos.

## Pendientes reales del proyecto

- Implementar y proteger microservicios de CREAR, MODIFICAR, ELIMINAR, AUDITORÍA y CONSULTAS IA; asegurar contenedores independientes.
- Autorizar las operaciones por roles, aplicar límites de solicitudes y CSRF en rutas de escritura.
- Confirmar con el docente el requisito **SSO**: correo/contraseña de Roble no prueba por sí solo SSO federado.
- Contenerización individual, gateway HTTPS, pruebas de copia/restauración y flujos RAG/n8n.

## Git antes del commit

Ejecutar `git status --short`, `git check-ignore -v` para cada `.env`, y revisar `git diff --cached --name-only`. Nunca subir `.env`, `.venv`, tokens, claves SSH, respaldos SQL ni datos reales.
