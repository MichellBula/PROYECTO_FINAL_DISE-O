"""
Autenticación con Roble y sesiones persistidas en PostgreSQL.

Funciones principales:
- Inicio de sesión mediante Roble.
- Registro y verificación de correo.
- Creación automática de perfiles.
- Asignación del rol CONSULTA por defecto.
- Administración de sesiones.
- Cierre de sesión.

IMPORTANTE:
En producción debe utilizarse HTTPS y configurarse
COOKIE_SECURE=true.
"""

import logging
import os
import secrets

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import psycopg

from dotenv import load_dotenv

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from roble import RobleClient, RobleError, RobleHttpError

from gestion_seguridad import (
    conexion,
    exigir_usuario,
    obtener_sesion,
)

from gestion_seguridad.sesiones import (
    COOKIE_NAME,
    token_hash,
)

# Importamos las rutas creadas en registro.py
from registro import router as registro_router
from roles import router as roles_router

# =====================================================
# 1. CONFIGURACIÓN
# =====================================================

load_dotenv(Path(__file__).with_name(".env"))

logger = logging.getLogger("gestion.auth")

ROBLE_BASE_URL = os.getenv(
    "ROBLE_BASE_URL", ""
).strip()

ROBLE_CONTRACT_ID = os.getenv(
    "ROBLE_CONTRACT_ID", ""
).strip()

COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false").lower()
    == "true"
)

SESSION_MINUTES = int(
    os.getenv("SESSION_MINUTES", "30")
)

ORIGENES = [
    origen.strip().rstrip("/")
    for origen in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://127.0.0.1:8001"
    ).split(",")
    if origen.strip()
]

if not ROBLE_BASE_URL or not ROBLE_CONTRACT_ID:
    raise RuntimeError(
        "Faltan ROBLE_BASE_URL o ROBLE_CONTRACT_ID"
    )

if not 1 <= SESSION_MINUTES <= 1440:
    raise RuntimeError(
        "SESSION_MINUTES debe estar entre 1 y 1440"
    )


# =====================================================
# 2. APLICACIÓN FASTAPI
# =====================================================

app = FastAPI(
    title="Gestion Personas - Autenticacion Roble",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Content-Type",
        "X-CSRF-Token",
    ],
)


# =====================================================
# 3. CONECTAR REGISTRO Y VERIFICACIÓN
# =====================================================

app.include_router(registro_router)
app.include_router(roles_router)
# =====================================================
# 4. MODELOS DE DATOS
# =====================================================

class Credenciales(BaseModel):

    email: str = Field(
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        min_length=1,
        max_length=1024,
    )


# =====================================================
# 5. VALIDACIONES DE SEGURIDAD
# =====================================================

def comprobar_origen(request: Request):

    origen = request.headers.get("origin")

    if origen and origen.rstrip("/") not in ORIGENES:

        raise HTTPException(
            status_code=403,
            detail="Origen no autorizado",
        )


# =====================================================
# 6. REGISTRAR EVENTOS DE AUTENTICACIÓN
# =====================================================

def evento(
    tipo: str,
    usuario_id: str | None = None,
):

    """
    Registra eventos de autenticación sin guardar
    contraseñas, tokens ni códigos de verificación.
    """

    try:

        with conexion() as conn:

            conn.execute(
                """
                INSERT INTO public.auth_eventos
                    (evento, usuario_roble_id)
                VALUES (%s, %s)
                """,
                (
                    tipo,
                    UUID(usuario_id)
                    if usuario_id
                    else None,
                ),
            )

    except (
        psycopg.Error,
        RuntimeError,
        ValueError,
    ):

        logger.exception(
            "No se pudo registrar evento de autenticación"
        )


# =====================================================
# 7. ESTADO DEL MICROSERVICIO
# =====================================================

@app.get("/salud")
def salud():

    return {
        "estado": "ok",
        "servicio": "autenticacion",
    }


@app.get("/preparado")
def preparado():

    try:

        with conexion() as conn:

            conn.execute(
                "SELECT 1 FROM public.auth_sesiones LIMIT 1"
            ).fetchone()

            conn.execute(
                "SELECT 1 FROM public.auth_eventos LIMIT 1"
            ).fetchone()

            conn.execute(
                "SELECT 1 FROM public.auth_perfiles LIMIT 1"
            ).fetchone()

    except (
        psycopg.Error,
        RuntimeError,
    ) as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "PostgreSQL o tablas de autenticación "
                "no disponibles"
            ),
        ) from exc

    return {
        "estado": "ok",
        "postgres": "conectado",
        "tablas_auth": "listas",
    }


# =====================================================
# 8. INICIAR SESIÓN CON ROBLE
# =====================================================

@app.post("/auth/login")
def login(
    datos: Credenciales,
    request: Request,
    response: Response,
):

    comprobar_origen(request)

    # -------------------------------------------------
    # 8.1. AUTENTICACIÓN EN ROBLE
    # -------------------------------------------------

    try:

        with RobleClient(
            base_url=ROBLE_BASE_URL,
            contract_id=ROBLE_CONTRACT_ID,
        ) as roble:

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

            try:

                roble.logout()

            except RobleError:

                logger.warning(
                    "Roble no confirmó el cierre "
                    "de la sesión temporal"
                )

    except RobleHttpError as exc:

        if exc.status_code == 401:

            evento("LOGIN_RECHAZADO")

            raise HTTPException(
                status_code=401,
                detail="Correo o contraseña incorrectos",
            ) from None

        if exc.status_code == 429:

            raise HTTPException(
                status_code=429,
                detail=(
                    "Roble limita temporalmente "
                    "los intentos"
                ),
            ) from None

        logger.warning(
            "Roble devolvió HTTP %s",
            exc.status_code,
        )

        raise HTTPException(
            status_code=502,
            detail="No se pudo autenticar con Roble",
        ) from None

    except RobleError:

        logger.exception(
            "Error al autenticar con Roble"
        )

        raise HTTPException(
            status_code=502,
            detail="No se pudo autenticar con Roble",
        ) from None

    # -------------------------------------------------
    # 8.2. GENERACIÓN DE SESIÓN
    # -------------------------------------------------

    token = secrets.token_urlsafe(32)

    csrf = secrets.token_urlsafe(32)

    ahora = datetime.now(timezone.utc)

    expira = ahora + timedelta(
        minutes=SESSION_MINUTES
    )

    # -------------------------------------------------
    # 8.3. CREACIÓN O ACTUALIZACIÓN DEL PERFIL
    # -------------------------------------------------

    try:

        with conexion() as conn:

            perfil = conn.execute(
                """
                INSERT INTO public.auth_perfiles (
                    usuario_roble_id,
                    correo,
                    nombre
                )
                VALUES (%s, %s, %s)

                ON CONFLICT (usuario_roble_id)
                DO UPDATE SET
                    correo = EXCLUDED.correo,
                    nombre = EXCLUDED.nombre,
                    actualizado_en = NOW()

                RETURNING rol, activo
                """,
                (
                    UUID(identidad["user_id"]),
                    identidad["email"],
                    identidad["name"],
                ),
            ).fetchone()

            # -----------------------------------------
            # VERIFICAR SI EL PERFIL ESTÁ ACTIVO
            # -----------------------------------------

            if not perfil["activo"]:

                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Tu cuenta no tiene acceso "
                        "al sistema"
                    ),
                )

            # Incorporamos el rol del usuario
            identidad["rol"] = perfil["rol"]

            # -----------------------------------------
            # GUARDAR SESIÓN
            # -----------------------------------------

            conn.execute(
                """
                INSERT INTO public.auth_sesiones (
                    token_hash,
                    usuario_roble_id,
                    correo,
                    nombre,
                    csrf_token,
                    creada_en,
                    expira_en
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    token_hash(token),
                    UUID(identidad["user_id"]),
                    identidad["email"],
                    identidad["name"],
                    csrf,
                    ahora,
                    expira,
                ),
            )

            # -----------------------------------------
            # REGISTRAR LOGIN EXITOSO
            # -----------------------------------------

            conn.execute(
                """
                INSERT INTO public.auth_eventos (
                    evento,
                    usuario_roble_id
                )
                VALUES (%s, %s)
                """,
                (
                    "LOGIN_OK",
                    UUID(identidad["user_id"]),
                ),
            )

    except (
        psycopg.Error,
        RuntimeError,
        ValueError,
    ) as exc:

        logger.exception(
            "Falló el almacenamiento de la sesión"
        )

        raise HTTPException(
            status_code=503,
            detail="No se pudo crear la sesión",
        ) from exc

    # -------------------------------------------------
    # 8.4. ENVIAR COOKIE AL NAVEGADOR
    # -------------------------------------------------

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_MINUTES * 60,
        path="/",
    )

    return {
        "estado": "autenticado",
        "usuario": identidad,
    }


# =====================================================
# 9. CONSULTAR SESIÓN ACTUAL
# =====================================================

@app.get("/auth/yo")
def yo(request: Request):

    sesion = obtener_sesion(request)

    return {
        "autenticado": True,
        "usuario": {
            clave: sesion[clave]
            for clave in (
                "user_id",
                "email",
                "name",
            )
        },
        "csrf_token": sesion["csrf_token"],
    }


# =====================================================
# 10. RUTA PRIVADA DE PRUEBA
# =====================================================

@app.get("/auth/privado")
def privado(
    usuario: dict = Depends(exigir_usuario),
):

    return {
        "protegido": True,
        "usuario": usuario,
    }


# =====================================================
# 11. CERRAR SESIÓN
# =====================================================

@app.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
):

    comprobar_origen(request)

    sesion = obtener_sesion(request)

    recibido = request.headers.get(
        "X-CSRF-Token", ""
    )

    if (
        not recibido
        or not secrets.compare_digest(
            recibido,
            sesion["csrf_token"],
        )
    ):

        raise HTTPException(
            status_code=403,
            detail="Token CSRF inválido",
        )

    token = request.cookies.get(COOKIE_NAME)

    try:

        with conexion() as conn:

            conn.execute(
                """
                UPDATE public.auth_sesiones

                SET revocada_en = NOW()

                WHERE token_hash = %s

                AND revocada_en IS NULL
                """,
                (token_hash(token),),
            )

            conn.execute(
                """
                INSERT INTO public.auth_eventos (
                    evento,
                    usuario_roble_id
                )
                VALUES (%s, %s)
                """,
                (
                    "LOGOUT",
                    UUID(sesion["user_id"]),
                ),
            )

    except (
        psycopg.Error,
        RuntimeError,
        ValueError,
    ) as exc:

        logger.exception(
            "Falló la revocación de sesión"
        )

        raise HTTPException(
            status_code=503,
            detail="No se pudo cerrar la sesión",
        ) from exc

    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        samesite="lax",
    )

    return {
        "estado": "sesion_cerrada",
    }