
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Request

from gestion_seguridad import exigir_usuario


# Cargar la configuración privada del microservicio.
load_dotenv(Path(__file__).with_name(".env"))


def usuario_autenticado(request: Request) -> dict:
    """
    Verifica la sesión de Roble almacenada en PostgreSQL.

    Rechaza las solicitudes sin una sesión válida.
    """

    usuario = exigir_usuario(request)

    # Identificar al usuario para registrar la auditoría.
    request.state.usuario_auditoria = (
        f"roble:{usuario['user_id']}"
    )

    return usuario
