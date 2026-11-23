
"""
Microservicio de consultas inteligentes.

Recuperacion controlada de informacion de PostgreSQL.

Las operaciones SQL son predefinidas.
Gemini solo selecciona operaciones y parametros.
No se permite ejecutar SQL generado por IA.
"""

from db import conexion


# ==========================================
# 1. CONTAR TODAS LAS PERSONAS
# ==========================================

def contar_personas():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
        """)

        resultado = cur.fetchone()

    return {
        "total": resultado["total"],
    }


# ==========================================
# 2. CONTAR PERSONAS POR GENERO
# ==========================================

def contar_por_genero():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                COALESCE(genero::text, 'Sin especificar') AS genero,
                COUNT(*) AS total
            FROM public.persona
            GROUP BY genero
            ORDER BY genero
        """)

        resultados = cur.fetchall()

    return {
        "datos": [
            {
                "genero": fila["genero"],
                "total": fila["total"],
            }
            for fila in resultados
        ],
    }


# ==========================================
# 3. CONTAR MAYORES DE EDAD
# ==========================================

def contar_mayores_edad():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE fecha_nacimiento IS NOT NULL
              AND fecha_nacimiento <= CURRENT_DATE
                  - INTERVAL '18 years'
        """)

        resultado = cur.fetchone()

    return {
        "total": resultado["total"],
    }


# ==========================================
# 4. CONTAR MENORES DE EDAD
# ==========================================

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

        resultado = cur.fetchone()

    return {
        "total": resultado["total"],
    }


# ==========================================
# 5. CALCULAR EDAD PROMEDIO
# ==========================================

def promedio_edad():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(
                EXTRACT(
                    YEAR FROM AGE(
                        CURRENT_DATE,
                        fecha_nacimiento
                    )
                )
            ) AS promedio
            FROM public.persona
            WHERE fecha_nacimiento IS NOT NULL
              AND fecha_nacimiento <= CURRENT_DATE
        """)

        resultado = cur.fetchone()

    promedio = resultado["promedio"]

    return {
        "promedio": (
            round(float(promedio), 2)
            if promedio is not None
            else None
        ),
    }


# ==========================================
# 6. CONTAR PERSONAS DE UN GENERO ESPECIFICO
# ==========================================

def contar_genero_especifico(genero):
    if (
        not isinstance(genero, str)
        or not 1 <= len(genero.strip()) <= 60
    ):
        raise ValueError("Genero invalido")

    genero = genero.strip()

    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE LOWER(TRIM(genero::text)) = LOWER(%s)
        """, (genero,))

        resultado = cur.fetchone()

    return {
        "genero": genero,
        "total": resultado["total"],
    }


# ==========================================
# 7. BUSCAR PERSONAS CON FILTROS
# ==========================================

def buscar_personas(parametros):
    """
    Permite buscar personas utilizando filtros.

    Filtros disponibles:
    - orden: nombre, mas_joven, mas_mayor
    - genero
    - nombre
    - edad_min
    - edad_max
    - limite

    Maximo 5 personas por consulta.
    La autorizacion se realiza en main.py.
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
            if (
                type(edad) is not int
                or not 0 <= edad <= 120
            ):
                raise ValueError("Edad invalida")

    if (
        edad_min is not None
        and edad_max is not None
        and edad_min > edad_max
    ):
        raise ValueError("Rango de edad invalido")

    condiciones = [
        "fecha_nacimiento IS NOT NULL",
        "fecha_nacimiento <= CURRENT_DATE",
    ]

    valores = []

    # FILTRO POR GENERO
    if genero is not None:
        condiciones.append(
            "LOWER(TRIM(genero::text)) = LOWER(%s)"
        )
        valores.append(genero)

    # FILTRO POR NOMBRE
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

    # EXPRESION PARA CALCULAR LA EDAD
    expresion_edad = """
        EXTRACT(
            YEAR FROM AGE(
                CURRENT_DATE,
                fecha_nacimiento
            )
        )::integer
    """

    # EDAD MINIMA
    if edad_min is not None:
        condiciones.append(
            f"({expresion_edad}) >= %s"
        )
        valores.append(edad_min)

    # EDAD MAXIMA
    if edad_max is not None:
        condiciones.append(
            f"({expresion_edad}) <= %s"
        )
        valores.append(edad_max)

    # ORDENAMIENTO CONTROLADO
    ordenes = {
        "nombre": (
            "primer_nombre ASC, "
            "apellidos ASC, "
            "id_persona ASC"
        ),
        "mas_joven": (
            "fecha_nacimiento DESC, "
            "id_persona ASC"
        ),
        "mas_mayor": (
            "fecha_nacimiento ASC, "
            "id_persona ASC"
        ),
    }

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
# 8. ESTADISTICAS CON FILTROS COMBINADOS
# ==========================================

def estadisticas_filtradas(parametros):
    """
    Permite contar personas con filtros combinados.

    Ejemplos:
    - Cuantas mujeres son mayores de edad.
    - Cuantos hombres tienen exactamente 25 anos.
    - Cuantas personas tienen entre 20 y 30 anos.
    - Que porcentaje de personas son menores de edad.

    No devuelve informacion individual.
    """

    if not isinstance(parametros, dict):
        raise ValueError("Parametros invalidos")

    campos_permitidos = {
        "genero",
        "edad_min",
        "edad_max",
        "porcentaje",
    }

    if set(parametros) - campos_permitidos:
        raise ValueError("Filtro no permitido")

    genero = parametros.get("genero")
    edad_min = parametros.get("edad_min")
    edad_max = parametros.get("edad_max")
    porcentaje = parametros.get("porcentaje", False)

    if type(porcentaje) is not bool:
        raise ValueError("Porcentaje invalido")

    condiciones = []
    valores = []

    # FILTRO POR GENERO
    if genero is not None:
        if (
            not isinstance(genero, str)
            or not 1 <= len(genero.strip()) <= 60
        ):
            raise ValueError("Genero invalido")

        condiciones.append(
            "LOWER(TRIM(genero::text)) = LOWER(%s)"
        )
        valores.append(genero.strip())

    # CALCULO DE EDAD
    expresion_edad = """
        EXTRACT(
            YEAR FROM AGE(
                CURRENT_DATE,
                fecha_nacimiento
            )
        )::integer
    """

    # VALIDAR EDADES
    for edad in (edad_min, edad_max):
        if edad is not None:
            if (
                type(edad) is not int
                or not 0 <= edad <= 120
            ):
                raise ValueError("Edad invalida")

    if (
        edad_min is not None
        and edad_max is not None
        and edad_min > edad_max
    ):
        raise ValueError("Rango de edad invalido")

    # EVITAR FECHAS NULAS O FUTURAS
    if edad_min is not None or edad_max is not None:
        condiciones.extend([
            "fecha_nacimiento IS NOT NULL",
            "fecha_nacimiento <= CURRENT_DATE",
        ])

    # EDAD MINIMA
    if edad_min is not None:
        condiciones.append(
            f"({expresion_edad}) >= %s"
        )
        valores.append(edad_min)

    # EDAD MAXIMA
    if edad_max is not None:
        condiciones.append(
            f"({expresion_edad}) <= %s"
        )
        valores.append(edad_max)

    # CONSTRUIR WHERE
    where = (
        "WHERE " + " AND ".join(condiciones)
        if condiciones
        else ""
    )

    # CONSULTA CON FILTROS
    consulta = f"""
        SELECT COUNT(*) AS total
        FROM public.persona
        {where}
    """

    with conexion() as conn, conn.cursor() as cur:
        cur.execute(consulta, tuple(valores))

        coincidencias = cur.fetchone()["total"]

        # TOTAL GENERAL PARA PORCENTAJES
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
        """)

        total_general = cur.fetchone()["total"]

    resultado = {
        "coincidencias": coincidencias,
        "total_general": total_general,
    }

    if porcentaje:
        resultado["porcentaje"] = (
            round(
                coincidencias * 100 / total_general,
                2,
            )
            if total_general > 0
            else None
        )

    return resultado


# ==========================================
# 9. DICCIONARIO DE OPERACIONES
# ==========================================

OPERACIONES_AUTORIZADAS = {
    "contar_personas": contar_personas,
    "contar_por_genero": contar_por_genero,
    "contar_mayores_edad": contar_mayores_edad,
    "contar_menores_edad": contar_menores_edad,
    "promedio_edad": promedio_edad,
    "contar_genero_especifico": contar_genero_especifico,
    "buscar_personas": buscar_personas,
    "estadisticas_filtradas": estadisticas_filtradas,
}


# ==========================================
# 10. RECUPERACION DE INFORMACION
# ==========================================

def recuperar_informacion(operacion, parametros=None):
    """
    Ejecuta solamente operaciones predefinidas.

    La autorizacion de los usuarios se comprueba
    en main.py antes de ejecutar esta funcion.
    """

    parametros = parametros or {}

    if not isinstance(parametros, dict):
        raise ValueError("Parametros invalidos")

    funcion = OPERACIONES_AUTORIZADAS.get(operacion)

    if funcion is None:
        raise ValueError("Operacion no disponible")

    # CONSULTAS ESTADISTICAS CON FILTROS
    if operacion == "estadisticas_filtradas":
        return funcion(parametros)

    # BUSQUEDAS INDIVIDUALES
    if operacion == "buscar_personas":
        return funcion(parametros)

    # CONTEO POR GENERO ESPECIFICO
    if operacion == "contar_genero_especifico":
        if set(parametros) != {"genero"}:
            raise ValueError("Se requiere el genero")

        return funcion(parametros["genero"])

    # OPERACIONES SIN PARAMETROS
    if parametros:
        raise ValueError(
            "Esta operacion no acepta parametros"
        )

    return funcion()
