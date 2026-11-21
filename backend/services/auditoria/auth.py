import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, HTTPException

from gestion_seguridad import exigir_usuario


# Cargar configuración privada
load_dotenv(Path(__file__).with_name(".env"))


def usuario_auditor(
    usuario: dict = Depends(exigir_usuario),
) -> dict:

    # Correos autorizados para consultar auditoría
    permitidos = {
        correo.strip().lower()
        for correo in os.getenv(
            "AUDITORIA_ALLOWED_EMAILS", ""
        ).split(",")
        if correo.strip()
    }

    correo_usuario = str(
        usuario.get("email", "")
    ).strip().lower()

    if not permitidos or correo_usuario not in permitidos:

        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar auditoría",
        )

    return usuario