
from db import conexion


# ==========================================
# CONSULTAS ESTADISTICAS EXISTENTES
# ==========================================

def contar_personas():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS total FROM public.persona"
        )
        return {"total": cur.fetchone()["total"]}


def contar_por_genero():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                COALESCE(genero::text, 'Sin especificar')
                    AS genero,
                COUNT(*) AS total
            FROM public.persona
            GROUP BY genero
            ORDER BY genero
        """)
        return {"datos": cur.fetchall()}


def contar_mayores_edad():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE fecha_nacimiento IS NOT NULL
              AND fecha_nacimiento <= CURRENT_DATE
                  - INTERVAL '18 years'
        """)
        return {"total": cur.fetchone()["total"]}


def contar_menores_edad():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE fecha_nacimiento IS NOT NULL
              AND fecha_nacimiento <= CURRENT_DATE
              AND fecha_nacimiento > CURRENT_DATE
                  - INTERVAL '18 years'
        """)
        return {"total": cur.fetchone()["total"]}


def promedio_edad():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(
                EXTRACT(YEAR FROM AGE(
                    CURRENT_DATE, fecha_nacimiento
                ))
            ) AS promedio
            FROM public.persona
            WHERE fecha_nacimiento IS NOT NULL
              AND fecha_nacimiento <= CURRENT_DATE
        """)
        valor = cur.fetchone()["promedio"]

    return {
        "promedio": (
            round(float(valor), 2)
            if valor is not None
            else None
        )
    }


def contar_genero_especifico(genero):
    if not isinstance(genero, str) or not genero.strip():
        raise ValueError("Genero invalido")

    if len(genero) > 60:
        raise ValueError("Genero demasiado largo")

    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE LOWER(TRIM(genero::text)) = LOWER(%s)
        """, (genero.strip(),))
        total = cur.fetchone()["total"]

    return {"genero": genero.strip(), "total": total}


# ==========================================
# BUSQUEDA FLEXIBLE DE PERSONAS
# ==========================================

def buscar_personas(parametros):
    """
    Busca personas combinando filtros autorizados.

    Admite:
      orden: nombre, mas_joven, mas_mayor
      genero: texto
      nombre: texto
      edad_min: entero
      edad_max: entero
      limite: entero entre 1 y 5

    No devuelve documentos, correos ni otros
    campos que no se necesitan para responder.
    """

    if not isinstance(parametros, dict):
        raise ValueError("Parametros invalidos")

    campos_permitidos = {
        "orden",
        "genero",
        "nombre",
        "edad_min",
        "edad_max",
        "limite",
    }

    if set(parametros) - campos_permitidos:
        raise ValueError("Filtro no permitido")

    orden = parametros.get("orden", "nombre")
    genero = parametros.get("genero")
    nombre = parametros.get("nombre")
    edad_min = parametros.get("edad_min")
    edad_max = parametros.get("edad_max")
    limite = parametros.get("limite", 5)

    if orden not in ("nombre", "mas_joven", "mas_mayor"):
        raise ValueError("Orden no permitido")

    if type(limite) is not int or not 1 <= limite <= 5:
        raise ValueError("Limite no permitido")

    if genero is not None:
        if (
            not isinstance(genero, str)
            or not 1 <= len(genero.strip()) <= 60
        ):
            raise ValueError("Genero invalido")
        genero = genero.strip()

    if nombre is not None:
        if (
            not isinstance(nombre, str)
            or not 1 <= len(nombre.strip()) <= 80
        ):
            raise ValueError("Nombre invalido")
        nombre = nombre.strip()

    for edad in (edad_min, edad_max):
        if edad is not None:
            if type(edad) is not int or not 0 <= edad <= 120:
                raise ValueError("Edad fuera de limites")

    if (
        edad_min is not None
        and edad_max is not None
        and edad_min > edad_max
    ):
        raise ValueError("Rango de edades invalido")

    condiciones = [
        "fecha_nacimiento IS NOT NULL",
        "fecha_nacimiento <= CURRENT_DATE",
    ]
    valores = []

    if genero is not None:
        condiciones.append(
            "LOWER(TRIM(genero::text)) = LOWER(%s)"
        )
        valores.append(genero)

    if nombre is not None:
        condiciones.append("""
            POSITION(
                LOWER(%s) IN LOWER(
                    CONCAT_WS(
                        ' ',
                        primer_nombre,
                        segundo_nombre,
                        apellidos
                    )
                )
            ) > 0
        """)
        valores.append(nombre)

    expresion_edad = """
        EXTRACT(
            YEAR FROM AGE(CURRENT_DATE, fecha_nacimiento)
        )::integer
    """

    if edad_min is not None:
        condiciones.append(
            f"({expresion_edad}) >= %s"
        )
        valores.append(edad_min)

    if edad_max is not None:
        condiciones.append(
            f"({expresion_edad}) <= %s"
        )
        valores.append(edad_max)

    ordenes = {
        "nombre": (
            "primer_nombre ASC, apellidos ASC, "
            "id_persona ASC"
        ),
        "mas_joven": (
            "fecha_nacimiento DESC, id_persona ASC"
        ),
        "mas_mayor": (
            "fecha_nacimiento ASC, id_persona ASC"
        ),
    }

    # Las expresiones SQL se construyen solo a partir
    # de fragmentos constantes definidos arriba.
    # Los valores del usuario siempre son parametros.
    sql = f"""
        SELECT
            CONCAT_WS(
                ' ',
                primer_nombre,
                segundo_nombre,
                apellidos
            ) AS nombre,
            {expresion_edad} AS edad
        FROM public.persona
        WHERE {" AND ".join(condiciones)}
        ORDER BY {ordenes[orden]}
        LIMIT %s
    """

    valores.append(limite)

    with conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(valores))
        personas = cur.fetchall()

    return {
        "personas": personas,
        "cantidad_mostrada": len(personas),
        "limite": limite,
        "orden": orden,
    }


# ==========================================
# OPERACIONES PERMITIDAS POR EL RECUPERADOR
# ==========================================

OPERACIONES_AUTORIZADAS = {
    "contar_personas": contar_personas,
    "contar_por_genero": contar_por_genero,
    "contar_mayores_edad": contar_mayores_edad,
    "contar_menores_edad": contar_menores_edad,
    "promedio_edad": promedio_edad,
    "contar_genero_especifico": contar_genero_especifico,
    "buscar_personas": buscar_personas,
}


def recuperar_informacion(operacion, parametros=None):
    parametros = parametros or {}

    if not isinstance(parametros, dict):
        raise ValueError("Parametros invalidos")

    funcion = OPERACIONES_AUTORIZADAS.get(operacion)

    if funcion is None:
        raise ValueError("Operacion no disponible")

    if operacion == "buscar_personas":
        return funcion(parametros)

    if operacion == "contar_genero_especifico":
        if set(parametros) != {"genero"}:
            raise ValueError("Se requiere el genero")
        return funcion(parametros["genero"])

    if parametros:
        raise ValueError(
            "Esta operacion no acepta parametros"
        )

    return funcion()
