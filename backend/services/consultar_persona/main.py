import logging
import re
from urllib.parse import unquote

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import usuario_autenticado
from db import conexion, registrar_auditoria

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("consultar_persona")
app = FastAPI(title="Microservicio de consulta de personas", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
)


def documento_de_ruta(path: str):
    partes = path.split("/")
    if len(partes) != 4 or partes[1] != "personas":
        return None, None
    tipo, numero = unquote(partes[2]), unquote(partes[3])
    if tipo not in ("Cédula", "Tarjeta de identidad") or not re.fullmatch(r"[0-9]{1,10}", numero):
        return None, None
    return tipo, numero


@app.middleware("http")
async def auditar_consultas(request: Request, call_next):
    if request.method != "GET" or not request.url.path.startswith("/personas/"):
        return await call_next(request)

    try:
        respuesta = await call_next(request)
        codigo = respuesta.status_code
    except Exception:
        log.exception("Error interno procesando consulta")
        codigo = 500
        respuesta = JSONResponse(status_code=500, content={"detail": "Error interno"})

    resultado = "EXITO" if codigo == 200 else "DENEGADO" if codigo in (401, 403) else "ERROR"
    tipo, numero = documento_de_ruta(request.url.path)
    usuario = getattr(request.state, "usuario_auditoria", "NO_AUTENTICADO")

    # Política fail-closed: no afirmamos una consulta exitosa si no pudimos auditarla.
    try:
        await run_in_threadpool(
            registrar_auditoria,
            usuario=usuario,
            resultado=resultado,
            detalle=f"Consulta convencional: HTTP {codigo}",
            tipo_documento=tipo,
            numero_documento=numero,
        )
    except Exception:
        log.exception("No se pudo registrar auditoria de consulta")
        return JSONResponse(status_code=503, content={"detail": "Auditoría no disponible"})

    return respuesta


@app.get("/salud")
def salud():
    try:
        with conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"estado": "ok", "postgres": "conectado"}
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")


@app.get("/personas/{tipo_documento}/{numero_documento}")
def consultar_persona(
    tipo_documento: str,
    numero_documento: str,
    _claims: dict = Depends(usuario_autenticado),
):
    if tipo_documento not in ("Cédula", "Tarjeta de identidad"):
        raise HTTPException(status_code=422, detail="Tipo de documento no admitido")
    if not re.fullmatch(r"[0-9]{1,10}", numero_documento):
        raise HTTPException(status_code=422, detail="Número de documento inválido")

    try:
        with conexion() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id_persona, tipo_documento, numero_documento,
                              primer_nombre, segundo_nombre, apellidos,
                              fecha_nacimiento, genero, correo, celular,
                              foto_ruta, fecha_registro
                       FROM public.persona
                       WHERE tipo_documento=%s AND numero_documento=%s""",
                    (tipo_documento, numero_documento),
                )
                persona = cur.fetchone()
    except psycopg.Error:
        log.exception("Error leyendo PostgreSQL")
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    if persona is None:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return persona
