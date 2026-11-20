import logging
import os
import shutil
import psycopg 
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from auth import usuario_autenticado
from db import conexion, modificar_persona_db, registrar_auditoria
from schemas import PersonaModificar

# 1. CONFIGURACIÓN DE FASTAPI
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("modificar_persona")

app = FastAPI(
    title="Microservicio de modificación de personas",
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
    allow_methods=["PUT", "POST", "GET"], 
    allow_headers=["Authorization", "Content-Type"],
)

# 2. COMPROBAR ESTADO DEL MICROSERVICIO
@app.get("/salud")
def salud():
    try:
        with conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

        return {
            "estado": "ok",
            "postgres": "conectado"
        }

    except psycopg.Error:
        log.exception("Error conectando a PostgreSQL")
        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible"
        )

# 3. MODIFICAR PERSONA
@app.put("/modificar-persona/personas/{numero_documento}")
async def modificar_persona_endpoint(
    numero_documento: str,
    tipo_documento: str = Form(...),
    primer_nombre: str = Form(...),
    segundo_nombre: Optional[str] = Form(None),
    apellidos: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    correo: Optional[str] = Form(None),
    celular: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    usuario: dict = Depends(usuario_autenticado)
):
    usuario_id = f"roble:{usuario['user_id']}"

    # 1. Validar datos con Pydantic
    try:
        datos_validados = PersonaModificar(
            tipo_documento=tipo_documento,
            primer_nombre=primer_nombre,
            segundo_nombre=segundo_nombre,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            correo=correo,
            celular=celular
        )
    except Exception as e:
        # Si falla la validación, auditamos el error
        with conexion() as conn:
            registrar_auditoria(conn, usuario_id, tipo_documento, numero_documento, "ERROR", f"Validación fallida: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

    # 2. Manejo de la foto
    nombre_foto = None
    if foto:
        contenido = await foto.read()
        # Validar tamaño máximo 2MB
        if len(contenido) > 2 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La imagen supera los 2MB permitidos")
        
        # Asegurarnos de que la carpeta existe
        os.makedirs("uploads", exist_ok=True)
        
        # Creamos un nombre de archivo único
        nombre_foto = f"{numero_documento}_{foto.filename}"
        ruta_foto = f"uploads/{nombre_foto}"
        
        # Volvemos a leer el archivo porque .read() lo consume
        await foto.seek(0)
        with open(ruta_foto, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)

    # 3. Guardar en Base de Datos
    try:
        persona_actualizada = modificar_persona_db(
	    datos=datos_validados, numero_documento=numero_documento,usuario=usuario_id, foto_ruta=nombre_foto
        )

        if not persona_actualizada:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        return {"mensaje": "Persona actualizada correctamente", "persona": persona_actualizada}

    except psycopg.Error:
        log.exception("Error al modificar persona")
        with conexion() as conn:
            registrar_auditoria(conn, usuario_id, tipo_documento, numero_documento, "ERROR", "Error de base de datos")
        raise HTTPException(status_code=503, detail="No se pudo modificar la persona")
