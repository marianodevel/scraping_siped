# Etapa 1: Constructor (Builder)
FROM python:3.9-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app

# Instalamos dependencias de compilación solo aquí
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements-prod.txt .
# Usamos caché de montaje para uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r requirements-prod.txt

# Etapa 2: Imagen Final (Runtime)
FROM python:3.9-slim

WORKDIR /app

# Copiamos solo lo instalado desde el builder
COPY --from=builder /usr/local /usr/local
COPY . .

# Crear directorios necesarios y ajustar permisos si fuera necesario
RUN mkdir -p logs datos_usuarios documentos_expedientes movimientos_expedientes

# Exponer el puerto que usa Flask (5000)
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]