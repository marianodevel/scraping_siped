#!/bin/bash

# 1. Iniciar el Worker de Celery en segundo plano (&)
echo "Iniciando Celery Worker..."
celery -A tasks.celery_app worker --loglevel=info &

# 2. Iniciar la App Web con Gunicorn en primer plano
# Railway inyecta la variable $PORT automáticamente
echo "Iniciando Gunicorn en el puerto $PORT..."
gunicorn --bind 0.0.0.0:$PORT app:app
