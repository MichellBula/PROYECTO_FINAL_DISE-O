# ==========================================
# MICROSERVICIO DE CONSULTA DE PERSONAS
# ==========================================

FROM python:3.12-slim

# Configuracion de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/backend/services/consultar_persona"

# Directorio principal
WORKDIR /app

# Copiar paquete compartido
COPY backend/shared/ /app/backend/shared/

# Copiar dependencias
COPY backend/services/consultar_persona/requirements.txt /app/backend/services/consultar_persona/requirements.txt

# Instalar dependencias
WORKDIR /app/backend/services/consultar_persona

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /app/backend/shared

# Copiar codigo del microservicio
COPY backend/services/consultar_persona/ /app/backend/services/consultar_persona/

# Directorio de ejecucion
WORKDIR /app

# Puerto del microservicio
EXPOSE 8000

# Iniciar FastAPI
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/app/backend/services/consultar_persona", "--host", "0.0.0.0", "--port", "8000"]