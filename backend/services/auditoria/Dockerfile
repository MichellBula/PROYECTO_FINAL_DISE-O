# ==========================================
# MICROSERVICIO DE AUDITORÍA
# ==========================================

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH="/app:/app/backend/services/auditoria"

WORKDIR /app

# Copiar biblioteca compartida
COPY backend/shared/ /app/backend/shared/

# Copiar dependencias
COPY backend/services/auditoria/requirements.txt \
     /app/backend/services/auditoria/requirements.txt

# Instalar dependencias
WORKDIR /app/backend/services/auditoria

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /app/backend/shared

# Copiar código
COPY backend/services/auditoria/ \
     /app/backend/services/auditoria/

WORKDIR /app

# Puerto del microservicio
EXPOSE 8004

# Ejecutar FastAPI
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/app/backend/services/auditoria", "--host", "0.0.0.0", "--port", "8004"]