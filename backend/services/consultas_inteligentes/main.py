
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado
from db import registrar_consulta_ia
from recuperacion import recuperar_informacion


app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.1.0",
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

    # Primera prueba: operacion agregada de conteo.
    # No permite ejecutar SQL enviado por el usuario.
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

    # Por ahora solo se habilita esta consulta agregada.
    # Las consultas con datos personales requieren
    # definir y aplicar autorizaciones especificas.
    datos = recuperar_informacion(operacion)

    respuesta = (
        f"Actualmente hay {datos['total']} "
        "personas registradas en el sistema."
    )

    registrar_consulta_ia(
        usuario=identificador_usuario,
        pregunta=pregunta,
        respuesta=respuesta,
        resultado="EXITO",
        detalle=f"Operacion autorizada: {operacion}",
    )

    return {
        "pregunta": pregunta,
        "respuesta": respuesta,
    }
