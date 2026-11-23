
"""
Recuperacion de informacion desde PostgreSQL.

Todas las consultas son de solo lectura.
Gemini no genera ni ejecuta instrucciones SQL.
"""

from db import conexion


# ==========================================
# TOTAL DE PERSONAS
# ==========================================

def contar_personas():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
        """)

        total = cur.fetchone()["total"]

    return {"total": total}


# ==========================================
# PERSONAS AGRUPADAS POR GENERO
# ==========================================

def contar_por_genero():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                COALESCE(genero, 'Sin especificar')
                    AS genero,
                COUNT(*) AS total
            FROM public.persona
            GROUP BY
                COALESCE(genero, 'Sin especificar')
            ORDER BY genero
        """)

        filas = cur.fetchall()

    return {
        "datos": [
            {
                "genero": fila["genero"],
                "total": fila["total"],
            }
            for fila in filas
        ]
    }


# ==========================================
# MAYORES DE EDAD
# ==========================================

def contar_mayores_edad():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE fecha_nacimiento IS NOT NULL
              AND fecha_nacimiento <=
                  CURRENT_DATE - INTERVAL '18 years'
        """)

        total = cur.fetchone()["total"]

    return {"total": total}


# ==========================================
# MENORES DE EDAD
# ==========================================

def contar_menores_edad():
    with conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE fecha_nacimiento IS NOT NULL
              AND fecha_nacimiento >
                  CURRENT_DATE - INTERVAL '18 years'
        """)

        total = cur.fetchone()["total"]

    return {"total": total}


# ==========================================
# EDAD PROMEDIO
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

        valor = cur.fetchone()["promedio"]

    return {
        "promedio": (
            round(float(valor), 2)
            if valor is not None
            else None
        )
    }


# ==========================================
# CONTAR UN GENERO ESPECIFICO
# ==========================================

def contar_genero_especifico(genero: str):
    if (
        not isinstance(genero, str)
        or not 1 <= len(genero.strip()) <= 60
    ):
        raise ValueError("Genero invalido")

    genero = genero.strip()

    with conexion() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM public.persona
            WHERE LOWER(TRIM(genero)) = LOWER(%s)
            """,
            (genero,),
        )

        total = cur.fetchone()["total"]

    return {
        "genero": genero,
        "total": total,
    }


# ==========================================
# OPERACIONES DISPONIBLES
# ==========================================

OPERACIONES_AUTORIZADAS = {
    "contar_personas": contar_personas,
    "contar_por_genero": contar_por_genero,
    "contar_mayores_edad": contar_mayores_edad,
    "contar_menores_edad": contar_menores_edad,
    "promedio_edad": promedio_edad,
    "contar_genero_especifico": contar_genero_especifico,
}


# ==========================================
# EJECUTAR RECUPERACION
# ==========================================

def recuperar_informacion(
    operacion: str,
    parametros=None,
) -> dict:

    parametros = parametros or {}

    if not isinstance(parametros, dict):
        raise ValueError("Parametros invalidos")

    funcion = OPERACIONES_AUTORIZADAS.get(operacion)

    if funcion is None:
        raise ValueError("Operacion no disponible")

    if operacion == "contar_genero_especifico":
        if set(parametros) != {"genero"}:
            raise ValueError(
                "Se requiere solamente el parametro genero"
            )

        return funcion(parametros["genero"])

    if parametros:
        raise ValueError(
            "La operacion no admite parametros"
        )

    return funcion()
