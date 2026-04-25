FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements-prod.txt .
RUN uv pip install --system --no-cache -r requirements-prod.txt

COPY . .

RUN mkdir -p logs datos_usuarios documentos_expedientes movimientos_expedientes

CMD gunicorn --bind 0.0.0.0:5000 app:app