
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
                "ELIMINAR",
                tipo_documento,
                numero_documento,
                resultado,
                detalle,
            ),
        )


def obtener_persona_para_eliminacion_db(tipo_documento, numero_documento):
    """Obtiene únicamente los datos necesarios para confirmar la eliminación."""
    with conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tipo_documento, numero_documento, primer_nombre,
                       segundo_nombre, apellidos, correo, celular
                FROM public.persona
                WHERE tipo_documento = %s AND numero_documento = %s
                """,
                (tipo_documento, numero_documento),
            )
            return cur.fetchone()


# 3. ELIMINAR PERSONA
def eliminar_persona_db(tipo_documento, numero_documento, usuario):
    with conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM public.persona
                WHERE tipo_documento = %s
                  AND numero_documento = %s
                RETURNING tipo_documento, numero_documento
                """,
                (tipo_documento, numero_documento),
            )

            persona = cur.fetchone()

        if not persona:
            return None

        registrar_auditoria(
            conn=conn,
            usuario=usuario,
            tipo_documento=persona["tipo_documento"],
            numero_documento=persona["numero_documento"],
            resultado="EXITO",
            detalle="Persona eliminada correctamente",
        )

    return persona
