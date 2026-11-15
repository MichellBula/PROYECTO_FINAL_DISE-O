"""Sesiones opacas compartidas en PostgreSQL. No usa tokens Roble en el navegador."""
import hashlib
import os
from typing import Any

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

COOKIE_NAME = "gp_session"


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def conexion():
    """Cada solicitud abre su propia conexion al PostgreSQL autorizado."""
    obligatorias = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
    faltantes = [nombre for nombre in obligatorias if not os.getenv(nombre)]
    if faltantes:
        raise RuntimeError("Faltan variables de PostgreSQL: " + ", ".join(faltantes))
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


def obtener_sesion(request: Request) -> dict[str, Any]:
    """Valida cookie contra la DB: rechazo por defecto si no hay DB o sesion."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "No has iniciado sesion")
    try:
        with conexion() as conn:
            sesion = conn.execute(
                """SELECT usuario_roble_id, correo, nombre, csrf_token
                   FROM public.auth_sesiones
                   WHERE token_hash = %s
                     AND revocada_en IS NULL
                     AND expira_en > NOW()""",
                (token_hash(token),),
            ).fetchone()
    except (psycopg.Error, RuntimeError) as exc:
        raise HTTPException(503, "No se puede validar la sesion") from exc
    if not sesion:
        raise HTTPException(401, "Sesion inexistente, vencida o cerrada")
    return {
        "user_id": str(sesion["usuario_roble_id"]),
        "email": sesion["correo"],
        "name": sesion["nombre"],
        "csrf_token": sesion["csrf_token"],
    }


def exigir_usuario(request: Request) -> dict[str, str]:
    """Usar con Depends(exigir_usuario) en rutas protegidas."""
    sesion = obtener_sesion(request)
    return {k: sesion[k] for k in ("user_id", "email", "name")}


def proteger_app(app: FastAPI, publicas: set[str] | None = None) -> None:
    """Protege las rutas de un servicio completo excepto salud/docs.

    NO activar sobre un servicio que aun exige tokens Entra sin adaptar
    primero sus dependencias antiguas.
    """
    permitidas = publicas or {"/salud", "/docs", "/openapi.json", "/redoc"}

    @app.middleware("http")
    async def exigir_sesion_http(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in permitidas:
            return await call_next(request)
        try:
            request.state.usuario = exigir_usuario(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)
