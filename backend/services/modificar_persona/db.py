
import psycopg
from psycopg.rows import dict_row

from config import config


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


def registrar_auditoria(conn, usuario, tipo_documento, numero_documento, resultado, detalle):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.auditoria
                (usuario, tipo_operacion, tipo_documento, numero_documento, resultado, detalle)
            VALUES (%s, 'MODIFICAR', %s, %s, %s, %s)
            """,
            (usuario[:255], tipo_documento, numero_documento, resultado, detalle),
        )


def modificar_persona_db(
    datos,
    tipo_doc_original,
    numero_documento,
    usuario,
    *,
    accion_foto="conservar",
    nombre_foto=None,
):
    """Retorna (persona_actualizada, foto_anterior). Todo el SQL y auditoría son transaccionales."""
    if accion_foto not in {"conservar", "reemplazar", "quitar"}:
        raise ValueError("Acción de fotografía no válida")
    if accion_foto == "reemplazar" and not nombre_foto:
        raise ValueError("Falta la nueva fotografía")

    with conexion() as conn:
        with conn.cursor() as cur:
            # Bloquea la fila durante el cambio para recuperar la ruta anterior de forma consistente.
            cur.execute(
                """
                SELECT foto_ruta
                FROM public.persona
                WHERE tipo_documento = %s AND numero_documento = %s
                FOR UPDATE
                """,
                (tipo_doc_original, numero_documento),
            )
            anterior = cur.fetchone()
            if anterior is None:
                return None, None

            foto_anterior = anterior["foto_ruta"]
            columnas_foto = ""
            parametros_foto = []
            if accion_foto == "reemplazar":
                columnas_foto = ", foto_ruta = %s"
                parametros_foto.append(nombre_foto)
            elif accion_foto == "quitar":
                columnas_foto = ", foto_ruta = NULL"

            cur.execute(
                f"""
                UPDATE public.persona
                SET tipo_documento = %s,
                    primer_nombre = %s,
                    segundo_nombre = %s,
                    apellidos = %s,
                    fecha_nacimiento = %s,
                    genero = %s,
                    correo = %s,
                    celular = %s
                    {columnas_foto}
                WHERE tipo_documento = %s AND numero_documento = %s
                RETURNING *
                """,
                (
                    datos.tipo_documento,
                    datos.primer_nombre,
                    datos.segundo_nombre,
                    datos.apellidos,
                    datos.fecha_nacimiento,
                    datos.genero,
                    datos.correo,
                    datos.celular,
                    *parametros_foto,
                    tipo_doc_original,
                    numero_documento,
                ),
            )
            persona = cur.fetchone()
            if persona is None:
                return None, None

        registrar_auditoria(
            conn=conn,
            usuario=usuario,
            tipo_documento=datos.tipo_documento,
            numero_documento=numero_documento,
            resultado="EXITO",
            detalle=f"Persona modificada; fotografía: {accion_foto}",
        )
    return persona, foto_anterior