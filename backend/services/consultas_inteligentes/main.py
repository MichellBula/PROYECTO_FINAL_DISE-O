
import os
import re
from collections import Counter
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado
from db import registrar_consulta_ia
from n8n_cliente import clasificar_pregunta, enviar_a_n8n
from recuperacion import recuperar_informacion


# ==========================================
# CONFIGURACION
# ==========================================

load_dotenv(Path(__file__).with_name(".env"))

app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.6.0",
)


# ==========================================
# MODELO DE SOLICITUD
# ==========================================

class ConsultaIA(BaseModel):
    pregunta: str = Field(
        min_length=1,
        max_length=500,
    )


# ==========================================
# ESTADO DEL MICROSERVICIO
# ==========================================

@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "servicio": "consultas_inteligentes",
    }


# ==========================================
# AUTORIZACION PARA CONSULTAS INDIVIDUALES
# ==========================================

def puede_consultar_identidades(usuario):
    """
    Comprueba si el usuario autenticado con Roble
    tiene permiso para consultar personas individuales.
    """

    configurados = os.getenv(
        "CONSULTAS_IA_USUARIOS_IDENTIFICACION",
        "",
    )

    permitidos = {
        identificador.strip()
        for identificador in configurados.split(",")
        if identificador.strip()
    }

    return str(usuario["user_id"]) in permitidos


# ==========================================
# GENERAR RESPUESTAS EXACTAS
# ==========================================

def respuesta_exacta(operacion, datos, parametros):
    """
    Construye respuestas utilizando exclusivamente
    los resultados obtenidos de PostgreSQL.
    """

    # TOTAL DE PERSONAS
    if operacion == "contar_personas":
        return (
            f"Hay {datos['total']} personas "
            "registradas en el sistema."
        )

    # PERSONAS AGRUPADAS POR GENERO
    if operacion == "contar_por_genero":
        grupos = datos["datos"]

        if not grupos:
            return "No hay personas registradas."

        detalle = "; ".join(
            f"{fila['genero']}: {fila['total']}"
            for fila in grupos
        )

        return f"Personas por género: {detalle}."

    # PERSONAS MAYORES DE EDAD
    if operacion == "contar_mayores_edad":
        return (
            f"Hay {datos['total']} personas "
            "de 18 años o más."
        )

    # PERSONAS MENORES DE EDAD
    if operacion == "contar_menores_edad":
        return (
            f"Hay {datos['total']} personas "
            "menores de 18 años."
        )

    # EDAD PROMEDIO
    if operacion == "promedio_edad":
        valor = datos["promedio"]

        if valor is None:
            return (
                "No hay datos válidos para calcular "
                "la edad promedio."
            )

        return f"La edad promedio es de {valor} años."

    # PERSONAS DE UN GENERO ESPECIFICO
    if operacion == "contar_genero_especifico":
        return (
            f"Hay {datos['total']} personas "
            f"registradas con género {datos['genero']}."
        )

    # ======================================
    # NUEVO: ESTADISTICAS CON FILTROS
    # ======================================

    if operacion == "estadisticas_filtradas":
        coincidencias = datos["coincidencias"]

        if "porcentaje" in datos:
            valor = datos["porcentaje"]

            if valor is None:
                return (
                    "No hay personas registradas para "
                    "calcular el porcentaje."
                )

            return (
                f"Se encontraron {coincidencias} personas "
                "que cumplen los filtros solicitados, "
                f"equivalentes al {valor}% "
                "del total registrado."
            )

        return (
            f"Se encontraron {coincidencias} personas "
            "que cumplen los filtros solicitados."
        )

    # ======================================
    # BUSQUEDA INDIVIDUAL DE PERSONAS
    # ======================================

    if operacion == "buscar_personas":
        personas = datos["personas"]

        if not personas:
            return (
                "No se encontraron personas que "
                "cumplan los criterios de búsqueda."
            )

        if len(personas) == 1:
            persona = personas[0]

            if parametros.get("orden") == "mas_joven":
                prefijo = "La persona más joven encontrada"

            elif parametros.get("orden") == "mas_mayor":
                prefijo = "La persona de mayor edad encontrada"

            else:
                prefijo = "La persona encontrada"

            return (
                f"{prefijo} es {persona['nombre']}, "
                f"con {persona['edad']} años."
            )

        listado = "; ".join(
            f"{persona['nombre']} "
            f"({persona['edad']} años)"
            for persona in personas
        )

        return (
            f"Se muestran {len(personas)} personas "
            f"(máximo {datos['limite']}): {listado}."
        )

    raise ValueError("Operación no soportada")


# ==========================================
# VALIDACION BASICA DE CIFRAS
# ==========================================

def cifras_coinciden(respuesta_ia, verificada):
    """
    Compara las cantidades presentes en la respuesta
    de Gemini con las obtenidas de PostgreSQL.

    Esta validacion no garantiza que toda la respuesta
    generada sea semanticamente correcta.
    """

    numeros_ia = Counter(
        re.findall(
            r"\d+(?:[.,]\d+)?",
            respuesta_ia,
        )
    )

    numeros_verificados = Counter(
        re.findall(
            r"\d+(?:[.,]\d+)?",
            verificada,
        )
    )

    return numeros_ia == numeros_verificados


# ==========================================
# PROCESAR CONSULTA INTELIGENTE
# ==========================================

@app.post("/consultas-ia")
def procesar_consulta(
    consulta: ConsultaIA,
    usuario: dict = Depends(usuario_autenticado),
):

    pregunta = consulta.pregunta.strip()

    identificador = f"roble:{usuario['user_id']}"

    # ======================================
    # FUNCION DE AUDITORIA
    # ======================================

    def auditar(resultado, respuesta, detalle):
        registrar_consulta_ia(
            usuario=identificador,
            pregunta=pregunta,
            respuesta=respuesta,
            resultado=resultado,
            detalle=detalle,
        )

    if not pregunta:
        raise HTTPException(
            status_code=422,
            detail="La pregunta no puede estar vacía",
        )

    # ======================================
    # 1. CLASIFICAR PREGUNTA CON GEMINI
    # ======================================

    try:
        clasificacion = clasificar_pregunta(pregunta)

        operacion = clasificacion["operacion"]
        parametros = clasificacion["parametros"]

    except (
        httpx.HTTPError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:

        auditar(
            "ERROR",
            "No fue posible clasificar la pregunta.",
            "Error en el clasificador de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible clasificar la consulta",
        ) from exc

    # ======================================
    # 2. PREGUNTAS NO RECONOCIDAS
    # ======================================

    if operacion == "NO_RECONOCIDA":

        auditar(
            "DENEGADO",
            "Pregunta fuera del alcance.",
            "Operación no reconocida",
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "La pregunta no corresponde "
                "a una consulta disponible"
            ),
        )

    # ======================================
    # 3. OPERACIONES ESTADISTICAS
    # ======================================

    operaciones_estadisticas = {
        "contar_personas",
        "contar_por_genero",
        "contar_mayores_edad",
        "contar_menores_edad",
        "promedio_edad",
        "contar_genero_especifico",
        "estadisticas_filtradas",
    }

    # ======================================
    # 4. VALIDAR PERMISOS
    # ======================================

    if operacion == "buscar_personas":

        if not puede_consultar_identidades(usuario):

            auditar(
                "DENEGADO",
                "Consulta individual no autorizada.",
                "Sin permiso de identificación",
            )

            raise HTTPException(
                status_code=403,
                detail=(
                    "No tienes permiso para "
                    "consultar identidades"
                ),
            )

    elif operacion not in operaciones_estadisticas:

        auditar(
            "DENEGADO",
            "Operación no autorizada.",
            "Operación no habilitada",
        )

        raise HTTPException(
            status_code=403,
            detail="Esta operación no está habilitada",
        )

    # ======================================
    # 5. RECUPERAR INFORMACION POSTGRESQL
    # ======================================

    try:
        datos = recuperar_informacion(
            operacion,
            parametros,
        )

        verificada = respuesta_exacta(
            operacion,
            datos,
            parametros,
        )

    except ValueError as exc:

        auditar(
            "DENEGADO",
            "Parámetros inválidos.",
            "Validación de filtros",
        )

        raise HTTPException(
            status_code=422,
            detail="Los filtros de consulta no son válidos",
        ) from exc

    except Exception as exc:

        auditar(
            "ERROR",
            "Error al recuperar información.",
            "Error en PostgreSQL",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible recuperar la información",
        ) from exc

    # ======================================
    # 6. GENERAR RESPUESTA MEDIANTE N8N
    # ======================================

    try:
        resultado_ia = enviar_a_n8n(
            pregunta=pregunta,
            datos=datos,
        )

        texto_ia = resultado_ia.get("respuesta")

        if (
            not isinstance(texto_ia, str)
            or not texto_ia.strip()
        ):
            raise ValueError(
                "Respuesta de IA inválida"
            )

    except (
        httpx.HTTPError,
        RuntimeError,
        ValueError,
        AttributeError,
    ) as exc:

        auditar(
            "ERROR",
            "No fue posible generar la respuesta.",
            "Error en el procesamiento de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "No fue posible generar "
                "la respuesta inteligente"
            ),
        ) from exc

    # ======================================
    # 7. VALIDAR LA RESPUESTA GENERADA
    # ======================================

    if operacion == "buscar_personas":
        # Para las consultas individuales usamos
        # directamente los resultados de PostgreSQL.
        respuesta_final = verificada

    elif operacion == "estadisticas_filtradas":
        # Para filtros combinados priorizamos la
        # respuesta calculada por PostgreSQL.
        respuesta_final = verificada

    elif cifras_coinciden(texto_ia, verificada):
        respuesta_final = texto_ia.strip()

    else:
        respuesta_final = verificada

    # ======================================
    # 8. REGISTRAR AUDITORIA
    # ======================================

    auditar(
        "EXITO",
        respuesta_final,
        f"Consulta IA: {operacion}",
    )

    # ======================================
    # 9. RESPONDER AL FRONTEND REACT
    # ======================================

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
    }
