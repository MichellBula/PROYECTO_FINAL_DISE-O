import logging

from datetime import date
from typing import Literal

import psycopg

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
)

from fastapi.middleware.cors import CORSMiddleware

from auth import usuario_auditor
from db import conexion, buscar_auditorias


# ============================================
# CONFIGURACIÓN
# ============================================

logging.basicConfig(level=logging.INFO)

log = logging.getLogger("auditoria")

app = FastAPI(
    title="Microservicio de auditoría",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)


# ============================================
# COMPROBAR SALUD
# ============================================

@app.get("/salud")
def salud():

    try:
        with conexion() as conn:

            conn.execute(
                "SELECT 1 FROM public.auditoria LIMIT 1"
            ).fetchone()

            conn.execute(
                "SELECT 1 FROM public.auth_sesiones LIMIT 1"
            ).fetchone()

        return {
            "estado": "ok",
            "postgres": "conectado",
            "servicio": "auditoria",
        }

    except psycopg.Error as exc:

        log.exception("Error de conexión o permisos")

        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible",
        ) from exc


# ============================================
# CONSULTAR AUDITORÍA
# ============================================

@app.get("/auditoria")
def consultar_auditoria(

    tipo_documento: Literal[
        "Cédula",
        "Tarjeta de identidad",
    ] | None = None,

    numero_documento: str | None = Query(
        default=None,
        pattern=r"^[0-9]{1,10}$",
    ),

    tipo_operacion: Literal[
        "CREAR",
        "CONSULTAR",
        "MODIFICAR",
        "ELIMINAR",
        "CONSULTA_IA",
        "CONSULTAR_AUDITORIA",
    ] | None = None,

    resultado: Literal[
        "EXITO",
        "ERROR",
        "DENEGADO",
    ] | None = None,

    fecha_desde: date | None = None,

    fecha_hasta: date | None = None,

    pagina: int = Query(default=1, ge=1),

    limite: int = Query(default=50, ge=1, le=100),

    usuario: dict = Depends(usuario_auditor),
):

    if (
        fecha_desde is not None
        and fecha_hasta is not None
        and fecha_desde > fecha_hasta
    ):
        raise HTTPException(
            status_code=422,
            detail="La fecha inicial no puede superar la fecha final",
        )

    try:

        return buscar_auditorias(
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            tipo_operacion=tipo_operacion,
            resultado=resultado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            pagina=pagina,
            limite=limite,
            usuario=f"roble:{usuario['user_id']}",
        )

    except psycopg.Error as exc:

        log.exception("Error consultando auditoría")

        raise HTTPException(
            status_code=503,
            detail="No se pudo consultar auditoría",
        ) from exc