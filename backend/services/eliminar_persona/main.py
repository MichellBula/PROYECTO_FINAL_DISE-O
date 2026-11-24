
import logging
import re
import psycopg

from urllib.parse import unquote
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from auth import usuario_autenticado
from db import (
    conexion,
    eliminar_persona_db,
    obtener_persona_para_eliminacion_db,
)

# 1. CONFIGURACIÓN DE FASTAPI
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("eliminar_persona")

app = FastAPI(
    title="Microservicio de eliminación de personas",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["DELETE", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)


def exigir_administrador(usuario: dict = Depends(usuario_autenticado)) -> dict:
    """Rechaza accesos directos al servicio de usuarios sin rol administrador."""
    if usuario.get("rol") != "ADMINISTRADOR":
        raise HTTPException(
            status_code=403,
            detail="Solo un administrador puede eliminar personas",
        )
    return usuario


def validar_documento(tipo_documento: str, numero_documento: str):
    if tipo_documento not in ("Cédula", "Tarjeta de identidad"):
        raise HTTPException(status_code=422, detail="Tipo de documento inválido")
    if not re.fullmatch(r"[0-9]{1,10}", numero_documento):
        raise HTTPException(status_code=422, detail="Número de documento inválido")


# 2. ESTADO DEL MICROSERVICIO
@app.get("/salud")
def salud():
    try:
        with conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

        return {
            "estado": "ok",
            "postgres": "conectado"
        }

    except psycopg.Error:
        log.exception("Error conectando a PostgreSQL")
        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible"
        )


# 3. OBTENER DATOS PARA CONFIRMAR LA ELIMINACIÓN
@app.get("/eliminar-persona/personas/{tipo_documento}/{numero_documento}")
def obtener_persona_para_eliminar(
    tipo_documento: str,
    numero_documento: str,
    _usuario: dict = Depends(exigir_administrador),
):
    # Consulta propia del microservicio de eliminación, sin llamar a consultar_persona.
    validar_documento(tipo_documento, numero_documento)
    try:
        persona = obtener_persona_para_eliminacion_db(
            tipo_documento, numero_documento
        )
    except psycopg.Error as exc:
        log.exception("No se pudo cargar la persona para eliminación")
        raise HTTPException(503, "No se pudo cargar la persona") from exc

    if persona is None:
        raise HTTPException(404, "Persona no encontrada")
    return {"persona": persona}


# 4. ELIMINAR PERSONA
@app.delete("/eliminar-persona/personas/{tipo_documento}/{numero_documento}")
def eliminar_persona_endpoint(
    tipo_documento: str,
    numero_documento: str,
    usuario: dict = Depends(exigir_administrador)
):
    tipo_documento = unquote(tipo_documento)
    validar_documento(tipo_documento, numero_documento)
    usuario_id = f"roble:{usuario['user_id']}"

    try:
        persona_eliminada = eliminar_persona_db(
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            usuario=usuario_id
        )

        if not persona_eliminada:
            raise HTTPException(
                status_code=404,
                detail="Persona no encontrada"
            )

        return {
            "mensaje": "Persona eliminada correctamente",
            "persona": persona_eliminada
        }

    except psycopg.Error:
        log.exception("Error al eliminar persona")
        raise HTTPException(
            status_code=503,
            detail="No se pudo eliminar la persona"
        )
