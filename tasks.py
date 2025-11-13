# tasks.py
import os
from celery import Celery
from scraper import (
    ejecutar_fase_1_lista,
    ejecutar_fase_2_movimientos,
    ejecutar_fase_3_documentos,
)

# --- Configuración de Celery ---
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# --- Definición de las Tareas ---


@celery_app.task(name="tasks.fase_1_lista_task")
def fase_1_lista_task():
    """Tarea de Celery para la Fase 1: Obtener lista maestra."""
    return ejecutar_fase_1_lista()


@celery_app.task(name="tasks.fase_2_movimientos_task")
def fase_2_movimientos_task():
    """Tarea de Celery para la Fase 2: Descargar movimientos individuales (CSV)."""
    return ejecutar_fase_2_movimientos()


@celery_app.task(name="tasks.fase_3_documentos_task")
def fase_3_documentos_task():
    """Tarea de Celery para la Fase 3: Descargar documentos de texto y compilar PDFs."""
    return ejecutar_fase_3_documentos()
