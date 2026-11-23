import logging
import os
import uuid
from io import BytesIO
from pathlib import Path

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError
from starlette.datastructures import UploadFile as StarletteUploadFile

from auth import usuario_autenticado
from db import conexion, crear_persona, registrar_auditoria
from schemas import PersonaCrear


# 1. CONFIGURACIÓN DE FASTAPI
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("crear_persona")

app = FastAPI(
    title="Microservicio de creación de personas",
    version="0.1.0"
)

# Permitir solicitudes desde React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
    ],
)

MAX_FOTO_BYTES = 2 * 1024 * 1024
MAX_FOTO_PIXELES = 8_000_000

DIRECTORIO_FOTOS = Path(
    os.environ.get(
        "PERSONAS_FOTOS_DIR",
        "/data/fotografias",
    )
)

# 2. COMPROBAR ESTADO DEL MICROSERVICIO
@app.get("/salud")
def salud():
    try:
        with conexion() as conn:
            conn.execute("SELECT 1").fetchone()

        return {
            "estado": "ok",
            "postgres": "conectado",
        }

    except psycopg.Error as exc:
        log.exception(
            "Error conectando a PostgreSQL"
        )

        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible",
        ) from exc

# 3. AUDITAR UNA CREACIÓN FALLIDA
def auditar_error(datos, usuario, detalle):
    """
    Registra el intento fallido en una
    transacción independiente.
    """

    try:
        with conexion() as conn:
            registrar_auditoria(
                conn=conn,
                usuario=usuario,
                tipo_documento=datos.tipo_documento,
                numero_documento=datos.numero_documento,
                resultado="ERROR",
                detalle=detalle
            )

    except psycopg.Error:
        log.exception("No se pudo registrar auditoría")


        raise HTTPException(
            status_code=503,
            detail="Auditoría no disponible"
        )

#4. EXTRAER DATOS Y FOTOGRAFÍA

async def extraer_datos_y_foto(request: Request):
    """
    Mantiene JSON para el flujo anterior y
    permite multipart con fotografía.
    """

    contenido = request.headers.get(
        "content-type",
        "",
    ).lower()

    foto = None

    if "application/json" in contenido:
        try:
            campos = await request.json()

        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail="JSON inválido",
            ) from exc

        if not isinstance(campos, dict):
            raise HTTPException(
                status_code=422,
                detail="Se esperaba un objeto JSON",
            )

    elif "multipart/form-data" in contenido:
        form = await request.form()

        campos = {
            nombre: form.get(nombre)
            for nombre in PersonaCrear.model_fields
        }

        foto = form.get("fotografia")

        if (
            foto is not None
            and not isinstance(
                foto,
                StarletteUploadFile,
            )
        ):
            raise HTTPException(
                status_code=422,
                detail="La fotografía debe ser un archivo",
            )

    else:
        raise HTTPException(
            status_code=415,
            detail=(
                "Envía application/json "
                "o multipart/form-data"
            ),
        )

    try:
        datos = PersonaCrear.model_validate(campos)

    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(
                include_context=False
            ),
        ) from exc

    return datos, foto

# 5. PROCESAR FOTOGRAFÍA

async def procesar_fotografia(
    foto: StarletteUploadFile | None,
) -> bytes | None:
    """
    Valida contenido real y normaliza a JPEG
    sin metadatos EXIF.
    """

    if foto is None:
        return None

    if foto.content_type not in (
        "image/jpeg",
        "image/png",
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Solo se admiten imágenes JPG y PNG"
            ),
        )

    contenido = await foto.read(
        MAX_FOTO_BYTES + 1
    )

    if (
        not contenido
        or len(contenido) > MAX_FOTO_BYTES
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "La fotografía debe pesar "
                "entre 1 byte y 2 MB"
            ),
        )

    try:
        with Image.open(
            BytesIO(contenido)
        ) as original:

            if original.format not in (
                "JPEG",
                "PNG",
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El archivo no es una imagen "
                        "JPG o PNG válida"
                    ),
                )

            if (
                original.width * original.height
                > MAX_FOTO_PIXELES
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Las dimensiones de la "
                        "fotografía son demasiado grandes"
                    ),
                )

            imagen = ImageOps.exif_transpose(
                original
            )

            imagen.thumbnail(
                (1800, 1800),
                Image.Resampling.LANCZOS,
            )

            if (
                imagen.mode == "RGBA"
                or (
                    imagen.mode == "P"
                    and "transparency" in imagen.info
                )
            ):
                rgba = imagen.convert("RGBA")

                fondo = Image.new(
                    "RGB",
                    rgba.size,
                    (255, 255, 255),
                )

                fondo.paste(
                    rgba,
                    mask=rgba.getchannel("A"),
                )

                imagen = fondo

            else:
                imagen = imagen.convert("RGB")

            salida = BytesIO()

            imagen.save(
                salida,
                format="JPEG",
                quality=85,
                optimize=True,
            )

            foto_final = salida.getvalue()

            if len(foto_final) > MAX_FOTO_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "La fotografía procesada "
                        "supera los 2 MB"
                    ),
                )

            return foto_final

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "La fotografía está dañada "
                "o no es válida"
            ),
        ) from exc

# 6. CREAR PERSONA
@app.post("/personas", status_code=201)
async def registrar_persona(
    request: Request,
    usuario: dict = Depends(usuario_autenticado),
):
    # Se conserva el endpoint y la autenticación.
    datos, foto = await extraer_datos_y_foto(
        request
    )

    imagen = await procesar_fotografia(foto)

    usuario_id = f"roble:{usuario['user_id']}"

    ruta_guardada = None
    creado = False

    try:
        if imagen is not None:
            # Debe montarse un volumen de Docker
            # en este directorio en CotesPC.
            DIRECTORIO_FOTOS.mkdir(
                mode=0o700,
                parents=True,
                exist_ok=True,
            )

            ruta_guardada = (
                DIRECTORIO_FOTOS
                / f"{uuid.uuid4().hex}.jpg"
            )

            with ruta_guardada.open("xb") as archivo:
                archivo.write(imagen)

            ruta_guardada.chmod(0o600)

        persona = crear_persona(
            datos=datos,
            usuario=usuario_id,
            foto_ruta=(
                ruta_guardada.name
                if ruta_guardada
                else None
            ),
        )

        creado = True

        return {
            "mensaje": "Persona creada correctamente",
            "persona": persona,
        }

    except psycopg.errors.UniqueViolation as exc:
        auditar_error(
            datos,
            usuario_id,
            (
                "Intento de crear persona "
                "con documento duplicado"
            ),
        )

        raise HTTPException(
            status_code=409,
            detail=(
                "Ya existe una persona con "
                "ese tipo y número de documento"
            ),
        ) from exc

    except psycopg.errors.CheckViolation as exc:
        auditar_error(
            datos,
            usuario_id,
            (
                "Datos rechazados por restricciones "
                "de la base de datos"
            ),
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Los datos no cumplen las "
                "restricciones de la base de datos"
            ),
        ) from exc

    except psycopg.Error as exc:
        log.exception(
            "Error al registrar persona"
        )

        auditar_error(
            datos,
            usuario_id,
            (
                "Error de base de datos "
                "durante la creación"
            ),
        )

        raise HTTPException(
            status_code=503,
            detail="No se pudo registrar la persona",
        ) from exc

    except OSError as exc:
        log.exception(
            "Error guardando la fotografía"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "No se pudo almacenar la fotografía"
            ),
        ) from exc

    finally:
        # Si PostgreSQL o la auditoría fallan,
        # no conservar una foto huérfana.
        if (
            not creado
            and ruta_guardada is not None
        ):
            try:
                ruta_guardada.unlink(
                    missing_ok=True
                )

            except OSError:
                log.exception(
                    "No se pudo limpiar "
                    "una fotografía fallida"
                )