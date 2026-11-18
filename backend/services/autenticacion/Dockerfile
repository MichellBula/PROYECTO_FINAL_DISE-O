# ==========================================
# MICROSERVICIO DE AUTENTICACION
# ==========================================

FROM python:3.12-slim

# Configuracion de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/backend/services/autenticacion"

# Directorio principal
WORKDIR /app

# Copiar paquete compartido
COPY backend/shared/ /app/backend/shared/

# Copiar dependencias
COPY backend/services/autenticacion/requirements.txt /app/backend/services/autenticacion/requirements.txt

# Instalar dependencias
WORKDIR /app/backend/services/autenticacion

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /app/backend/shared

# Copiar codigo del microservicio
COPY backend/services/autenticacion/ /app/backend/services/autenticacion/

# Directorio de ejecucion
WORKDIR /app

# Puerto del microservicio
EXPOSE 8001

# Iniciar FastAPI
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/app/backend/services/autenticacion", "--host", "0.0.0.0", "--port", "8001"]