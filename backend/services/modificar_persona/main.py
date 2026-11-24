
import logging
import os
import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError

from auth import usuario_autenticado
from db import conexion, modificar_persona_db, registrar_auditoria
from schemas import PersonaModificar

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("modificar_persona")

app = FastAPI(title="Microservicio de modificación de personas", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "PUT"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

MAX_FOTO_BYTES = 2 * 1024 * 1024
MAX_FOTO_PIXELES = 8_000_000
DIRECTORIO_FOTOS = Path(os.getenv("PERSONAS_FOTOS_DIR", "/data/fotografias"))


def auditar_error(usuario, tipo_doc, numero, detalle):
    try:
        with conexion() as conn:
            registrar_auditoria(conn, usuario, tipo_doc, numero, "ERROR", detalle)
    except psycopg.Error:
        log.exception("No se pudo registrar el intento fallido de modificación")


async def procesar_foto(foto: UploadFile) -> bytes:
    if foto.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(400, "La fotografía debe ser JPG o PNG")

    contenido = await foto.read(MAX_FOTO_BYTES + 1)
    if not contenido or len(contenido) > MAX_FOTO_BYTES:
        raise HTTPException(400, "La fotografía no puede estar vacía ni superar los 2 MB")

    try:
        with Image.open(BytesIO(contenido)) as original:
            if original.format not in ("JPEG", "PNG"):
                raise HTTPException(400, "El contenido no es una imagen JPG o PNG")
            if original.width * original.height > MAX_FOTO_PIXELES:
                raise HTTPException(400, "La imagen tiene demasiados píxeles")

            imagen = ImageOps.exif_transpose(original)
            imagen.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            if imagen.mode == "RGBA" or (imagen.mode == "P" and "transparency" in imagen.info):
                rgba = imagen.convert("RGBA")
                fondo = Image.new("RGB", rgba.size, "white")
                fondo.paste(rgba, mask=rgba.getchannel("A"))
                imagen = fondo
            else:
                imagen = imagen.convert("RGB")

            salida = BytesIO()
            imagen.save(salida, format="JPEG", quality=85, optimize=True)
            final = salida.getvalue()
            if len(final) > MAX_FOTO_BYTES:
                raise HTTPException(400, "La fotografía procesada supera los 2 MB")
            return final
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(400, "La imagen está dañada o no es válida") from exc


def borrar_foto_propia(nombre: str | None):
    """Solo elimina archivos con el formato nuevo (UUID.jpg) del directorio compartido."""
    if nombre and re.fullmatch(r"[0-9a-f]{32}\.jpg", nombre):
        try:
            (DIRECTORIO_FOTOS / nombre).unlink(missing_ok=True)
        except OSError:
            log.exception("No se pudo eliminar una fotografía antigua")


@app.get("/salud")
def salud():
    try:
        with conexion() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"estado": "ok", "postgres": "conectado"}
    except psycopg.Error as exc:
        log.exception("Error conectando a PostgreSQL")
        raise HTTPException(503, "Base de datos no disponible") from exc


@app.put("/modificar-persona/personas/{tipo_doc_original}/{numero_documento}")
async def modificar_persona_endpoint(
    tipo_doc_original: str,
    numero_documento: str,
    tipo_documento: str = Form(...),
    primer_nombre: str = Form(...),
    segundo_nombre: str | None = Form(None),
    apellidos: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    correo: str | None = Form(None),
    celular: str | None = Form(None),
    accion_foto: Literal["conservar", "reemplazar", "quitar"] = Form("conservar"),
    foto: UploadFile | None = File(None),
    usuario: dict = Depends(usuario_autenticado),
):
    usuario_id = f"roble:{usuario['user_id']}"
    if not re.fullmatch(r"[0-9]{1,10}", numero_documento):
        raise HTTPException(422, "Número de documento no válido")

    try:
        datos = PersonaModificar(
            tipo_documento=tipo_documento,
            primer_nombre=primer_nombre,
            segundo_nombre=segundo_nombre,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            correo=correo,
            celular=celular,
        )
    except ValidationError as exc:
        auditar_error(usuario_id, tipo_doc_original, numero_documento, "Validación fallida")
        raise HTTPException(422, "Los datos enviados no cumplen las validaciones") from exc

    if accion_foto == "reemplazar" and foto is None:
        raise HTTPException(422, "Selecciona una fotografía para reemplazar la actual")
    if accion_foto != "reemplazar" and foto is not None:
        raise HTTPException(422, "La fotografía solo puede enviarse al elegir reemplazar")

    nombre_nuevo = None
    confirmado = False
    try:
        if foto is not None:
            contenido = await procesar_foto(foto)
            DIRECTORIO_FOTOS.mkdir(parents=True, exist_ok=True, mode=0o700)
            nombre_nuevo = f"{uuid.uuid4().hex}.jpg"
            ruta_nueva = DIRECTORIO_FOTOS / nombre_nuevo
            with ruta_nueva.open("xb") as destino:
                destino.write(contenido)
            ruta_nueva.chmod(0o600)

        try:
            persona, foto_anterior = modificar_persona_db(
                datos=datos,
                tipo_doc_original=tipo_doc_original,
                numero_documento=numero_documento,
                usuario=usuario_id,
                accion_foto=accion_foto,
                nombre_foto=nombre_nuevo,
            )
        except psycopg.errors.UniqueViolation as exc:
            auditar_error(usuario_id, tipo_doc_original, numero_documento, "Documento duplicado al modificar")
            raise HTTPException(409, "Ya existe otra persona con ese tipo y número de documento") from exc
        except psycopg.Error as exc:
            log.exception("Error de PostgreSQL al modificar")
            auditar_error(usuario_id, tipo_doc_original, numero_documento, "Error de base de datos")
            raise HTTPException(503, "No se pudo modificar la persona") from exc

        if persona is None:
            auditar_error(usuario_id, tipo_doc_original, numero_documento, "Persona no encontrada")
            raise HTTPException(404, "Persona no encontrada")

        confirmado = True  # El bloque de conexión confirmó el UPDATE y la auditoría.
        if accion_foto in {"reemplazar", "quitar"}:
            borrar_foto_propia(foto_anterior)

        return {"mensaje": "Persona actualizada correctamente", "persona": persona}

    except OSError as exc:
        log.exception("No se pudo escribir la fotografía")
        raise HTTPException(503, "No se pudo almacenar la fotografía") from exc
    finally:
        if not confirmado:
            borrar_foto_propia(nombre_nuevo)