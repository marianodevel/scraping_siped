FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r siped_group && useradd -r -g siped_group siped_user

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

RUN mkdir -p logs datos_usuarios && \
    chown -R siped_user:siped_group /app

USER siped_user

EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
