import logging
import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    allow_methods=["POST", "GET"],
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


# 4. CREAR PERSONA
@app.post("/personas", status_code=201)
def registrar_persona(
    datos: PersonaCrear,
    usuario: dict = Depends(usuario_autenticado)
):

    # Identificar al usuario autenticado
    usuario_id = f"roble:{usuario['user_id']}"

    try:

        # Guardar persona y auditoría
        persona = crear_persona(
            datos=datos,
            usuario=usuario_id
        )

        return {
            "mensaje": "Persona creada correctamente",
            "persona": persona
        }

    # DOCUMENTO DUPLICADO
    except psycopg.errors.UniqueViolation:

        auditar_error(
            datos=datos,
            usuario=usuario_id,
            detalle="Intento de crear persona con documento duplicado"
        )

        raise HTTPException(
            status_code=409,
            detail="Ya existe una persona con ese tipo y número de documento"
        )

    # DATOS QUE INCUMPLEN RESTRICCIONES DE POSTGRESQL
    except psycopg.errors.CheckViolation:

        auditar_error(
            datos=datos,
            usuario=usuario_id,
            detalle="Datos rechazados por las restricciones de la base de datos"
        )

        raise HTTPException(
            status_code=422,
            detail="Los datos no cumplen las restricciones de la base de datos"
        )

    # ERRORES DE POSTGRESQL
    except psycopg.Error:

        log.exception("Error al registrar persona")

        auditar_error(
            datos=datos,
            usuario=usuario_id,
            detalle="Error de base de datos durante la creación"
        )

        raise HTTPException(
            status_code=503,
            detail="No se pudo registrar la persona"
        )
