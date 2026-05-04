import os
import scraper_tasks
import utils
import config
import db_manager
from utils import manejar_fase_con_sesion
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@manejar_fase_con_sesion("FASE 2: OBTENER MOVIMIENTOS")
def ejecutar_fase_2_movimientos(session, username):
    ruta_usuario = utils.obtener_ruta_usuario(username)
    
    # Leer maestro desde la DB
    expedientes_a_procesar = db_manager.obtener_expedientes(username, origen="PRIVADO")
    
    if not expedientes_a_procesar:
        mensaje = f"Error: No se encontraron expedientes en la base de datos para {username}. Ejecute Fase 1 primero."
        logger.error(mensaje)
        return mensaje
        
    total_expedientes = len(expedientes_a_procesar)
    logger.info(f"Se encontraron {total_expedientes} expedientes para procesar.")
    
    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    os.makedirs(dir_movimientos, exist_ok=True)
    contador_movimientos = 0
    
    for i, expediente in enumerate(expedientes_a_procesar):
        nro_expediente = expediente["expediente"]
        logger.info(f"Procesando {i + 1}/{total_expedientes}: {nro_expediente}")
        
        nro = utils.limpiar_nombre_archivo(expediente.get("expediente"))
        caratula = utils.limpiar_nombre_archivo(expediente.get("caratula"))
        nombre_archivo = f"{nro} - {caratula}.csv"
        
        # Eliminamos la condición que saltaba el scraping si el archivo existía
        # para forzar SIEMPRE la actualización de los movimientos.
        logger.info(f"  > Extrayendo/Actualizando historial de '{nombre_archivo}'...")
            
        try:
            movimientos = scraper_tasks.raspar_movimientos_de_expediente(
                session, expediente
            )
            if movimientos:
                # Al guardar el CSV, se sobrescribirá el archivo anterior actualizándolo por completo
                utils.guardar_a_csv(
                    movimientos,
                    nombre_archivo,
                    subdirectory=dir_movimientos,
                )
                
                # La BD procesará la lista y solo insertará los movimientos que no existan previamente
                db_manager.upsert_movimientos(expediente["id"], movimientos)
                
                contador_movimientos += len(movimientos)
                logger.info(f"  > Guardados/Actualizados {len(movimientos)} movimientos.")
            else:
                logger.info("  > No se encontraron movimientos.")
        except Exception as e:
            logger.error(f"  > !!! ERROR al procesar {nro_expediente}: {e}", exc_info=True)

    mensaje = f"Proceso de actualización de movimientos completado. Movimientos analizados: {contador_movimientos}"
    return mensaje