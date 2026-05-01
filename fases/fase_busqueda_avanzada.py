import os
import session_manager
import scraper_tasks
import utils
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def ejecutar_fase_busqueda_avanzada(cookies, username, filtros):
    logger.info(f"--- Iniciando Búsqueda Avanzada para el usuario: {username} ---")
    session = session_manager.crear_sesion_con_cookies(cookies)
    
    try:
        expedientes_filtrados = scraper_tasks.raspar_busqueda_parametrizada(session, filtros)
        ruta_usuario = utils.obtener_ruta_usuario(username)
        nombre_archivo = utils.generar_nombre_busqueda_avanzada(filtros)
        
        if expedientes_filtrados:
            utils.guardar_a_csv(
                expedientes_filtrados, nombre_archivo, subdirectory=ruta_usuario
            )
            logger.info(f"Búsqueda avanzada guardada como '{nombre_archivo}'. Total: {len(expedientes_filtrados)}")
            return {"status": "success", "count": len(expedientes_filtrados), "file": nombre_archivo}
        else:
            logger.warning("La búsqueda no arrojó resultados con esos parámetros.")
            return {"status": "empty", "count": 0}
            
    except Exception as e:
        logger.error(f"Error de ejecución en Búsqueda Avanzada: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}