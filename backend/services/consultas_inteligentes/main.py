
import re

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado
from db import registrar_consulta_ia
from n8n_cliente import clasificar_pregunta, enviar_a_n8n
from recuperacion import recuperar_informacion


app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.3.0",
)


class ConsultaIA(BaseModel):
    pregunta: str = Field(min_length=1, max_length=500)


@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "servicio": "consultas_inteligentes",
    }


@app.post("/consultas-ia")
def procesar_consulta(
    consulta: ConsultaIA,
    usuario: dict = Depends(usuario_autenticado),
):
    pregunta = consulta.pregunta.strip()
    identificador_usuario = f"roble:{usuario['user_id']}"

    if not pregunta:
        raise HTTPException(
            status_code=422,
            detail="La pregunta no puede estar vacia",
        )

    # Gemini identifica la intencion, pero no ejecuta SQL.
    try:
        operacion = clasificar_pregunta(pregunta)

    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta="No fue posible clasificar la pregunta.",
            resultado="ERROR",
            detalle="Error en el clasificador de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible clasificar la consulta",
        ) from exc

    # Preguntas fuera del alcance del sistema.
    if operacion == "NO_RECONOCIDA":
        raise HTTPException(
            status_code=422,
            detail="La pregunta no corresponde a una consulta disponible",
        )

    # Lista de operaciones habilitadas en esta etapa.
    # No basta con que Gemini reconozca una operacion:
    # FastAPI debe autorizar su ejecucion.
    operaciones_habilitadas = {"contar_personas"}

    if operacion not in operaciones_habilitadas:
        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta="Consulta no autorizada.",
            resultado="DENEGADO",
            detalle="Operacion no habilitada",
        )

        raise HTTPException(
            status_code=403,
            detail="Esta operacion no esta habilitada",
        )

    # Recuperacion controlada desde PostgreSQL.
    datos = recuperar_informacion(operacion)
    total = datos["total"]

    respuesta_verificada = (
        f"Actualmente hay {total} "
        "personas registradas en el sistema."
    )

    try:
        # Gemini solo recibe el conteo agregado.
        resultado_n8n = enviar_a_n8n(
            pregunta=pregunta,
            datos={"total": total},
        )

        if not isinstance(resultado_n8n, dict):
            raise ValueError("Respuesta inesperada de n8n")

        respuesta_ia = resultado_n8n.get("respuesta")

        if not isinstance(respuesta_ia, str) or not respuesta_ia.strip():
            raise ValueError("Respuesta de n8n vacia o invalida")

        respuesta_ia = respuesta_ia.strip()

    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta="No fue posible generar la respuesta.",
            resultado="ERROR",
            detalle="Error en el procesamiento de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible generar la respuesta inteligente",
        ) from exc

    # Validacion basica para la operacion de conteo.
    # Si la IA introduce cantidades diferentes,
    # utilizamos la respuesta exacta de PostgreSQL.
    numeros = re.findall(r"\d+", respuesta_ia)

    if numeros == [str(total)]:
        respuesta_final = respuesta_ia
    else:
        respuesta_final = respuesta_verificada

    registrar_consulta_ia(
        usuario=identificador_usuario,
        pregunta=pregunta,
        respuesta=respuesta_final,
        resultado="EXITO",
        detalle=f"Consulta IA: {operacion}",
    )

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
    }
