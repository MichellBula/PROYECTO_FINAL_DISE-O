
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from auth import usuario_autenticado


# ============================================
# MICROSERVICIO DE CONSULTAS INTELIGENTES
# ============================================

app = FastAPI(
    title="Microservicio de consultas inteligentes",
    version="0.1.0",
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
    # La autenticación se verifica antes
    # de procesar la consulta.

    # PENDIENTE:
    # 1. Recuperar información autorizada.
    # 2. Integrar el flujo de n8n y RAG.
    # 3. Generar la respuesta fundamentada.
    # 4. Registrar pregunta y respuesta en auditoría.

    raise HTTPException(
        status_code=503,
        detail="El servicio de consultas inteligentes aún no está configurado",
    )
