
import os
import secrets
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response

from gestion_seguridad import obtener_sesion


app = FastAPI(title="Gestion de Personas - API Gateway")

# Direcciones internas de los microservicios en Docker.
SERVICIOS = {
    "autenticacion": os.getenv("AUTH_URL", "http://autenticacion:8001"),
    "consultar": os.getenv("CONSULTAR_URL", "http://consultar_persona:8000"),
    "crear": os.getenv("CREAR_URL", "http://crear_persona:8002"),
    "modificar": os.getenv("MODIFICAR_URL", "http://modificar_persona:8003"),
    "eliminar": os.getenv("ELIMINAR_URL", "http://eliminar_persona:8005"),
    "auditoria": os.getenv("AUDITORIA_URL", "http://auditoria:8004"),
}


def validar_documento(tipo: str, numero: str):
    if tipo not in ("Cédula", "Tarjeta de identidad"):
        raise HTTPException(422, "Tipo de documento invalido")

    if not numero.isascii() or not numero.isdigit() or len(numero) > 10:
        raise HTTPException(422, "Numero de documento invalido")


def verificar_acceso(request: Request):
    # Las sesiones de Roble se validan contra PostgreSQL.
    sesion = obtener_sesion(request)

    # Proteger operaciones que modifican datos.
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        recibido = request.headers.get("X-CSRF-Token", "")
        esperado = sesion["csrf_token"]

        if not recibido or not secrets.compare_digest(recibido, esperado):
            raise HTTPException(403, "Token CSRF invalido")

    return sesion


async def reenviar(
    request: Request,
    servicio: str,
    ruta_interna: str,
    excluir_parametros=(),
):
    # Mantener el formato original: JSON, formularios o fotografias.
    cuerpo = await request.body()

    encabezados = {}
    for nombre in ("content-type", "cookie", "origin", "x-csrf-token", "accept"):
        valor = request.headers.get(nombre)
        if valor:
            encabezados[nombre] = valor

    parametros = [
        (clave, valor)
        for clave, valor in request.query_params.multi_items()
        if clave not in excluir_parametros
    ]

    url = SERVICIOS[servicio] + ruta_interna

    try:
        async with httpx.AsyncClient(timeout=30.0) as cliente:
            respuesta = await cliente.request(
                method=request.method,
                url=url,
                params=parametros,
                content=cuerpo,
                headers=encabezados,
                follow_redirects=False,
            )
    except httpx.RequestError:
        raise HTTPException(
            503,
            f"El servicio {servicio} no esta disponible",
        )

    # Conservar codigo HTTP, contenido y cookie cuando corresponda.
    encabezados_respuesta = {}
    for nombre in ("content-type", "set-cookie", "location"):
        valor = respuesta.headers.get(nombre)
        if valor:
            encabezados_respuesta[nombre] = valor

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        headers=encabezados_respuesta,
    )


@app.get("/salud")
def salud():
    return {"estado": "ok", "servicio": "api_gateway"}


# AUTENTICACION ROBLE
@app.api_route("/api/auth/{subruta:path}", methods=["GET", "POST"])
async def autenticacion(request: Request, subruta: str):
    if subruta not in ("login", "yo", "privado", "logout"):
        raise HTTPException(404, "Ruta de autenticacion inexistente")
    return await reenviar(request, "autenticacion", "/auth/" + subruta)


# CREAR PERSONA
@app.post("/api/personas")
async def crear_persona(request: Request):
    verificar_acceso(request)
    return await reenviar(request, "crear", "/personas")


# CONSULTAR PERSONA
@app.get("/api/personas/{documento}")
async def consultar_persona(
    documento: str,
    request: Request,
    tipo_documento: str = Query(...),
):
    verificar_acceso(request)
    validar_documento(tipo_documento, documento)

    ruta = (
        "/personas/"
        + quote(tipo_documento, safe="")
        + "/"
        + quote(documento, safe="")
    )

    return await reenviar(
        request, "consultar", ruta,
        excluir_parametros=("tipo_documento",),
    )


# MODIFICAR PERSONA
@app.put("/api/personas/{documento}")
async def modificar_persona(
    documento: str,
    request: Request,
    tipo_documento: str = Query(...),
):
    verificar_acceso(request)
    validar_documento(tipo_documento, documento)

    ruta = (
        "/modificar-persona/personas/"
        + quote(tipo_documento, safe="")
        + "/"
        + quote(documento, safe="")
    )

    return await reenviar(
        request, "modificar", ruta,
        excluir_parametros=("tipo_documento",),
    )


# ELIMINAR PERSONA
@app.delete("/api/personas/{documento}")
async def eliminar_persona(
    documento: str,
    request: Request,
    tipo_documento: str = Query(...),
):
    verificar_acceso(request)
    validar_documento(tipo_documento, documento)

    ruta = (
        "/eliminar-persona/personas/"
        + quote(tipo_documento, safe="")
        + "/"
        + quote(documento, safe="")
    )

    return await reenviar(
        request, "eliminar", ruta,
        excluir_parametros=("tipo_documento",),
    )


# CONSULTAR AUDITORIA
@app.get("/api/auditoria")
async def consultar_auditoria(request: Request):
    verificar_acceso(request)
    return await reenviar(request, "auditoria", "/auditoria")


# CONSULTAS INTELIGENTES - PENDIENTE DE INTEGRAR CON N8N
@app.post("/api/consultas-ia")
async def consultas_ia(request: Request):
    verificar_acceso(request)
    raise HTTPException(
        503,
        "La integracion con n8n y RAG aun no esta configurada",
    )
