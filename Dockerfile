FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv directamente desde la imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar manifiestos y sincronizar dependencias (sin instalar el proyecto aun para aprovechar cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copiar el codigo fuente y sincronizar el proyecto completo
COPY . .
RUN uv sync --frozen --no-dev

# Exponer el entorno virtual generado por uv al PATH del sistema
ENV PATH="/app/.venv/bin:$PATH"

# Crear directorios para los volumenes persistentes
RUN mkdir -p logs datos_usuarios documentos_expedientes movimientos_expedientes

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]