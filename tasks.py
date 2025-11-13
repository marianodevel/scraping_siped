# tasks.py
import os
from celery import Celery

# Importamos las tres funciones de scraping
from scraper import run_phase_1_list, run_phase_2_movements, run_phase_3_documents

# --- Configuración de Celery ---

# Render.com proveerá esta variable, localmente usa localhost
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# --- Definición de las Tareas ---


@celery_app.task(name="tasks.phase_1_list_task")
def phase_1_list_task():
    """Tarea de Celery para la Fase 1: Obtener lista maestra."""
    return run_phase_1_list()


@celery_app.task(name="tasks.phase_2_movements_task")
def phase_2_movements_task():
    """Tarea de Celery para la Fase 2: Descargar movimientos individuales (CSV)."""
    return run_phase_2_movements()


@celery_app.task(name="tasks.phase_3_documents_task")
def phase_3_documents_task():
    """Tarea de Celery para la Fase 3: Descargar documentos de texto y compilar PDFs."""
    return run_phase_3_documents()
