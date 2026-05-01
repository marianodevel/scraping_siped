import os
import session_manager
import scraper_tasks
import utils
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def ejecutar_fase_publica(cookies, username):
    logger.info(f"--- Iniciando Fase Publica Masiva para el usuario: {username} ---")
    session = session_manager.crear_sesion_con_cookies(cookies)
    
    try:
        expedientes_publicos = scraper_tasks.raspar_busqueda_publica_masiva(session)
        ruta_usuario = utils.obtener_ruta_usuario(username)
        nombre_archivo = "expedientes_publicos.csv"
        
        if expedientes_publicos:
            utils.guardar_a_csv(
                expedientes_publicos, nombre_archivo, subdirectory=ruta_usuario
            )
            logger.info(f"Extracción publica guardada exitosamente. Total registros: {len(expedientes_publicos)}")
            return {"status": "success", "count": len(expedientes_publicos), "file": nombre_archivo}
        else:
            logger.warning("La extracción no devolvió resultados válidos.")
            return {"status": "empty", "count": 0}
            
    except Exception as e:
        logger.error(f"Error de ejecución en Fase Publica: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}