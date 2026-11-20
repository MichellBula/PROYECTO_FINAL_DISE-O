
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Request

from gestion_seguridad import exigir_usuario


# Cargar la configuración privada del microservicio
load_dotenv(Path(__file__).with_name(".env"))


def usuario_autenticado(request: Request) -> dict:
    """
    Verifica que el usuario tenga una sesión
    válida de Roble.

    Si no existe una sesión válida,
    se rechaza la solicitud.
    """

    usuario = exigir_usuario(request)

    # Guardar la identidad para auditoría
    request.state.usuario_auditoria = (
        f"roble:{usuario['user_id']}"
    )

    return usuario
