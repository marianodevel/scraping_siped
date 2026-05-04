import os
import scraper_tasks
import utils
import config
import db_manager
from utils import manejar_fase_con_sesion
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@manejar_fase_con_sesion("FASE 1: OBTENER LISTA DE EXPEDIENTES")
def ejecutar_fase_1_lista(session, username):
    ruta_usuario = utils.obtener_ruta_usuario(username)
    lista_expedientes = scraper_tasks.raspar_lista_expedientes(session)
    
    if lista_expedientes:
        # Mantener backup CSV
        utils.guardar_a_csv(
            lista_expedientes, config.LISTA_EXPEDIENTES_CSV, subdirectory=ruta_usuario
        )
        
        # Integración con DB
        db_manager.upsert_expedientes(username, lista_expedientes, origen="PRIVADO")
        
        ruta_completa = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)
        mensaje = f"Lista de expedientes guardada en DB y en '{ruta_completa}'. Total: {len(lista_expedientes)}"
        return mensaje
    else:
        mensaje = "No se encontraron expedientes."
        return mensaje