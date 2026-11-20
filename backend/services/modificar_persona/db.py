
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
                "MODIFICAR",
                tipo_documento,
                numero_documento,
                resultado,
                detalle,
            ),
        )


# 3. MODIFICAR PERSONA
def modificar_persona_db(datos, numero_documento, usuario, foto_ruta=None):
    with conexion() as conn:
        with conn.cursor() as cur:
            
            # Armamos la consulta dinamicamente por si la foto es opcional
            query = """
                UPDATE public.persona
                SET tipo_documento = %s,
                    primer_nombre = %s,
                    segundo_nombre = %s,
                    apellidos = %s,
                    fecha_nacimiento = %s,
                    genero = %s,
                    correo = %s,
                    celular = %s
            """
            params = [
                datos.tipo_documento, datos.primer_nombre, datos.segundo_nombre,
                datos.apellidos, datos.fecha_nacimiento, datos.genero,
                datos.correo, datos.celular
            ]

            # Si el usuario subió una foto nueva, la actualizamos
            if foto_ruta:
                query += ", foto_ruta = %s"
                params.append(foto_ruta)

            query += " WHERE numero_documento = %s RETURNING *"
            params.append(numero_documento)

            cur.execute(query, tuple(params))
            persona = cur.fetchone()

        # Si no encontró a nadie, la persona no existe
        if not persona:
            return None

        # Registrar la operación exitosa
        registrar_auditoria(
            conn=conn,
            usuario=usuario,
            tipo_documento=datos.tipo_documento,
            numero_documento=numero_documento,
            resultado="EXITO",
            detalle="Persona modificada correctamente",
        )
    return persona