"""Autenticacion Roble + sesiones persistidas en PostgreSQL, version de equipo local.

IMPORTANTE: Prueba local con cookies HTTP; no exponer en Internet sin HTTPS,
proteccion contra fuerza bruta, roles separados y despliegue adecuado.
"""
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from roble import RobleClient, RobleError, RobleHttpError

# La biblioteca compartida se instala con pip install -e .\backend\shared
from gestion_seguridad import conexion, exigir_usuario, obtener_sesion
from gestion_seguridad.sesiones import COOKIE_NAME, token_hash

load_dotenv(Path(__file__).with_name(".env"))
logger = logging.getLogger("gestion.auth")

ROBLE_BASE_URL = os.getenv("ROBLE_BASE_URL", "").strip()
ROBLE_CONTRACT_ID = os.getenv("ROBLE_CONTRACT_ID", "").strip()
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
SESSION_MINUTES = int(os.getenv("SESSION_MINUTES", "30"))
ORIGENES = [x.strip().rstrip("/") for x in os.getenv(
    "ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://127.0.0.1:8001"
).split(",") if x.strip()]

if not ROBLE_BASE_URL or not ROBLE_CONTRACT_ID:
    raise RuntimeError("Faltan ROBLE_BASE_URL o ROBLE_CONTRACT_ID")
if not 1 <= SESSION_MINUTES <= 1440:
    raise RuntimeError("SESSION_MINUTES debe estar entre 1 y 1440")

app = FastAPI(title="Gestion Personas - Autenticacion Roble", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


class Credenciales(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


def comprobar_origen(request: Request):
    origen = request.headers.get("origin")
    if origen and origen.rstrip("/") not in ORIGENES:
        raise HTTPException(403, "Origen no autorizado")


def evento(tipo: str, usuario_id: str | None = None):
    """No registra correo, contrasenas, codigos ni tokens en auditoria."""
    try:
        with conexion() as conn:
            conn.execute(
                "INSERT INTO public.auth_eventos (evento, usuario_roble_id) VALUES (%s, %s)",
                (tipo, UUID(usuario_id) if usuario_id else None),
            )
    except (psycopg.Error, RuntimeError, ValueError):
        logger.exception("No se pudo registrar evento de autenticacion")


@app.get("/salud")
def salud():
    return {"estado": "ok", "servicio": "autenticacion"}


@app.get("/preparado")
def preparado():
    try:
        with conexion() as conn:
            conn.execute("SELECT 1 FROM public.auth_sesiones LIMIT 1").fetchone()
            conn.execute("SELECT 1 FROM public.auth_eventos LIMIT 1").fetchone()
    except (psycopg.Error, RuntimeError) as exc:
        raise HTTPException(503, "PostgreSQL o tablas de autenticacion no disponibles") from exc
    return {"estado": "ok", "postgres": "conectado", "tablas_auth": "listas"}


@app.post("/auth/login")
def login(datos: Credenciales, request: Request, response: Response):
    comprobar_origen(request)

    try:
        # Instancia privada por solicitud, nunca compartida entre usuarios.
        with RobleClient(base_url=ROBLE_BASE_URL, contract_id=ROBLE_CONTRACT_ID) as roble:
            usuario = roble.login(
                email=datos.email.strip(),
                password=datos.password,
                persist_session=False,
            )
            identidad = {
                "user_id": str(usuario.user_id),
                "email": usuario.email,
                "name": usuario.name or "",
            }
            # Revocamos la sesion temporal en Roble. La propia sesion del sistema
            # se guardara por separado, sin exponer los tokens de Roble.
            try:
                roble.logout()
            except RobleError:
                logger.warning("Roble no confirmo el cierre de la sesion temporal")
    except RobleHttpError as exc:
        if exc.status_code == 401:
            evento("LOGIN_RECHAZADO")
            raise HTTPException(401, "Correo o contrasena incorrectos") from None
        if exc.status_code == 429:
            raise HTTPException(429, "Roble limita temporalmente los intentos") from None
        logger.warning("Roble devolvio HTTP %s", exc.status_code)
        raise HTTPException(502, "No se pudo autenticar con Roble") from None
    except RobleError:
        logger.exception("Error al autenticar con Roble")
        raise HTTPException(502, "No se pudo autenticar con Roble") from None

    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    ahora = datetime.now(timezone.utc)
    expira = ahora + timedelta(minutes=SESSION_MINUTES)
    try:
        with conexion() as conn:
            conn.execute(
                """INSERT INTO public.auth_sesiones
                       (token_hash, usuario_roble_id, correo, nombre, csrf_token,
                        creada_en, expira_en)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (token_hash(token), UUID(identidad["user_id"]),
                 identidad["email"], identidad["name"], csrf, ahora, expira),
            )
            conn.execute(
                "INSERT INTO public.auth_eventos (evento, usuario_roble_id) VALUES (%s, %s)",
                ("LOGIN_OK", UUID(identidad["user_id"])),
            )
    except (psycopg.Error, RuntimeError, ValueError) as exc:
        logger.exception("Fallo almacenamiento de sesion en PostgreSQL")
        raise HTTPException(503, "No se pudo crear la sesion") from exc

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_MINUTES * 60,
        path="/",
    )
    return {"estado": "autenticado", "usuario": identidad}


@app.get("/auth/yo")
def yo(request: Request):
    sesion = obtener_sesion(request)
    return {
        "autenticado": True,
        "usuario": {k: sesion[k] for k in ("user_id", "email", "name")},
        "csrf_token": sesion["csrf_token"],
    }


@app.get("/auth/privado")
def privado(usuario: dict = Depends(exigir_usuario)):
    """Prueba de la misma dependencia que usaran otros microservicios."""
    return {"protegido": True, "usuario": usuario}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    comprobar_origen(request)
    sesion = obtener_sesion(request)
    recibido = request.headers.get("X-CSRF-Token", "")
    if not recibido or not secrets.compare_digest(recibido, sesion["csrf_token"]):
        raise HTTPException(403, "Token CSRF invalido")

    token = request.cookies.get(COOKIE_NAME)
    try:
        with conexion() as conn:
            conn.execute(
                """UPDATE public.auth_sesiones SET revocada_en = NOW()
                   WHERE token_hash = %s AND revocada_en IS NULL""",
                (token_hash(token),),
            )
            conn.execute(
                "INSERT INTO public.auth_eventos (evento, usuario_roble_id) VALUES (%s, %s)",
                ("LOGOUT", UUID(sesion["user_id"])),
            )
    except (psycopg.Error, RuntimeError, ValueError) as exc:
        logger.exception("Fallo revocacion de sesion")
        raise HTTPException(503, "No se pudo cerrar la sesion") from exc

    response.delete_cookie(key=COOKIE_NAME, path="/", samesite="lax")
    return {"estado": "sesion_cerrada"}
