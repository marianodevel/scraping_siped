import os
import scraper_tasks
import utils
import config
from utils import manejar_fase_con_sesion


@manejar_fase_con_sesion("FASE 2: OBTENER MOVIMIENTOS")
def ejecutar_fase_2_movimientos(session, username):
    """
    FASE 2: Descarga los movimientos para CADA expediente de la lista maestra
    y los guarda en archivos CSV individuales.
    La 'session' es inyectada por el decorador.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    ruta_csv_maestro = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)

    expedientes_a_procesar = utils.leer_csv_a_diccionario(ruta_csv_maestro)
    if not expedientes_a_procesar:
        mensaje = f"Error: No se encontró el archivo maestro '{config.LISTA_EXPEDIENTES_CSV}' en {ruta_usuario}. Ejecute Fase 1 primero."
        print(mensaje)
        return mensaje

    total_expedientes = len(expedientes_a_procesar)
    print(f"Se encontraron {total_expedientes} expedientes para procesar.")

    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    os.makedirs(dir_movimientos, exist_ok=True)

    contador_movimientos = 0

    for i, expediente in enumerate(expedientes_a_procesar):
        nro_expediente = expediente["expediente"]
        print(f"\nProcesando {i + 1}/{total_expedientes}: {nro_expediente}")

        nro = utils.limpiar_nombre_archivo(expediente.get("expediente"))
        caratula = utils.limpiar_nombre_archivo(expediente.get("caratula"))
        nombre_archivo = f"{nro} - {caratula}.csv"

        ruta_archivo = os.path.join(dir_movimientos, nombre_archivo)
        if os.path.exists(ruta_archivo):
            print(f"  > Ya existe '{nombre_archivo}', saltando.")
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
                print(f"  > Guardados {len(movimientos)} movimientos.")
            else:
                print("  > No se encontraron movimientos.")

        except Exception as e:
            print(f"  > !!! ERROR al procesar {expediente['expediente']}: {e}")
            pass

    mensaje = f"Proceso de movimientos completado. Total de movimientos descargados (nuevos): {contador_movimientos}"
    return mensaje
