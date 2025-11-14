# fases/fase_2.py
import os
import scraper_tasks
import utils
import config
from utils import manejar_fase_con_sesion  # <<< CAMBIO: Importar el decorador

# <<< CAMBIO: 'SessionManager' ya no es necesario aquí


@manejar_fase_con_sesion("FASE 2: OBTENER MOVIMIENTOS")
def ejecutar_fase_2_movimientos(session):
    """
    FASE 2: Descarga los movimientos para CADA expediente de la lista maestra
    y los guarda en archivos CSV individuales.
    La 'session' es inyectada por el decorador.
    """
    expedientes_a_procesar = utils.leer_csv_a_diccionario(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        mensaje = f"Error: No se encontró el archivo maestro '{config.LISTA_EXPEDIENTES_CSV}'. Ejecute Fase 1 primero."
        print(mensaje)  # Dejamos los prints internos
        return mensaje

    total_expedientes = len(expedientes_a_procesar)
    print(f"Se encontraron {total_expedientes} expedientes para procesar.")

    # <<< CAMBIO: El 'try...except' fatal y el 'SessionManager' han desaparecido.

    contador_movimientos = 0

    for i, expediente in enumerate(expedientes_a_procesar):
        nro_expediente = expediente["expediente"]
        print(f"\nProcesando {i + 1}/{total_expedientes}: {nro_expediente}")

        # Crear nombre de archivo
        nro = utils.limpiar_nombre_archivo(expediente.get("expediente"))
        caratula = utils.limpiar_nombre_archivo(expediente.get("caratula"))
        nombre_archivo = f"{nro} - {caratula}.csv"

        # Saltar si ya existe
        ruta_archivo = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, nombre_archivo)
        if os.path.exists(ruta_archivo):
            print(f"  > Ya existe '{nombre_archivo}', saltando.")
            continue

        # Este try/except es BUENO. Es específico de esta lógica
        # y permite que el bucle continúe si un expediente falla.
        try:
            movimientos = scraper_tasks.raspar_movimientos_de_expediente(
                session, expediente
            )

            if movimientos:
                utils.guardar_a_csv(
                    movimientos,
                    nombre_archivo,
                    subdirectory=config.MOVIMIENTOS_OUTPUT_DIR,
                )
                contador_movimientos += len(movimientos)
                print(f"  > Guardados {len(movimientos)} movimientos.")
            else:
                print("  > No se encontraron movimientos.")

        except Exception as e:
            print(f"  > !!! ERROR al procesar {expediente['expediente']}: {e}")
            pass  # Continuar con el siguiente expediente

    mensaje = f"Proceso de movimientos completado. Total de movimientos descargados (nuevos): {contador_movimientos}"
    return mensaje  # <<< CAMBIO: Solo devolvemos el mensaje final
