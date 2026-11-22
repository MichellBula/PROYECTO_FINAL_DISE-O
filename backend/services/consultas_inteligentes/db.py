
import psycopg
from psycopg.rows import dict_row

from config import config


# ============================================
# CONEXIÓN A POSTGRESQL
# ============================================

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


# ============================================
# REGISTRAR CONSULTA INTELIGENTE
# ============================================

def registrar_consulta_ia(
    *,
    usuario: str,
    pregunta: str,
    respuesta: str,
    resultado: str,
    detalle: str,
):
    """
    Registra una consulta inteligente en auditoría.

    No almacena contraseñas, cookies ni tokens.
    """

    with conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.auditoria
                (
                    usuario,
                    tipo_operacion,
                    resultado,
                    detalle,
                    pregunta,
                    respuesta
                )
                VALUES
                (
                    %s,
                    'CONSULTA_IA',
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    usuario[:255],
                    resultado,
                    detalle,
                    pregunta,
                    respuesta,
                ),
            )
