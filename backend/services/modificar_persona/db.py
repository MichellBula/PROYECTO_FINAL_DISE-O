
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
def modificar_persona_db(datos, tipo_doc_original, numero_documento, usuario, nombre_foto=None):
    with conexion() as conn:
        with conn.cursor() as cur:
            
            # El UPDATE ahora puede cambiar el tipo_documento
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
                datos.tipo_documento, 
                datos.primer_nombre, datos.segundo_nombre, datos.apellidos,
                datos.fecha_nacimiento, datos.genero, datos.correo, datos.celular,
            ]

            if nombre_foto:
                query += ", foto_ruta = %s"
                params.append(nombre_foto)

            # BUSCAMOS SOLO POR EL NÚMERO DE DOCUMENTO PARA EVITAR PROBLEMAS CON TILDES
            query += " WHERE numero_documento = %s RETURNING *"
            params.append(numero_documento)

            cur.execute(query, tuple(params))
            persona = cur.fetchone()

            if not persona:
                return None

        # Registrar la operación exitosa
        registrar_auditoria(
            conn=conn, usuario=usuario, tipo_documento=datos.tipo_documento,
            numero_documento=numero_documento, resultado="EXITO",
            detalle=f"Persona modificada de {tipo_doc_original} a {datos.tipo_documento}",
        )
    return persona