import logging

import psycopg
from psycopg.rows import dict_row

from config import config

logger = logging.getLogger(__name__)


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


def registrar_auditoria(*, usuario: str, resultado: str, detalle: str,
                         tipo_documento: str | None, numero_documento: str | None):
    # NO guardar JWT, contraseñas ni información de la petición sin filtrar.
    with conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO public.auditoria
                   (usuario, tipo_operacion, tipo_documento, numero_documento, resultado, detalle)
                   VALUES (%s, 'CONSULTAR', %s, %s, %s, %s)""",
                (usuario[:255], tipo_documento, numero_documento, resultado, detalle),
            )
