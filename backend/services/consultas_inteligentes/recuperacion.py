
"""
Recuperación controlada de información para consultas inteligentes.

Las operaciones SQL están predefinidas.
No se permite ejecutar SQL generado por el modelo de IA.
"""

from db import conexion


# ============================================
# CONTAR PERSONAS REGISTRADAS
# ============================================

def contar_personas():
    """
    Recupera la cantidad total de personas registradas.
    """

    with conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM public.persona
                """
            )

            resultado = cur.fetchone()

    return {
        "operacion": "contar_personas",
        "total": resultado["total"],
    }


# ============================================
# CONSULTAR PERSONA MÁS JOVEN
# ============================================

def persona_mas_joven():
    """
    Obtiene la persona con la fecha de nacimiento
    más reciente.
    """

    with conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    primer_nombre,
                    segundo_nombre,
                    apellidos,
                    fecha_nacimiento
                FROM public.persona
                ORDER BY
                    fecha_nacimiento DESC,
                    id_persona ASC
                LIMIT 1
                """
            )

            resultado = cur.fetchone()

    if resultado is None:
        return {
            "operacion": "persona_mas_joven",
            "encontrado": False,
            "datos": None,
        }

    return {
        "operacion": "persona_mas_joven",
        "encontrado": True,
        "datos": {
            "primer_nombre": resultado["primer_nombre"],
            "segundo_nombre": resultado["segundo_nombre"],
            "apellidos": resultado["apellidos"],
            "fecha_nacimiento": (
                resultado["fecha_nacimiento"].isoformat()
            ),
        },
    }


# ============================================
# CONTAR PERSONAS POR GÉNERO
# ============================================

def contar_por_genero():
    """
    Recupera la cantidad de personas agrupadas
    por género.
    """

    with conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    genero,
                    COUNT(*) AS total
                FROM public.persona
                GROUP BY genero
                ORDER BY genero
                """
            )

            resultados = cur.fetchall()

    return {
        "operacion": "contar_por_genero",
        "datos": resultados,
    }


# ============================================
# OPERACIONES AUTORIZADAS
# ============================================

OPERACIONES_AUTORIZADAS = {
    "contar_personas": contar_personas,
    "persona_mas_joven": persona_mas_joven,
    "contar_por_genero": contar_por_genero,
}


def recuperar_informacion(operacion: str):
    """
    Ejecuta únicamente operaciones conocidas
    y autorizadas.

    Nunca recibe instrucciones SQL del usuario
    ni del modelo de inteligencia artificial.
    """

    funcion = OPERACIONES_AUTORIZADAS.get(operacion)

    if funcion is None:
        raise ValueError(
            "La operación solicitada no está autorizada"
        )

    return funcion()
