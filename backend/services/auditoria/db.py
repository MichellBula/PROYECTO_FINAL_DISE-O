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
# CONSULTAR AUDITORÍA
# ============================================

def buscar_auditorias(
    tipo_documento=None,
    numero_documento=None,
    tipo_operacion=None,
    resultado=None,
    fecha_desde=None,
    fecha_hasta=None,
    pagina=1,
    limite=50,
    usuario="",
):

    filtros = []
    parametros = []

    # FILTRO: TIPO DE DOCUMENTO
    if tipo_documento:
        filtros.append("tipo_documento = %s")
        parametros.append(tipo_documento)

    # FILTRO: NÚMERO DE DOCUMENTO
    if numero_documento:
        filtros.append("numero_documento = %s")
        parametros.append(numero_documento)

    # FILTRO: OPERACIÓN
    if tipo_operacion:
        filtros.append("tipo_operacion = %s")
        parametros.append(tipo_operacion)

    # FILTRO: RESULTADO
    if resultado:
        filtros.append("resultado = %s")
        parametros.append(resultado)

    # FILTRO: FECHA INICIAL
    if fecha_desde:
        filtros.append(
            "fecha_transaccion >= %s::date"
        )
        parametros.append(fecha_desde)

    # FILTRO: FECHA FINAL
    if fecha_hasta:
        filtros.append(
            "fecha_transaccion < "
            "(%s::date + INTERVAL '1 day')"
        )
        parametros.append(fecha_hasta)

    # Construir WHERE con campos conocidos
    where_sql = ""

    if filtros:
        where_sql = "WHERE " + " AND ".join(filtros)

    desplazamiento = (pagina - 1) * limite

    with conexion() as conn:

        # CONTAR RESULTADOS
        consulta_total = f"""
            SELECT COUNT(*) AS total
            FROM public.auditoria
            {where_sql}
        """

        total = conn.execute(
            consulta_total,
            tuple(parametros),
        ).fetchone()["total"]

        # OBTENER RESULTADOS
        consulta = f"""
            SELECT
                id_auditoria,
                usuario,
                tipo_operacion,
                tipo_documento,
                numero_documento,
                fecha_transaccion,
                resultado,
                detalle,
                pregunta,
                respuesta
            FROM public.auditoria
            {where_sql}
            ORDER BY
                fecha_transaccion DESC,
                id_auditoria DESC
            LIMIT %s OFFSET %s
        """

        registros = conn.execute(
            consulta,
            tuple(
                parametros + [limite, desplazamiento]
            ),
        ).fetchall()

        # REGISTRAR LA CONSULTA DE AUDITORÍA
        conn.execute(
            """
            INSERT INTO public.auditoria
            (
                usuario,
                tipo_operacion,
                resultado,
                detalle
            )
            VALUES
            (
                %s,
                'CONSULTAR_AUDITORIA',
                'EXITO',
                %s
            )
            """,
            (
                usuario[:255],
                "Consulta autorizada del historial de auditoría",
            ),
        )

    return {
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "registros": registros,
    }