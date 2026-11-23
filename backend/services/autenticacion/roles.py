"""
Administración de usuarios y roles.

Permite:
- Consultar perfiles registrados.
- Cambiar roles.
- Registrar cambios de roles.

Solo los administradores pueden acceder.
"""

import logging
import os
import secrets

from pathlib import Path
from typing import Literal
from uuid import UUID

import psycopg

from dotenv import load_dotenv

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
)

from pydantic import BaseModel

from gestion_seguridad import (
    conexion,
    obtener_sesion,
)


# =====================================================
# 1. CONFIGURACIÓN
# =====================================================

load_dotenv(Path(__file__).with_name(".env"))

logger = logging.getLogger("gestion.roles")

router = APIRouter(
    prefix="/auth",
    tags=["Administración de roles"],
)

ORIGENES = [
    origen.strip().rstrip("/")
    for origen in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://127.0.0.1:8001",
    ).split(",")
    if origen.strip()
]


# =====================================================
# 2. MODELO PARA CAMBIAR ROLES
# =====================================================

class CambioRol(BaseModel):

    rol: Literal[
        "ADMINISTRADOR",
        "OPERADOR",
        "CONSULTA",
    ]


# =====================================================
# 3. VERIFICAR ADMINISTRADOR
# =====================================================

def exigir_administrador(
    request: Request,
):

    sesion = obtener_sesion(request)

    if sesion["rol"] != "ADMINISTRADOR":

        raise HTTPException(
            status_code=403,
            detail=(
                "Esta operacion requiere "
                "permisos de administrador"
            ),
        )

    return sesion


# =====================================================
# 4. VALIDAR ORIGEN Y TOKEN CSRF
# =====================================================

def verificar_seguridad(
    request: Request,
    sesion: dict,
):

    origen = request.headers.get("origin")

    if origen and origen.rstrip("/") not in ORIGENES:

        raise HTTPException(
            status_code=403,
            detail="Origen no autorizado",
        )

    recibido = request.headers.get(
        "X-CSRF-Token",
        "",
    )

    esperado = sesion["csrf_token"]

    if (
        not recibido
        or not secrets.compare_digest(
            recibido,
            esperado,
        )
    ):

        raise HTTPException(
            status_code=403,
            detail="Token CSRF invalido",
        )


# =====================================================
# 5. CONSULTAR USUARIOS REGISTRADOS
# =====================================================

@router.get("/usuarios")
def listar_usuarios(
    request: Request,
    pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=20, ge=1, le=100),
):

    # Solo administradores
    exigir_administrador(request)

    desplazamiento = (pagina - 1) * limite

    try:

        with conexion() as conn:

            total = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM public.auth_perfiles
                """
            ).fetchone()["total"]

            usuarios = conn.execute(
                """
                SELECT
                    usuario_roble_id,
                    correo,
                    nombre,
                    rol,
                    activo,
                    creado_en

                FROM public.auth_perfiles

                ORDER BY creado_en DESC,
                         usuario_roble_id

                LIMIT %s
                OFFSET %s
                """,
                (
                    limite,
                    desplazamiento,
                ),
            ).fetchall()

    except (
        psycopg.Error,
        RuntimeError,
    ) as exc:

        logger.exception(
            "Error consultando perfiles"
        )

        raise HTTPException(
            status_code=503,
            detail="No se pudieron consultar los usuarios",
        ) from exc

    registros = []

    for usuario in usuarios:

        registros.append({

            "usuario_roble_id": str(
                usuario["usuario_roble_id"]
            ),

            "correo": usuario["correo"],

            "nombre": usuario["nombre"],

            "rol": usuario["rol"],

            "activo": usuario["activo"],

            "creado_en": (
                usuario["creado_en"].isoformat()
            ),

        })

    return {
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "usuarios": registros,
    }


# =====================================================
# 6. CAMBIAR ROL DE UN USUARIO
# =====================================================

@router.patch("/usuarios/{usuario_id}/rol")
def cambiar_rol(
    usuario_id: UUID,
    datos: CambioRol,
    request: Request,
):

    # Verificar administrador
    administrador = exigir_administrador(request)

    # Validar origen y token CSRF
    verificar_seguridad(
        request,
        administrador,
    )

    # Evitar que un administrador
    # modifique su propio rol
    if administrador["user_id"] == str(usuario_id):

        raise HTTPException(
            status_code=403,
            detail=(
                "No puedes modificar "
                "tu propio rol"
            ),
        )

    try:

        with conexion() as conn:

            # -----------------------------------------
            # 6.1. CONSULTAR ROL ACTUAL
            # -----------------------------------------

            usuario = conn.execute(
                """
                SELECT
                    rol

                FROM public.auth_perfiles

                WHERE usuario_roble_id = %s

                FOR UPDATE
                """,
                (usuario_id,),
            ).fetchone()

            if not usuario:

                raise HTTPException(
                    status_code=404,
                    detail="Usuario no encontrado",
                )

            rol_anterior = usuario["rol"]

            # -----------------------------------------
            # 6.2. COMPROBAR SI HAY CAMBIOS
            # -----------------------------------------

            if rol_anterior == datos.rol:

                return {
                    "estado": "sin_cambios",
                    "mensaje": (
                        "El usuario ya tiene "
                        "ese rol"
                    ),
                }

            # -----------------------------------------
            # 6.3. ACTUALIZAR ROL
            # -----------------------------------------

            conn.execute(
                """
                UPDATE public.auth_perfiles

                SET
                    rol = %s,
                    actualizado_en = NOW()

                WHERE usuario_roble_id = %s
                """,
                (
                    datos.rol,
                    usuario_id,
                ),
            )

            # -----------------------------------------
            # 6.4. REGISTRAR HISTORIAL
            # -----------------------------------------

            conn.execute(
                """
                INSERT INTO public.auth_cambios_rol (

                    administrador_roble_id,
                    usuario_roble_id,
                    rol_anterior,
                    rol_nuevo

                )

                VALUES (%s, %s, %s, %s)
                """,
                (
                    UUID(administrador["user_id"]),
                    usuario_id,
                    rol_anterior,
                    datos.rol,
                ),
            )

    except (
        psycopg.Error,
        RuntimeError,
    ) as exc:

        logger.exception(
            "Error modificando rol"
        )

        raise HTTPException(
            status_code=503,
            detail="No se pudo modificar el rol",
        ) from exc

    return {
        "estado": "actualizado",
        "mensaje": "Rol actualizado correctamente",
        "usuario_roble_id": str(usuario_id),
        "rol_anterior": rol_anterior,
        "rol_nuevo": datos.rol,
    }