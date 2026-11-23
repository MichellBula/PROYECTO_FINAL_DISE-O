# ============================================
# REGISTRO DE USUARIOS CON ROBLE
# ============================================

import logging
import os
import re

from pathlib import Path

from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, Request

from pydantic import BaseModel, Field

from roble import RobleClient, RobleError, RobleHttpError


# ============================================
# 1. CONFIGURACIÓN
# ============================================

load_dotenv(Path(__file__).with_name(".env"))

logger = logging.getLogger("gestion.registro")

ROBLE_BASE_URL = os.getenv("ROBLE_BASE_URL", "").strip()

ROBLE_CONTRACT_ID = os.getenv("ROBLE_CONTRACT_ID", "").strip()

ORIGENES = {
    origen.strip().rstrip("/")
    for origen in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://127.0.0.1:8001"
    ).split(",")
    if origen.strip()
}


# ============================================
# 2. RUTAS DEL REGISTRO
# ============================================

router = APIRouter(
    prefix="/auth",
    tags=["Registro de usuarios"]
)


# ============================================
# 3. MODELOS DE DATOS
# ============================================

class DatosRegistro(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    email: str = Field(min_length=5, max_length=255)

    password: str = Field(min_length=8, max_length=128)


class DatosVerificacion(BaseModel):

    email: str = Field(min_length=5, max_length=255)

    code: str = Field(min_length=4, max_length=32)


# ============================================
# 4. VALIDACIÓN DEL ORIGEN
# ============================================

def comprobar_origen(request: Request):

    origen = request.headers.get("origin")

    if origen and origen.rstrip("/") not in ORIGENES:

        raise HTTPException(
            status_code=403,
            detail="Origen no autorizado"
        )


def normalizar_correo(correo: str) -> str:

    correo = correo.strip().lower()

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        correo
    ):

        raise HTTPException(
            status_code=422,
            detail="Correo electrónico inválido"
        )

    return correo


# ============================================
# 5. REGISTRAR USUARIO
# ============================================

@router.post("/registro", status_code=202)
def registrar_usuario(
    datos: DatosRegistro,
    request: Request
):

    comprobar_origen(request)

    correo = normalizar_correo(datos.email)

    nombre = datos.name.strip()

    if len(nombre) < 2:

        raise HTTPException(
            status_code=422,
            detail="El nombre es demasiado corto"
        )

    try:

        with RobleClient(
            base_url=ROBLE_BASE_URL,
            contract_id=ROBLE_CONTRACT_ID
        ) as roble:

            roble.register_with_verification(
                email=correo,
                password=datos.password,
                name=nombre
            )

    except RobleHttpError as error:

        if error.status_code in (400, 409):

            raise HTTPException(
                status_code=400,
                detail="No se pudo registrar la cuenta. Revisa los datos o si el correo ya existe."
            ) from None

        if error.status_code == 429:

            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos. Inténtalo más tarde."
            ) from None

        logger.warning(
            "Roble rechazó el registro: HTTP %s",
            error.status_code
        )

        raise HTTPException(
            status_code=502,
            detail="No se pudo completar el registro con Roble"
        ) from None

    except RobleError:

        logger.exception(
            "Error al solicitar registro en Roble"
        )

        raise HTTPException(
            status_code=502,
            detail="Servicio de registro no disponible"
        ) from None

    return {
        "estado": "pendiente_verificacion",
        "mensaje": "Revisa tu correo para obtener el código de verificación"
    }


# ============================================
# 6. VERIFICAR CORREO ELECTRÓNICO
# ============================================

@router.post("/verificar-correo")
def verificar_correo(
    datos: DatosVerificacion,
    request: Request
):

    comprobar_origen(request)

    correo = normalizar_correo(datos.email)

    try:

        with RobleClient(
            base_url=ROBLE_BASE_URL,
            contract_id=ROBLE_CONTRACT_ID
        ) as roble:

            roble.verify_email(
                email=correo,
                code=datos.code.strip()
            )

    except RobleHttpError as error:

        if error.status_code in (400, 404):

            raise HTTPException(
                status_code=400,
                detail="Código inválido o vencido"
            ) from None

        if error.status_code == 429:

            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos. Inténtalo más tarde."
            ) from None

        logger.warning(
            "Roble rechazó la verificación: HTTP %s",
            error.status_code
        )

        raise HTTPException(
            status_code=502,
            detail="No se pudo verificar el correo"
        ) from None

    except RobleError:

        logger.exception(
            "Error al verificar correo en Roble"
        )

        raise HTTPException(
            status_code=502,
            detail="Servicio de verificación no disponible"
        ) from None

    return {
        "estado": "correo_verificado",
        "mensaje": "Correo verificado. Ya puedes iniciar sesión."
    }