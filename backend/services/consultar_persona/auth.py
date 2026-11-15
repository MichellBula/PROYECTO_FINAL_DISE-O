
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Request

from gestion_seguridad import exigir_usuario


# Cargar la configuración privada de este microservicio.
load_dotenv(Path(__file__).with_name(".env"))


def usuario_autenticado(request: Request) -> dict:
    """
    Verifica la cookie de sesión compartida en PostgreSQL.

    Si no existe una sesión válida, exigir_usuario
    devuelve HTTP 401 o 503 según corresponda.
    """

    usuario = exigir_usuario(request)

    # Identidad que utilizará la auditoría.
    request.state.usuario_auditoria = (
        f"roble:{usuario['user_id']}"
    )

    return usuario
