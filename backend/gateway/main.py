
"""
API Gateway del sistema de gestión de personas.

Responsabilidades:
- Recibir solicitudes de React.
- Validar sesiones.
- Controlar permisos según el rol.
- Validar tokens CSRF.
- Comunicarse con los microservicios.
"""

import os
import secrets

from urllib.parse import quote
from uuid import UUID

import httpx

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
)

from gestion_seguridad import obtener_sesion


# =====================================================
# 1. CONFIGURACIÓN
# =====================================================

app = FastAPI(
    title="Gestion de Personas - API Gateway"
)


# =====================================================
# 2. MICROSERVICIOS
# =====================================================

SERVICIOS = {
    "autenticacion": os.getenv(
        "AUTH_URL", "http://autenticacion:8001"
    ),
    "consultar": os.getenv(
        "CONSULTAR_URL", "http://consultar_persona:8000"
    ),
    "crear": os.getenv(
        "CREAR_URL", "http://crear_persona:8002"
    ),
    "modificar": os.getenv(
        "MODIFICAR_URL", "http://modificar_persona:8003"
    ),
    "eliminar": os.getenv(
        "ELIMINAR_URL", "http://eliminar_persona:8005"
    ),
    "auditoria": os.getenv(
        "AUDITORIA_URL", "http://auditoria:8004"
    ),
    "consultas_ia": os.getenv(
        "CONSULTAS_IA_URL",
        "http://consultas_inteligentes:8007"
    ),
}


# =====================================================
# 3. PERMISOS
# =====================================================

PERMISOS = {

    "CONSULTAR": {
        "CONSULTA",
        "OPERADOR",
        "ADMINISTRADOR",
    },

    "CREAR": {
        "OPERADOR",
        "ADMINISTRADOR",
    },

    "MODIFICAR": {
        "OPERADOR",
        "ADMINISTRADOR",
    },

    "ELIMINAR": {
        "ADMINISTRADOR",
    },

    "AUDITORIA": {
        "ADMINISTRADOR",
    },

    "CONSULTAS_IA": {
        "CONSULTA",
        "OPERADOR",
        "ADMINISTRADOR",
    },

    "GESTION_USUARIOS": {
        "ADMINISTRADOR",
    },
}


# =====================================================
# 4. VALIDACIÓN DE DOCUMENTOS
# =====================================================

def validar_documento(tipo: str, numero: str):

    if tipo not in ("Cédula", "Tarjeta de identidad"):

        raise HTTPException(
            status_code=422,
            detail="Tipo de documento invalido",
        )

    if (
        not numero.isascii()
        or not numero.isdigit()
        or len(numero) > 10
    ):

        raise HTTPException(
            status_code=422,
            detail="Numero de documento invalido",
        )


# =====================================================
# 5. VALIDACIÓN DE ACCESO
# =====================================================

def verificar_acceso(
    request: Request,
    operacion: str,
):

    sesion = obtener_sesion(request)

    roles_permitidos = PERMISOS.get(operacion)

    if roles_permitidos is None:

        raise HTTPException(
            status_code=500,
            detail="Operacion sin politica de permisos",
        )

    if sesion["rol"] not in roles_permitidos:

        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para esta operacion",
        )

    if request.method in ("POST", "PUT", "PATCH", "DELETE"):

        recibido = request.headers.get(
            "X-CSRF-Token", ""
        )

        esperado = sesion["csrf_token"]

        if (
            not recibido
            or not secrets.compare_digest(recibido, esperado)
        ):

            raise HTTPException(
                status_code=403,
                detail="Token CSRF invalido",
            )

    return sesion


# =====================================================
# 6. REENVIAR SOLICITUDES
# =====================================================

async def reenviar(
    request: Request,
    servicio: str,
    ruta_interna: str,
    excluir_parametros=(),
):

    cuerpo = await request.body()

    encabezados = {}

    for nombre in (
        "content-type",
        "cookie",
        "origin",
        "x-csrf-token",
        "accept",
    ):

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
            status_code=503,
            detail=f"El servicio {servicio} no esta disponible",
        )

    encabezados_respuesta = {}

    for nombre in (
        "content-type",
        "set-cookie",
        "location",
        "cache-control",
        "x-content-type-options",
    ):

        valor = respuesta.headers.get(nombre)

        if valor:
            encabezados_respuesta[nombre] = valor

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        headers=encabezados_respuesta,
    )


# =====================================================
# 7. SALUD
# =====================================================

@app.get("/salud")
def salud():

    return {
        "estado": "ok",
        "servicio": "api_gateway",
    }


# =====================================================
# 8. ADMINISTRACIÓN DE USUARIOS
# =====================================================

@app.get("/api/auth/usuarios")
async def listar_usuarios(request: Request):

    verificar_acceso(
        request,
        "GESTION_USUARIOS",
    )

    return await reenviar(
        request,
        "autenticacion",
        "/auth/usuarios",
    )


@app.patch("/api/auth/usuarios/{usuario_id}/rol")
async def cambiar_rol(
    usuario_id: UUID,
    request: Request,
):

    verificar_acceso(
        request,
        "GESTION_USUARIOS",
    )

    return await reenviar(
        request,
        "autenticacion",
        f"/auth/usuarios/{usuario_id}/rol",
    )


# =====================================================
# 9. AUTENTICACIÓN Y REGISTRO
# =====================================================

@app.api_route(
    "/api/auth/{subruta:path}",
    methods=["GET", "POST"],
)
async def autenticacion(
    request: Request,
    subruta: str,
):

    rutas_permitidas = {
        "login",
        "yo",
        "privado",
        "logout",
        "registro",
        "verificar-correo",
    }

    if subruta not in rutas_permitidas:

        raise HTTPException(
            status_code=404,
            detail="Ruta de autenticacion inexistente",
        )

    return await reenviar(
        request,
        "autenticacion",
        "/auth/" + subruta,
    )


# =====================================================
# 10. CREAR PERSONA
# =====================================================

@app.post("/api/personas")
async def crear_persona(request: Request):

    verificar_acceso(request, "CREAR")

    return await reenviar(
        request,
        "crear",
        "/personas",
    )


# =====================================================
# FOTOGRAFÍA DE PERSONA (LECTURA PROTEGIDA)
# =====================================================

@app.get("/api/personas/{documento}/fotografia")
async def consultar_fotografia(
    documento: str,
    request: Request,
    tipo_documento: str = Query(...),
):
    verificar_acceso(request, "CONSULTAR")
    validar_documento(tipo_documento, documento)

    ruta = (
        "/personas/"
        + quote(tipo_documento, safe="")
        + "/"
        + quote(documento, safe="")
        + "/fotografia"
    )

    return await reenviar(
        request,
        "consultar",
        ruta,
        excluir_parametros=("tipo_documento",),
    )


# =====================================================
# 11. CONSULTAR PERSONA
# =====================================================

@app.get("/api/personas/{documento}")
async def consultar_persona(
    documento: str,
    request: Request,
    tipo_documento: str = Query(...),
):

    verificar_acceso(request, "CONSULTAR")

    validar_documento(
        tipo_documento,
        documento,
    )

    ruta = (
        "/personas/"
        + quote(tipo_documento, safe="")
        + "/"
        + quote(documento, safe="")
    )

    return await reenviar(
        request,
        "consultar",
        ruta,
        excluir_parametros=("tipo_documento",),
    )


# =====================================================
# 12. MODIFICAR PERSONA
# =====================================================

@app.put("/api/personas/{documento}")
async def modificar_persona(
    documento: str,
    request: Request,
    tipo_documento: str = Query(...),
):

    verificar_acceso(request, "MODIFICAR")

    validar_documento(
        tipo_documento,
        documento,
    )

    ruta = (
        "/modificar-persona/personas/"
        + quote(tipo_documento, safe="")
        + "/"
        + quote(documento, safe="")
    )

    return await reenviar(
        request,
        "modificar",
        ruta,
        excluir_parametros=("tipo_documento",),
    )


# =====================================================
# 13. ELIMINAR PERSONA
# =====================================================

@app.delete("/api/personas/{documento}")
async def eliminar_persona(
    documento: str,
    request: Request,
    tipo_documento: str = Query(...),
):

    verificar_acceso(request, "ELIMINAR")

    validar_documento(
        tipo_documento,
        documento,
    )

    ruta = (
        "/eliminar-persona/personas/"
        + quote(tipo_documento, safe="")
        + "/"
        + quote(documento, safe="")
    )

    return await reenviar(
        request,
        "eliminar",
        ruta,
        excluir_parametros=("tipo_documento",),
    )


# =====================================================
# 14. AUDITORÍA
# =====================================================

@app.get("/api/auditoria")
async def consultar_auditoria(request: Request):

    verificar_acceso(request, "AUDITORIA")

    return await reenviar(
        request,
        "auditoria",
        "/auditoria",
    )


# =====================================================
# 15. CHATBOT
# =====================================================

@app.post("/api/consultas-ia")
async def consultas_ia(request: Request):

    verificar_acceso(request, "CONSULTAS_IA")

    return await reenviar(
        request,
        "consultas_ia",
        "/consultas-ia",
    )