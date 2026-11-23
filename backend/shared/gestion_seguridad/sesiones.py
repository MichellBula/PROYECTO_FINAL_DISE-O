"""
Gestión de sesiones y perfiles de usuario.

Este módulo permite:

1. Validar sesiones almacenadas en PostgreSQL.
2. Identificar al usuario autenticado.
3. Consultar su rol.
4. Comprobar si su cuenta está activa.
5. Proteger los endpoints de los microservicios.

Las sesiones utilizan tokens opacos.
Los tokens de Roble no se almacenan en el navegador.
"""

import hashlib
import os

from typing import Any

import psycopg

from psycopg.rows import dict_row

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)

from fastapi.responses import JSONResponse


# =====================================================
# 1. CONFIGURACIÓN DE SESIONES
# =====================================================

COOKIE_NAME = "gp_session"


# =====================================================
# 2. GENERAR HASH DEL TOKEN
# =====================================================

def token_hash(token: str) -> str:

    """
    Genera el hash SHA-256 del token de sesión.

    En PostgreSQL se almacena el hash,
    no el token original.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# =====================================================
# 3. CONEXIÓN A POSTGRESQL
# =====================================================

def conexion():

    """
    Crea una conexión a PostgreSQL utilizando
    las variables de entorno configuradas.
    """

    obligatorias = (
        "PGHOST",
        "PGPORT",
        "PGDATABASE",
        "PGUSER",
        "PGPASSWORD",
    )

    faltantes = [
        nombre
        for nombre in obligatorias
        if not os.getenv(nombre)
    ]

    if faltantes:

        raise RuntimeError(
            "Faltan variables de PostgreSQL: "
            + ", ".join(faltantes)
        )

    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


# =====================================================
# 4. OBTENER Y VALIDAR SESIÓN
# =====================================================

def obtener_sesion(
    request: Request,
) -> dict[str, Any]:

    """
    Valida la cookie de sesión y consulta
    el perfil del usuario en PostgreSQL.

    Devuelve:
    - ID del usuario.
    - Correo electrónico.
    - Nombre.
    - Rol.
    - Token CSRF.

    Rechaza:
    - Sesiones inexistentes.
    - Sesiones vencidas.
    - Sesiones revocadas.
    - Usuarios sin perfil.
    - Cuentas desactivadas.
    """

    # -------------------------------------------------
    # 4.1. OBTENER COOKIE
    # -------------------------------------------------

    token = request.cookies.get(COOKIE_NAME)

    if not token:

        raise HTTPException(
            status_code=401,
            detail="No has iniciado sesion",
        )

    # -------------------------------------------------
    # 4.2. CONSULTAR SESIÓN Y PERFIL
    # -------------------------------------------------

    try:

        with conexion() as conn:

            sesion = conn.execute(
                """
                SELECT
                    s.usuario_roble_id,
                    p.correo,
                    p.nombre,
                    s.csrf_token,
                    p.rol,
                    p.activo

                FROM public.auth_sesiones AS s

                INNER JOIN public.auth_perfiles AS p
                    ON p.usuario_roble_id =
                       s.usuario_roble_id

                WHERE s.token_hash = %s

                  AND s.revocada_en IS NULL

                  AND s.expira_en > NOW()
                """,
                (token_hash(token),),
            ).fetchone()

    except (
        psycopg.Error,
        RuntimeError,
    ) as exc:

        raise HTTPException(
            status_code=503,
            detail="No se puede validar la sesion",
        ) from exc

    # -------------------------------------------------
    # 4.3. VALIDAR EXISTENCIA DE SESIÓN
    # -------------------------------------------------

    if not sesion:

        raise HTTPException(
            status_code=401,
            detail=(
                "Sesion inexistente, vencida, "
                "cerrada o sin perfil"
            ),
        )

    # -------------------------------------------------
    # 4.4. COMPROBAR SI LA CUENTA ESTÁ ACTIVA
    # -------------------------------------------------

    if not sesion["activo"]:

        raise HTTPException(
            status_code=403,
            detail=(
                "Tu cuenta esta desactivada"
            ),
        )

    # -------------------------------------------------
    # 4.5. DEVOLVER IDENTIDAD Y ROL
    # -------------------------------------------------

    return {
        "user_id": str(
            sesion["usuario_roble_id"]
        ),
        "email": sesion["correo"],
        "name": sesion["nombre"],
        "rol": sesion["rol"],
        "csrf_token": sesion["csrf_token"],
    }


# =====================================================
# 5. EXIGIR USUARIO AUTENTICADO
# =====================================================

def exigir_usuario(
    request: Request,
) -> dict[str, str]:

    """
    Comprueba que el usuario tenga
    una sesión válida.

    Devuelve su identidad y su rol.

    El token CSRF no se incluye en
    los datos públicos del usuario.
    """

    sesion = obtener_sesion(request)

    return {
        "user_id": sesion["user_id"],
        "email": sesion["email"],
        "name": sesion["name"],
        "rol": sesion["rol"],
    }


# =====================================================
# 6. PROTEGER MICROSERVICIOS
# =====================================================

def proteger_app(
    app: FastAPI,
    publicas: set[str] | None = None,
) -> None:

    """
    Protege los endpoints de una aplicación
    FastAPI mediante sesiones.

    Permite acceder sin autenticación
    a las rutas públicas configuradas.
    """

    permitidas = (
        publicas
        if publicas is not None
        else {
            "/salud",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
    )

    @app.middleware("http")
    async def exigir_sesion_http(
        request: Request,
        call_next,
    ):

        # ---------------------------------------------
        # PERMITIR PREFLIGHT Y RUTAS PÚBLICAS
        # ---------------------------------------------

        if (
            request.method == "OPTIONS"
            or request.url.path in permitidas
        ):

            return await call_next(request)

        # ---------------------------------------------
        # VERIFICAR AUTENTICACIÓN
        # ---------------------------------------------

        try:

            usuario = exigir_usuario(request)

            # Guardar usuario y rol en la solicitud
            request.state.usuario = usuario

        except HTTPException as exc:

            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": exc.detail
                },
            )

        # ---------------------------------------------
        # CONTINUAR CON EL ENDPOINT
        # ---------------------------------------------

        return await call_next(request)