FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalamos librerías Python
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copiamos el código (el .dockerignore filtra lo innecesario)
COPY . .

# Creamos carpetas necesarias
RUN mkdir -p logs datos_usuarios

# --- CAMBIO IMPORTANTE ---
# Copiamos el script de arranque y le damos permisos
COPY start.sh .
RUN chmod +x start.sh

# El puerto lo define Railway dinámicamente, pero exponemos 5000 por convención
EXPOSE 5000

# Usamos el script para arrancar TODO junto
CMD ["./start.sh"]
