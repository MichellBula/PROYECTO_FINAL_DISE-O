
# Imagen base de Python
FROM python:3.12-slim

# Configuración de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Rutas de los módulos
ENV PYTHONPATH="/app:/app/backend/services/eliminar_persona"

# Carpeta principal del contenedor
WORKDIR /app

# Copiar el código compartido de seguridad
COPY backend/shared/ /app/backend/shared/

# Copiar las dependencias
COPY backend/services/eliminar_persona/requirements.txt /app/backend/services/eliminar_persona/requirements.txt

# Instalar dependencias del microservicio
RUN pip install --no-cache-dir -r /app/backend/services/eliminar_persona/requirements.txt

# Instalar el paquete compartido
RUN pip install --no-cache-dir /app/backend/shared

# Copiar los archivos del microservicio
COPY backend/services/eliminar_persona/ /app/backend/services/eliminar_persona/

# Puerto interno del microservicio
EXPOSE 8005

# Ejecutar FastAPI
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/app/backend/services/eliminar_persona", "--host", "0.0.0.0", "--port", "8005"]
