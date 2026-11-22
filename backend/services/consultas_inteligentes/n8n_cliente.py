
import os

import httpx
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(Path(__file__).with_name(".env"))


def enviar_a_n8n(pregunta: str, datos: dict) -> dict:
    """
    Envia a n8n una pregunta y datos previamente
    recuperados y autorizados por el microservicio.
    """

    url = os.getenv("N8N_WEBHOOK_URL")
    clave = os.getenv("N8N_INTERNAL_API_KEY")

    if not url or not clave:
        raise RuntimeError(
            "Falta configurar la conexion con n8n"
        )

    payload = {
        "pregunta": pregunta,
        "datos": datos,
    }

    with httpx.Client(timeout=30.0) as cliente:
        respuesta = cliente.post(
            url,
            json=payload,
            headers={
                "X-Internal-API-Key": clave,
            },
        )

        respuesta.raise_for_status()

        return respuesta.json()
