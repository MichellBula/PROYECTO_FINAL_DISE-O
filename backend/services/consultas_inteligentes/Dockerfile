
FROM python:3.12-slim

WORKDIR /app

# Instalar las dependencias del microservicio
COPY backend/services/consultas_inteligentes/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Instalar el módulo compartido de seguridad
COPY backend/shared /app/backend/shared

RUN pip install --no-cache-dir /app/backend/shared

# Copiar el código del microservicio
COPY backend/services/consultas_inteligentes /app/backend/services/consultas_inteligentes

WORKDIR /app/backend/services/consultas_inteligentes

# Puerto previsto para el sexto microservicio
EXPOSE 8007

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
