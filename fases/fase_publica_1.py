import os
import session_manager
import scraper_tasks
import utils
import db_manager
from catalogos.localidades import LOCALIDADES
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def ejecutar_fase_publica(cookies, username):
    logger.info(f"--- Iniciando Fase Publica Masiva para el usuario: {username} ---")
    session = session_manager.crear_sesion_con_cookies(cookies)
    
    try:
        expedientes_totales = []
        
        # Estrategia "Dividir y Conquistar":
        # Iteramos sobre el catálogo de localidades para hacer consultas más pequeñas.
        # Esto evita que la paginación del SIPED se rompa y active nuestra protección anti-bucles.
        for id_loc, nombre_loc in LOCALIDADES.items():
            logger.info(f"Extrayendo expedientes públicos de: {nombre_loc} (ID: {id_loc})")
            
            filtros_loc = {
                "organismo_origen": "2",  # Nivel de acceso PÚBLICO
                "id_localidad": str(id_loc)
            }
            
            # Extraemos los datos de esta localidad específica
            expedientes_loc = scraper_tasks.raspar_busqueda_parametrizada(session, filtros_loc)
            
            if expedientes_loc:
                expedientes_totales.extend(expedientes_loc)
                logger.info(f"  > {len(expedientes_loc)} expedientes recuperados de {nombre_loc}.")
            else:
                logger.info(f"  > Sin resultados para {nombre_loc}.")
                
        ruta_usuario = utils.obtener_ruta_usuario(username)
        nombre_archivo = "expedientes_publicos.csv"
        
        if expedientes_totales:
            # 1. Exportación a CSV para mantener compatibilidad
            utils.guardar_a_csv(
                expedientes_totales, nombre_archivo, subdirectory=ruta_usuario
            )
            
            # 2. Persistencia en base de datos SQLite
            db_manager.upsert_expedientes(username, expedientes_totales, origen="PUBLICO")
            
            logger.info(f"Extracción publica finalizada. Total consolidado: {len(expedientes_totales)}")
            return {"status": "success", "count": len(expedientes_totales), "file": nombre_archivo}
        else:
            logger.warning("La extracción no devolvió resultados en ninguna localidad.")
            return {"status": "empty", "count": 0}
            
    except Exception as e:
        logger.error(f"Error de ejecución en Fase Publica: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}