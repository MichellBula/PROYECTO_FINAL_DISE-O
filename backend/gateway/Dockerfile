
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend/gateway

WORKDIR /app

# Instalar la biblioteca compartida de seguridad
COPY backend/shared/ /app/backend/shared/

# Instalar las dependencias de la Gateway
COPY backend/gateway/requirements.txt /app/backend/gateway/requirements.txt

RUN pip install --no-cache-dir \
    -r /app/backend/gateway/requirements.txt \
    /app/backend/shared

# Copiar el código de la Gateway
COPY backend/gateway/ /app/backend/gateway/

EXPOSE 8006

CMD ["uvicorn", "main:app", "--app-dir", "/app/backend/gateway", "--host", "0.0.0.0", "--port", "8006"]
