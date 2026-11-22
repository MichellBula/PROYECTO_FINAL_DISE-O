
import re

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado
from db import registrar_consulta_ia
from n8n_cliente import enviar_a_n8n
from recuperacion import recuperar_informacion


app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.2.0",
)


class ConsultaIA(BaseModel):
    pregunta: str = Field(min_length=1, max_length=500)


@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "servicio": "consultas_inteligentes",
    }


@app.post("/consultas-ia")
def procesar_consulta(
    consulta: ConsultaIA,
    usuario: dict = Depends(usuario_autenticado),
):
    pregunta = consulta.pregunta.strip()
    pregunta_normalizada = pregunta.lower().strip(" ¿?¡!.")

    # Primera operacion controlada.
    # No se ejecuta SQL proporcionado por el usuario o la IA.
    preguntas_permitidas = {
        "cuantas personas hay registradas": "contar_personas",
        "cuántas personas hay registradas": "contar_personas",
    }

    operacion = preguntas_permitidas.get(pregunta_normalizada)
    identificador_usuario = f"roble:{usuario['user_id']}"

    if operacion is None:
        raise HTTPException(
            status_code=422,
            detail="Esta pregunta todavia no esta implementada",
        )

    # Recuperacion controlada desde PostgreSQL.
    datos = recuperar_informacion(operacion)
    total = datos["total"]

    # Respuesta exacta, calculada por el microservicio.
    respuesta_verificada = (
        f"Actualmente hay {total} "
        "personas registradas en el sistema."
    )

    try:
        # Solo enviamos una pregunta permitida y el conteo.
        # No enviamos cookies, documentos ni registros personales.
        resultado_n8n = enviar_a_n8n(
            pregunta=pregunta,
            datos={"total": total},
        )

        if not isinstance(resultado_n8n, dict):
            raise ValueError("Respuesta inesperada de n8n")

        respuesta_ia = resultado_n8n.get("respuesta")

        if not isinstance(respuesta_ia, str):
            raise ValueError("n8n no devolvio una respuesta valida")

        respuesta_ia = respuesta_ia.strip()

        if not respuesta_ia:
            raise ValueError("La respuesta de n8n esta vacia")

    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        registrar_consulta_ia(
            usuario=identificador_usuario,
            pregunta=pregunta,
            respuesta="No fue posible generar la respuesta.",
            resultado="ERROR",
            detalle="Error en la integracion con n8n",
        )

        raise HTTPException(
            status_code=503,
            detail="No fue posible procesar la consulta inteligente",
        ) from exc

    # Comprobacion basica para esta pregunta de conteo.
    # Evita utilizar una respuesta con cantidades diferentes.
    numeros = re.findall(r"\d+", respuesta_ia)

    if numeros == [str(total)]:
        respuesta_final = respuesta_ia
    else:
        respuesta_final = respuesta_verificada

    # Registrar la respuesta que realmente recibira el usuario.
    registrar_consulta_ia(
        usuario=identificador_usuario,
        pregunta=pregunta,
        respuesta=respuesta_final,
        resultado="EXITO",
        detalle=f"Consulta IA con recuperacion: {operacion}",
    )

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
    }
