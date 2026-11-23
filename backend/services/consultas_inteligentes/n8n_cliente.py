
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))


def _configuracion(nombre_url: str):
    url = os.getenv(nombre_url)
    clave = os.getenv("N8N_INTERNAL_API_KEY")

    if not url or not clave:
        raise RuntimeError(
            "Falta configurar la conexion con n8n"
        )

    return url, {"X-Internal-API-Key": clave}


def enviar_a_n8n(pregunta: str, datos: dict) -> dict:
    """
    Envia a n8n solamente los datos recuperados
    y autorizados por el microservicio.
    """
    url, encabezados = _configuracion("N8N_WEBHOOK_URL")

    with httpx.Client(timeout=30.0) as cliente:
        respuesta = cliente.post(
            url,
            json={
                "pregunta": pregunta,
                "datos": datos,
            },
            headers=encabezados,
        )

        respuesta.raise_for_status()
        contenido = respuesta.json()

    if not isinstance(contenido, dict):
        raise ValueError(
            "Respuesta invalida del procesador de n8n"
        )

    return contenido


def clasificar_pregunta(pregunta: str) -> dict:
    """
    Solicita a Gemini, mediante n8n, la operacion
    y sus parametros.

    Gemini no ejecuta SQL.

    Se acepta temporalmente la clasificacion antigua
    que solo contenia la operacion.
    """
    url, encabezados = _configuracion(
        "N8N_CLASIFICADOR_URL"
    )

    with httpx.Client(timeout=30.0) as cliente:
        respuesta = cliente.post(
            url,
            json={"pregunta": pregunta},
            headers=encabezados,
        )

        respuesta.raise_for_status()
        contenido = respuesta.json()

    if not isinstance(contenido, dict):
        raise ValueError(
            "Respuesta invalida del clasificador"
        )

    operacion = contenido.get("operacion")
    parametros = contenido.get("parametros", {})

    if (
        not isinstance(operacion, str)
        or not operacion.strip()
    ):
        raise ValueError("Operacion invalida")

    if not isinstance(parametros, dict):
        raise ValueError("Parametros invalidos")

    if len(parametros) > 3 or len(operacion) > 80:
        raise ValueError(
            "Clasificacion fuera de limites"
        )

    return {
        "operacion": operacion.strip(),
        "parametros": parametros,
    }

