
import psycopg
from psycopg.rows import dict_row

from config import config


# 1. CONEXIÓN A POSTGRESQL
def conexion():
    return psycopg.connect(
        host=config.PGHOST,
        port=config.PGPORT,
        dbname=config.PGDATABASE,
        user=config.PGUSER,
        password=config.PGPASSWORD,
        connect_timeout=5,
        row_factory=dict_row,
    )


# 2. REGISTRAR AUDITORÍA
def registrar_auditoria(
    conn,
    usuario,
    tipo_documento,
    numero_documento,
    resultado,
    detalle,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.auditoria
            (
                usuario,
                tipo_operacion,
                tipo_documento,
                numero_documento,
                resultado,
                detalle
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                usuario[:255],
                "CREAR",
                tipo_documento,
                numero_documento,
                resultado,
                detalle,
            ),
        )


# 3. CREAR PERSONA
def crear_persona(datos, usuario):

    with conexion() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO public.persona
                (
                    tipo_documento,
                    numero_documento,
                    primer_nombre,
                    segundo_nombre,
                    apellidos,
                    fecha_nacimiento,
                    genero,
                    correo,
                    celular
                )
                VALUES
                (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
                RETURNING
                    id_persona,
                    tipo_documento,
                    numero_documento,
                    primer_nombre,
                    segundo_nombre,
                    apellidos,
                    fecha_nacimiento,
                    genero,
                    correo,
                    celular,
                    foto_ruta,
                    fecha_registro
                """,
                (
                    datos.tipo_documento,
                    datos.numero_documento,
                    datos.primer_nombre,
                    datos.segundo_nombre,
                    datos.apellidos,
                    datos.fecha_nacimiento,
                    datos.genero,
                    datos.correo,
                    datos.celular,
                ),
            )

            persona = cur.fetchone()

        # Registrar la operación exitosa
        registrar_auditoria(
            conn=conn,
            usuario=usuario,
            tipo_documento=datos.tipo_documento,
            numero_documento=datos.numero_documento,
            resultado="EXITO",
            detalle="Persona creada correctamente",
        )

        # Ambos INSERT se confirman juntos
        # al terminar el bloque de conexión.

    return persona
