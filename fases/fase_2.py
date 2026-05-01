import os
import scraper_tasks
import utils
import config
from utils import manejar_fase_con_sesion
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@manejar_fase_con_sesion("FASE 2: OBTENER MOVIMIENTOS")
def ejecutar_fase_2_movimientos(session, username):
    ruta_usuario = utils.obtener_ruta_usuario(username)
    ruta_csv_maestro = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)
    
    expedientes_a_procesar = utils.leer_csv_a_diccionario(ruta_csv_maestro)
    if not expedientes_a_procesar:
        mensaje = f"Error: No se encontró el archivo maestro '{config.LISTA_EXPEDIENTES_CSV}' en {ruta_usuario}. Ejecute Fase 1 primero."
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
        ruta_archivo = os.path.join(dir_movimientos, nombre_archivo)
        
        if os.path.exists(ruta_archivo):
            logger.info(f"  > Ya existe '{nombre_archivo}', saltando.")
            continue
            
        try:
            movimientos = scraper_tasks.raspar_movimientos_de_expediente(
                session, expediente
            )
            if movimientos:
                utils.guardar_a_csv(
                    movimientos,
                    nombre_archivo,
                    subdirectory=dir_movimientos,
                )
                contador_movimientos += len(movimientos)
                logger.info(f"  > Guardados {len(movimientos)} movimientos.")
            else:
                logger.info("  > No se encontraron movimientos.")
        except Exception as e:
            logger.error(f"  > !!! ERROR al procesar {nro_expediente}: {e}", exc_info=True)

    mensaje = f"Proceso de movimientos completado. Total descargados (nuevos): {contador_movimientos}"
    return mensaje