
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


load_dotenv(Path(__file__).with_name(".env"))

app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.5.0",
)


class ConsultaIA(BaseModel):
    pregunta: str = Field(min_length=1, max_length=500)


@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "servicio": "consultas_inteligentes",
    }


def puede_consultar_identidades(usuario):
    """
    Permite consultas individuales solo a los
    identificadores Roble autorizados por el proyecto.
    """
    configurados = os.getenv(
        "CONSULTAS_IA_USUARIOS_IDENTIFICACION", ""
    )

    permitidos = {
        identificador.strip()
        for identificador in configurados.split(",")
        if identificador.strip()
    }

    return str(usuario["user_id"]) in permitidos


def respuesta_exacta(operacion, datos, parametros):
    if operacion == "contar_personas":
        return (
            f"Hay {datos['total']} personas "
            "registradas en el sistema."
        )

    if operacion == "contar_por_genero":
        grupos = datos["datos"]
        if not grupos:
            return "No hay personas registradas."

        detalle = "; ".join(
            f"{fila['genero']}: {fila['total']}"
            for fila in grupos
        )
        return f"Personas por género: {detalle}."

    if operacion == "contar_mayores_edad":
        return (
            f"Hay {datos['total']} personas "
            "de 18 años o más."
        )

    if operacion == "contar_menores_edad":
        return (
            f"Hay {datos['total']} personas "
            "menores de 18 años."
        )

    if operacion == "promedio_edad":
        valor = datos["promedio"]
        if valor is None:
            return "No hay datos válidos para calcular la edad promedio."
        return f"La edad promedio es de {valor} años."

    if operacion == "contar_genero_especifico":
        return (
            f"Hay {datos['total']} personas "
            f"registradas con género {datos['genero']}."
        )

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
            f"{p['nombre']} ({p['edad']} años)"
            for p in personas
        )

        return (
            f"Se muestran {len(personas)} personas "
            f"(máximo {datos['limite']}): {listado}."
        )

    raise ValueError("Operacion no soportada")


def cifras_coinciden(respuesta_ia, verificada):
    numeros_ia = Counter(
        re.findall(r"\d+(?:[.,]\d+)?", respuesta_ia)
    )
    numeros_verificados = Counter(
        re.findall(r"\d+(?:[.,]\d+)?", verificada)
    )

    return numeros_ia == numeros_verificados


@app.post("/consultas-ia")
def procesar_consulta(
    consulta: ConsultaIA,
    usuario: dict = Depends(usuario_autenticado),
):
    pregunta = consulta.pregunta.strip()
    identificador = f"roble:{usuario['user_id']}"

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

    # 1. Clasificar mediante Gemini/n8n.
    try:
        clasificacion = clasificar_pregunta(pregunta)
        operacion = clasificacion["operacion"]
        parametros = clasificacion["parametros"]

    except (httpx.HTTPError, ValueError, RuntimeError) as exc:
        auditar(
            "ERROR",
            "Error de clasificación",
            "Clasificador n8n no disponible",
        )
        raise HTTPException(
            status_code=503,
            detail="No fue posible clasificar la consulta",
        ) from exc

    # 2. Consultas fuera de alcance.
    if operacion == "NO_RECONOCIDA":
        auditar(
            "DENEGADO",
            "Consulta no reconocida",
            "Pregunta fuera de las operaciones disponibles",
        )
        raise HTTPException(
            status_code=422,
            detail="La pregunta no corresponde a una consulta disponible",
        )

    operaciones_estadisticas = {
        "contar_personas",
        "contar_por_genero",
        "contar_mayores_edad",
        "contar_menores_edad",
        "promedio_edad",
        "contar_genero_especifico",
    }

    # 3. Autorización separada para identidades.
    if operacion == "buscar_personas":
        if not puede_consultar_identidades(usuario):
            auditar(
                "DENEGADO",
                "Consulta individual no autorizada",
                "Sin permiso de identificación",
            )
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para consultar identidades",
            )

    elif operacion not in operaciones_estadisticas:
        auditar(
            "DENEGADO",
            "Operación no autorizada",
            "Operación no habilitada",
        )
        raise HTTPException(
            status_code=403,
            detail="Esta operación no está habilitada",
        )

    # 4. Recuperación SQL controlada.
    try:
        datos = recuperar_informacion(
            operacion, parametros
        )
        verificada = respuesta_exacta(
            operacion, datos, parametros
        )

    except ValueError as exc:
        auditar(
            "DENEGADO",
            "Parámetros inválidos",
            "Validación de filtros",
        )
        raise HTTPException(
            status_code=422,
            detail="Los filtros de consulta no son válidos",
        ) from exc

    except Exception as exc:
        auditar(
            "ERROR",
            "Error al recuperar datos",
            "Error en PostgreSQL",
        )
        raise HTTPException(
            status_code=503,
            detail="No fue posible recuperar la información",
        ) from exc

    # 5. Enviar únicamente los resultados autorizados a n8n.
    try:
        resultado_ia = enviar_a_n8n(
            pregunta=pregunta,
            datos=datos,
        )

        texto_ia = resultado_ia.get("respuesta")

        if not isinstance(texto_ia, str) or not texto_ia.strip():
            raise ValueError("Respuesta de IA inválida")

    except (httpx.HTTPError, ValueError, RuntimeError) as exc:
        auditar(
            "ERROR",
            "Error en respuesta IA",
            "Procesamiento n8n fallido",
        )
        raise HTTPException(
            status_code=503,
            detail="No fue posible generar la respuesta inteligente",
        ) from exc

    # 6. Priorizar exactitud en resultados individuales.
    # Las respuestas con nombres se construyen con
    # datos de PostgreSQL, no con nombres inventados.
    if operacion == "buscar_personas":
        respuesta_final = verificada

    elif cifras_coinciden(texto_ia, verificada):
        respuesta_final = texto_ia.strip()

    else:
        respuesta_final = verificada

    # 7. Auditoría y respuesta.
    auditar(
        "EXITO",
        respuesta_final,
        f"Consulta IA: {operacion}",
    )

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
    }
