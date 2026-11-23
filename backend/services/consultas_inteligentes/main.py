
import os
import re
import secrets
from collections import Counter
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado
from db import registrar_consulta_ia
from n8n_cliente import clasificar_pregunta, enviar_a_n8n
from recuperacion import recuperar_informacion


# ==========================================
# CONFIGURACION
# ==========================================

load_dotenv(Path(__file__).with_name(".env"))

app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.7.0",
)


class ConsultaIA(BaseModel):
    pregunta: str = Field(min_length=1, max_length=500)


# ==========================================
# SALUD DEL MICROSERVICIO
# ==========================================

@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "servicio": "consultas_inteligentes",
    }


# ==========================================
# OPERACIONES PERMITIDAS
# ==========================================

OPERACIONES_ESTADISTICAS = {
    "contar_personas",
    "contar_por_genero",
    "contar_mayores_edad",
    "contar_menores_edad",
    "promedio_edad",
    "contar_genero_especifico",
    "estadisticas_filtradas",
}


# ==========================================
# PERMISOS DE IDENTIFICACION EN ROBLE
# ==========================================

def puede_consultar_identidades(usuario):
    configurados = os.getenv(
        "CONSULTAS_IA_USUARIOS_IDENTIFICACION",
        "",
    )

    permitidos = {
        identificador.strip()
        for identificador in configurados.split(",")
        if identificador.strip()
    }

    return str(usuario["user_id"]) in permitidos


# ==========================================
# SEGURIDAD DEL CHAT INTERNO DE N8N
# ==========================================

def verificar_chat_interno(
    x_internal_chat_key: str | None = Header(
        default=None,
        alias="X-Internal-Chat-Key",
    ),
):
    """
    Autentica la integracion tecnica n8n -> FastAPI.

    Esta clave NO representa una sesion Roble
    ni concede identidad de usuario final.
    """

    clave_esperada = os.getenv(
        "N8N_CHAT_INTERNAL_API_KEY",
        "",
    )

    if not clave_esperada:
        raise HTTPException(
            status_code=503,
            detail="Integracion interna no configurada",
        )

    if (
        not x_internal_chat_key
        or not secrets.compare_digest(
            x_internal_chat_key,
            clave_esperada,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Acceso interno no autorizado",
        )

    return True


def chat_demo_permite_identidades():
    """
    Solo se habilita expresamente para una
    demostracion autorizada con datos ficticios.

    No equivale a una autorizacion de Roble.
    """

    return os.getenv(
        "CONSULTAS_IA_CHAT_DEMO_IDENTIDADES",
        "false",
    ).strip().lower() == "true"


# ==========================================
# RESPUESTAS VERIFICADAS DESDE POSTGRESQL
# ==========================================

def respuesta_exacta(operacion, datos, parametros):

    if operacion == "contar_personas":
        return (
            f"Hay {datos['total']} personas "
            "registradas en el sistema."
        )

    if operacion == "contar_por_genero":
        grupos = datos["datos"]

        if not grupos:
            return "No hay personas registradas."

        detalle = "; ".join(
            f"{fila['genero']}: {fila['total']}"
            for fila in grupos
        )

        return f"Personas por género: {detalle}."

    if operacion == "contar_mayores_edad":
        return (
            f"Hay {datos['total']} personas "
            "de 18 años o más."
        )

    if operacion == "contar_menores_edad":
        return (
            f"Hay {datos['total']} personas "
            "menores de 18 años."
        )

    if operacion == "promedio_edad":
        valor = datos["promedio"]

        if valor is None:
            return (
                "No hay datos válidos para calcular "
                "la edad promedio."
            )

        return f"La edad promedio es de {valor} años."

    if operacion == "contar_genero_especifico":
        return (
            f"Hay {datos['total']} personas "
            f"registradas con género {datos['genero']}."
        )

    if operacion == "estadisticas_filtradas":
        coincidencias = datos["coincidencias"]

        if "porcentaje" in datos:
            valor = datos["porcentaje"]

            if valor is None:
                return (
                    "No hay personas registradas "
                    "para calcular el porcentaje."
                )

            return (
                f"Se encontraron {coincidencias} personas "
                "que cumplen los filtros solicitados, "
                f"equivalentes al {valor}% del total."
            )

        return (
            f"Se encontraron {coincidencias} personas "
            "que cumplen los filtros solicitados."
        )

    if operacion == "buscar_personas":
        personas = datos["personas"]

        if not personas:
            return (
                "No se encontraron personas que "
                "cumplan los criterios de búsqueda."
            )

        if len(personas) == 1:
            persona = personas[0]
            orden = parametros.get("orden")

            if orden == "mas_joven":
                prefijo = "La persona más joven encontrada"
            elif orden == "mas_mayor":
                prefijo = "La persona de mayor edad encontrada"
            else:
                prefijo = "La persona encontrada"

            return (
                f"{prefijo} es {persona['nombre']}, "
                f"con {persona['edad']} años."
            )

        listado = "; ".join(
            f"{persona['nombre']} "
            f"({persona['edad']} años)"
            for persona in personas
        )

        return (
            f"Se muestran {len(personas)} personas "
            f"(máximo {datos['limite']}): {listado}."
        )

    raise ValueError("Operación no soportada")


# ==========================================
# VERIFICACION BASICA DE NUMEROS
# ==========================================

def cifras_coinciden(respuesta_ia, verificada):
    """
    Comprueba numeros, pero no garantiza
    por si sola la exactitud semantica.
    """

    numeros_ia = Counter(
        re.findall(
            r"\d+(?:[.,]\d+)?",
            respuesta_ia,
        )
    )

    numeros_verificados = Counter(
        re.findall(
            r"\d+(?:[.,]\d+)?",
            verificada,
        )
    )

    return numeros_ia == numeros_verificados


# ==========================================
# PROCESAMIENTO COMPARTIDO
# ==========================================

def ejecutar_consulta(
    pregunta: str,
    identificador: str,
    permitir_identidades: bool,
):
    """
    Reutiliza clasificacion, recuperacion,
    generacion y auditoria.

    No recibe instrucciones SQL del modelo.
    """

    pregunta = pregunta.strip()

    def auditar(resultado, respuesta, detalle):
        registrar_consulta_ia(
            usuario=identificador,
            pregunta=pregunta,
            respuesta=respuesta,
            resultado=resultado,
            detalle=detalle,
        )

    if not pregunta:
        raise HTTPException(
            status_code=422,
            detail="La pregunta no puede estar vacía",
        )

    # ======================================
    # 1. CLASIFICAR PREGUNTA
    # ======================================

    try:
        clasificacion = clasificar_pregunta(pregunta)

        operacion = clasificacion["operacion"]
        parametros = clasificacion["parametros"]

    except (
        httpx.HTTPError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        auditar(
            "ERROR",
            "No fue posible clasificar la pregunta.",
            "Error en el clasificador de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible clasificar la consulta",
        ) from exc

    # ======================================
    # 2. VALIDAR OPERACION
    # ======================================

    if operacion == "NO_RECONOCIDA":
        auditar(
            "DENEGADO",
            "Pregunta fuera del alcance.",
            "Operación no reconocida",
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "La pregunta no corresponde "
                "a una consulta disponible"
            ),
        )

    if operacion == "buscar_personas":
        if not permitir_identidades:
            auditar(
                "DENEGADO",
                "Consulta individual no autorizada.",
                "Sin permiso de identificación",
            )

            raise HTTPException(
                status_code=403,
                detail=(
                    "No tienes permiso para "
                    "consultar identidades"
                ),
            )

    elif operacion not in OPERACIONES_ESTADISTICAS:
        auditar(
            "DENEGADO",
            "Operación no autorizada.",
            "Operación no habilitada",
        )

        raise HTTPException(
            status_code=403,
            detail="Esta operación no está habilitada",
        )

    # ======================================
    # 3. RECUPERAR DATOS
    # ======================================

    try:
        datos = recuperar_informacion(
            operacion,
            parametros,
        )

        verificada = respuesta_exacta(
            operacion,
            datos,
            parametros,
        )

    except ValueError as exc:
        auditar(
            "DENEGADO",
            "Parámetros inválidos.",
            "Validación de filtros",
        )

        raise HTTPException(
            status_code=422,
            detail="Los filtros de consulta no son válidos",
        ) from exc

    except Exception as exc:
        auditar(
            "ERROR",
            "Error al recuperar información.",
            "Error en PostgreSQL",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible recuperar la información",
        ) from exc

    # ======================================
    # 4. GENERAR RESPUESTA CON N8N + GEMINI
    # ======================================

    try:
        resultado_ia = enviar_a_n8n(
            pregunta=pregunta,
            datos=datos,
        )

        texto_ia = resultado_ia.get("respuesta")

        if (
            not isinstance(texto_ia, str)
            or not texto_ia.strip()
        ):
            raise ValueError("Respuesta de IA inválida")

    except (
        httpx.HTTPError,
        RuntimeError,
        ValueError,
        AttributeError,
    ) as exc:
        auditar(
            "ERROR",
            "No fue posible generar la respuesta.",
            "Error en el procesamiento de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "No fue posible generar "
                "la respuesta inteligente"
            ),
        ) from exc

    # ======================================
    # 5. ASEGURAR RESPUESTA FUNDAMENTADA
    # ======================================

    # Consultas con filtros o identidades:
    # se conserva el resultado exacto de PostgreSQL.
    if operacion in {
        "buscar_personas",
        "estadisticas_filtradas",
    }:
        respuesta_final = verificada

    elif cifras_coinciden(texto_ia, verificada):
        respuesta_final = texto_ia.strip()

    else:
        respuesta_final = verificada

    # ======================================
    # 6. AUDITAR Y RESPONDER
    # ======================================

    auditar(
        "EXITO",
        respuesta_final,
        f"Consulta IA: {operacion}",
    )

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
    }


# ==========================================
# RUTA EXISTENTE PARA REACT + ROBLE
# ==========================================

@app.post("/consultas-ia")
def procesar_consulta(
    consulta: ConsultaIA,
    usuario: dict = Depends(usuario_autenticado),
):
    return ejecutar_consulta(
        pregunta=consulta.pregunta,
        identificador=f"roble:{usuario['user_id']}",
        permitir_identidades=puede_consultar_identidades(
            usuario
        ),
    )


# ==========================================
# NUEVA RUTA INTERNA PARA CHAT DE N8N
# ==========================================

@app.post("/consultas-ia/chat-interno")
def procesar_chat_interno(
    consulta: ConsultaIA,
    acceso_interno: bool = Depends(
        verificar_chat_interno
    ),
):
    """
    Ruta tecnica para la demostracion privada
    desde el editor de n8n.

    No afirma que el usuario se autentico
    mediante Roble.

    El encabezado secreto es obligatorio.
    """

    return ejecutar_consulta(
        pregunta=consulta.pregunta,
        identificador="servicio:n8n_chat_demo",
        permitir_identidades=(
            chat_demo_permite_identidades()
        ),
    )
