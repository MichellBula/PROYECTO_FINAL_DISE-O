
"""
Lectura autenticada de fotografías para el
microservicio consultar_persona.
"""

import logging
import os
import re

from pathlib import Path

import psycopg

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from fastapi.responses import FileResponse
from psycopg.rows import dict_row

from db import conexion
from auth import usuario_autenticado


router_fotografias = APIRouter()

log = logging.getLogger(
    "consultar_persona.fotografias"
)

DIRECTORIO_FOTOS = Path(
    os.getenv(
        "PERSONAS_FOTOS_DIR",
        "/data/fotografias",
    )
)

NOMBRE_VALIDO = re.compile(
    r"[0-9a-f]{32}\.jpg\Z"
)


@router_fotografias.get(
    "/personas/{tipo_documento}/{numero_documento}/fotografia"
)
def obtener_fotografia(
    tipo_documento: str,
    numero_documento: str,
    _usuario: dict = Depends(usuario_autenticado),
):
    # Comprobar la sesión Roble antes de leer la imagen.

    if tipo_documento not in (
        "Cédula",
        "Tarjeta de identidad",
    ):
        raise HTTPException(
            status_code=422,
            detail="Tipo de documento no válido",
        )

    if not re.fullmatch(
        r"[0-9]{1,10}",
        numero_documento,
    ):
        raise HTTPException(
            status_code=422,
            detail="Número de documento no válido",
        )

    try:
        with conexion() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                cur.execute(
                    """
                    SELECT foto_ruta
                    FROM public.persona
                    WHERE tipo_documento = %s
                      AND numero_documento = %s
                    """,
                    (
                        tipo_documento,
                        numero_documento,
                    ),
                )

                persona = cur.fetchone()

    except psycopg.Error as exc:
        log.exception(
            "Error consultando la fotografía en PostgreSQL"
        )

        raise HTTPException(
            status_code=503,
            detail="Consulta de fotografía no disponible",
        ) from exc

    # Sin persona o sin foto asignada.
    if not persona or not persona["foto_ruta"]:
        raise HTTPException(
            status_code=404,
            detail="Fotografía no disponible",
        )

    nombre = str(
        persona["foto_ruta"]
    )

    # Solo aceptar los nombres seguros de las
    # fotografías nuevas: UUID hexadecimal + .jpg.
    if NOMBRE_VALIDO.fullmatch(nombre) is None:
        raise HTTPException(
            status_code=404,
            detail="Fotografía no disponible",
        )

    ruta = DIRECTORIO_FOTOS / nombre

    if not ruta.is_file():
        raise HTTPException(
            status_code=404,
            detail="Fotografía no disponible",
        )

    return FileResponse(
        path=ruta,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )