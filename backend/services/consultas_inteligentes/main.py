
"""
Microservicio de consultas inteligentes.

Autenticacion con Proyecto Roble.
Clasificacion mediante n8n y Gemini.
Recuperacion SQL controlada.
Auditoria de consultas.
"""

from collections import Counter
import re

import httpx

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado
from db import registrar_consulta_ia

from n8n_cliente import (
    clasificar_pregunta,
    enviar_a_n8n,
)

from recuperacion import (
    recuperar_informacion,
    OPERACIONES_AUTORIZADAS,
)


# ==========================================
# APLICACION
# ==========================================

app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.4.0",
)


class ConsultaIA(BaseModel):
    pregunta: str = Field(
        min_length=1,
        max_length=500,
    )


@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "servicio": "consultas_inteligentes",
    }


# ==========================================
# RESPUESTAS EXACTAS DE POSTGRESQL
# ==========================================

def respuesta_exacta(operacion: str, datos: dict) -> str:

    if operacion == "contar_personas":
        return (
            f"Actualmente hay {datos['total']} "
            "personas registradas en el sistema."
        )

    if operacion == "contar_por_genero":
        if not datos["datos"]:
            return (
                "No hay personas registradas "
                "para agrupar por genero."
            )

        detalle = "; ".join(
            f"{fila['genero']}: {fila['total']}"
            for fila in datos["datos"]
        )

        return (
            f"Personas registradas por genero: "
            f"{detalle}."
        )

    if operacion == "contar_mayores_edad":
        return (
            f"Hay {datos['total']} personas "
            "de 18 anos o mas registradas."
        )

    if operacion == "contar_menores_edad":
        return (
            f"Hay {datos['total']} personas "
            "menores de 18 anos registradas."
        )

    if operacion == "promedio_edad":
        if datos["promedio"] is None:
            return (
                "No hay fechas de nacimiento validas "
                "para calcular el promedio de edad."
            )

        return (
            "La edad promedio de las personas "
            f"registradas es {datos['promedio']} anos."
        )

    if operacion == "contar_genero_especifico":
        return (
            f"Hay {datos['total']} personas "
            f"registradas con genero {datos['genero']}."
        )

    raise ValueError(
        "Operacion sin respuesta definida"
    )


# ==========================================
# VALIDAR CIFRAS DE LA RESPUESTA IA
# ==========================================

def validar_respuesta_ia(
    texto: str,
    respuesta_verificada: str,
) -> bool:
    """
    Descarta respuestas de Gemini que introduzcan
    cifras distintas a las verificadas en PostgreSQL.

    Es una comprobacion basica, no una garantia
    completa de exactitud semantica.
    """

    numeros_verificados = Counter(
        re.findall(
            r"\d+(?:[.,]\d+)?",
            respuesta_verificada,
        )
    )

    numeros_generados = Counter(
        re.findall(
            r"\d+(?:[.,]\d+)?",
            texto,
        )
    )

    return (
        bool(texto.strip())
        and numeros_generados == numeros_verificados
    )


# ==========================================
# PROCESAR CONSULTA
# ==========================================

@app.post("/consultas-ia")
def procesar_consulta(
    consulta: ConsultaIA,
    usuario: dict = Depends(usuario_autenticado),
):

    pregunta = consulta.pregunta.strip()

    identificador_usuario = (
        f"roble:{usuario['user_id']}"
    )

    if not pregunta:
        raise HTTPException(
            status_code=422,
            detail="La pregunta no puede estar vacia",
        )

    # Registrar operaciones en auditoria.
    def auditar(
        resultado: str,
        respuesta: str,
        detalle: str,
    ):
        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta=respuesta,
            resultado=resultado,
            detalle=detalle,
        )

    # ======================================
    # 1. CLASIFICACION
    # ======================================

    try:
        clasificacion = clasificar_pregunta(pregunta)

    except (
        httpx.HTTPError,
        RuntimeError,
        ValueError,
    ) as exc:

        auditar(
            "ERROR",
            "No fue posible clasificar la pregunta.",
            "Error en clasificador n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible clasificar la consulta",
        ) from exc

    operacion = clasificacion["operacion"]
    parametros = clasificacion["parametros"]

    # ======================================
    # 2. PREGUNTAS NO RECONOCIDAS
    # ======================================

    if operacion == "NO_RECONOCIDA":
        auditar(
            "DENEGADO",
            "Pregunta fuera del alcance.",
            "Operacion no reconocida",
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "La pregunta no corresponde "
                "a una consulta disponible"
            ),
        )

    # ======================================
    # 3. OPERACIONES HABILITADAS
    # ======================================

    # Solamente consultas agregadas.
    # No se permite recuperar personas
    # individuales mediante este endpoint.

    operaciones_habilitadas = set(
        OPERACIONES_AUTORIZADAS
    )

    if operacion not in operaciones_habilitadas:

        auditar(
            "DENEGADO",
            "Consulta no autorizada.",
            (
                "Operacion no habilitada: "
                f"{operacion[:80]}"
            ),
        )

        raise HTTPException(
            status_code=403,
            detail="Esta operacion no esta habilitada",
        )

    # ======================================
    # 4. RECUPERAR INFORMACION
    # ======================================

    try:
        datos = recuperar_informacion(
            operacion,
            parametros,
        )

        respuesta_verificada = respuesta_exacta(
            operacion,
            datos,
        )

    except ValueError as exc:
        auditar(
            "DENEGADO",
            "Parametros invalidos.",
            "Parametros invalidos en consulta IA",
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "La consulta contiene "
                "parametros invalidos"
            ),
        ) from exc

    except Exception as exc:
        auditar(
            "ERROR",
            "Error al consultar los datos.",
            "Error en recuperacion SQL",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible recuperar los datos",
        ) from exc

    # ======================================
    # 5. PROCESAR EN N8N
    # ======================================

    try:
        resultado_n8n = enviar_a_n8n(
            pregunta=pregunta,
            datos=datos,
        )

        respuesta_ia = resultado_n8n.get("respuesta")

        if (
            not isinstance(respuesta_ia, str)
            or not respuesta_ia.strip()
        ):
            raise ValueError(
                "Respuesta no valida del procesador IA"
            )

    except (
        httpx.HTTPError,
        RuntimeError,
        ValueError,
    ) as exc:

        auditar(
            "ERROR",
            "No fue posible generar la respuesta.",
            "Error en procesador n8n",
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "No fue posible generar "
                "la respuesta inteligente"
            ),
        ) from exc

    # ======================================
    # 6. VALIDAR RESPUESTA
    # ======================================

    if validar_respuesta_ia(
        respuesta_ia,
        respuesta_verificada,
    ):
        respuesta_final = respuesta_ia.strip()
    else:
        respuesta_final = respuesta_verificada

    # ======================================
    # 7. AUDITORIA
    # ======================================

    auditar(
        "EXITO",
        respuesta_final,
        f"Consulta IA: {operacion}",
    )

    # ======================================
    # 8. RESPUESTA AL FRONTEND
    # ======================================

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
    }
