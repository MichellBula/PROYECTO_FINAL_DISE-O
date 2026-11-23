
import re

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado
from db import registrar_consulta_ia
from n8n_cliente import clasificar_pregunta, enviar_a_n8n
from recuperacion import recuperar_informacion


# ============================================
# MICROSERVICIO DE CONSULTAS INTELIGENTES
# ============================================

app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.3.0",
)


# ============================================
# MODELO DE SOLICITUD
# ============================================

class ConsultaIA(BaseModel):
    pregunta: str = Field(
        min_length=1,
        max_length=500,
    )


# ============================================
# COMPROBAR ESTADO DEL MICROSERVICIO
# ============================================

@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "servicio": "consultas_inteligentes",
    }


# ============================================
# PROCESAR CONSULTA INTELIGENTE
# ============================================

@app.post("/consultas-ia")
def procesar_consulta(
    consulta: ConsultaIA,
    usuario: dict = Depends(usuario_autenticado),
):
    # Identificar la pregunta y al usuario autenticado.
    pregunta = consulta.pregunta.strip()
    identificador_usuario = f"roble:{usuario['user_id']}"

    if not pregunta:
        raise HTTPException(
            status_code=422,
            detail="La pregunta no puede estar vacia",
        )

    # ========================================
    # 1. CLASIFICAR LA PREGUNTA CON GEMINI
    # ========================================

    # Gemini identifica la intencion de la pregunta.
    # No tiene acceso directo a PostgreSQL ni ejecuta SQL.

    try:
        operacion = clasificar_pregunta(pregunta)

    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta="No fue posible clasificar la pregunta.",
            resultado="ERROR",
            detalle="Error en el clasificador de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible clasificar la consulta",
        ) from exc

    # ========================================
    # 2. PREGUNTAS NO RECONOCIDAS
    # ========================================

    if operacion == "NO_RECONOCIDA":

        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta=(
                "La pregunta no corresponde a "
                "una consulta disponible."
            ),
            resultado="DENEGADO",
            detalle="Pregunta fuera del alcance del sistema",
        )

        raise HTTPException(
            status_code=422,
            detail="La pregunta no corresponde a una consulta disponible",
        )

    # ========================================
    # 3. VALIDAR OPERACIONES HABILITADAS
    # ========================================

    # Solo habilitamos la consulta de conteo.
    # Las operaciones con datos personales individuales
    # permanecen bloqueadas hasta definir autorizaciones.

    operaciones_habilitadas = {
        "contar_personas",
    }

    if operacion not in operaciones_habilitadas:

        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta="Consulta no autorizada.",
            resultado="DENEGADO",
            detalle="Operacion no habilitada",
        )

        raise HTTPException(
            status_code=403,
            detail="Esta operacion no esta habilitada",
        )

    # ========================================
    # 4. RECUPERAR DATOS DE POSTGRESQL
    # ========================================

    # Ejecutar una operacion SQL predefinida.
    # Nunca se ejecuta SQL generado por Gemini.

    datos = recuperar_informacion(operacion)

    total = datos["total"]

    # Preparar una respuesta exacta como respaldo.
    respuesta_verificada = (
        f"Actualmente hay {total} "
        "personas registradas en el sistema."
    )

    # ========================================
    # 5. GENERAR RESPUESTA MEDIANTE N8N
    # ========================================

    try:
        # Enviamos exclusivamente el conteo agregado.
        # No enviamos cookies, documentos ni registros
        # personales individuales.

        resultado_n8n = enviar_a_n8n(
            pregunta=pregunta,
            datos={
                "total": total,
            },
        )

        if not isinstance(resultado_n8n, dict):
            raise ValueError(
                "Respuesta inesperada de n8n"
            )

        respuesta_ia = resultado_n8n.get("respuesta")

        if (
            not isinstance(respuesta_ia, str)
            or not respuesta_ia.strip()
        ):
            raise ValueError(
                "Respuesta de n8n vacia o invalida"
            )

        respuesta_ia = respuesta_ia.strip()

    except (httpx.HTTPError, RuntimeError, ValueError) as exc:

        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta="No fue posible generar la respuesta.",
            resultado="ERROR",
            detalle="Error en el procesamiento de n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible generar la respuesta inteligente",
        ) from exc

    # ========================================
    # 6. COMPROBAR LA RESPUESTA DE GEMINI
    # ========================================

    # Validacion basica para la operacion de conteo.
    # Si Gemini introduce cantidades diferentes,
    # se utiliza el dato exacto de PostgreSQL.

    numeros = re.findall(r"\d+", respuesta_ia)

    if numeros == [str(total)]:
        respuesta_final = respuesta_ia
    else:
        respuesta_final = respuesta_verificada

    # ========================================
    # 7. REGISTRAR CONSULTA EN AUDITORIA
    # ========================================

    registrar_consulta_ia(
        usuario=identificador_usuario,
        pregunta=pregunta,
        respuesta=respuesta_final,
        resultado="EXITO",
        detalle=f"Consulta IA: {operacion}",
    )

    # ========================================
    # 8. DEVOLVER RESPUESTA AL USUARIO
    # ========================================

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
    }

