# fases/fase_3.py
import os
import time
import scraper_tasks
import utils
import config
from utils import manejar_fase_con_sesion  # <<< CAMBIO: Importar el decorador

# <<< CAMBIO: 'SessionManager' ya no es necesario aquí


@manejar_fase_con_sesion("FASE 3: OBTENER DOCUMENTOS Y COMPILAR PDF")
def ejecutar_fase_3_documentos(session):
    """
    FASE 3: Descarga el texto y compila el PDF para cada movimiento.
    La 'session' es inyectada por el decorador.
    """
    expedientes_a_procesar = utils.leer_csv_a_diccionario(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        mensaje = "Error: No se encontró el archivo maestro. Ejecute Fase 1 primero."
        print(mensaje)
        return mensaje

    total_expedientes = len(expedientes_a_procesar)
    print(f"Se encontraron {total_expedientes} expedientes para procesar.")

    # <<< CAMBIO: El 'try...except' fatal y el 'SessionManager' han desaparecido.
    print("Sesión iniciada para el bucle de documentos.")

    for i, expediente in enumerate(expedientes_a_procesar):
        nro_expediente = expediente.get("expediente", "SIN_NRO")
        caratula_exp = expediente.get("caratula", "SIN_CARATULA")

        print(
            f"\n--- Procesando Expediente {i + 1}/{total_expedientes}: {nro_expediente} ---"
        )

        # --- Definir rutas de archivos ---
        nro = utils.limpiar_nombre_archivo(nro_expediente)
        caratula = utils.limpiar_nombre_archivo(caratula_exp)
        nombre_carpeta_expediente = f"{nro} - {caratula}"
        ruta_carpeta_expediente = os.path.join(
            config.DOCUMENTOS_OUTPUT_DIR, nombre_carpeta_expediente
        )

        os.makedirs(ruta_carpeta_expediente, exist_ok=True)

        nombre_csv = f"{nro} - {caratula}.csv"
        ruta_csv = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, nombre_csv)

        # Intentar leer el CSV de movimientos (debe existir de la Fase 2)
        movimientos = utils.leer_csv_a_diccionario(ruta_csv)

        if not movimientos:
            print(
                f"  > ADVERTENCIA: No se encontró CSV de movimientos para {nro_expediente}. Ejecute Fase 2."
            )
            continue

        print(f"  > Iniciando descarga de textos de {len(movimientos)} movimientos...")

        contador_documentos = 0

        for movimiento in movimientos:
            url_doc = movimiento.get("link_escrito")

            if url_doc and url_doc.strip():
                contador_documentos += 1

                id_correlativo = str(contador_documentos).zfill(2)
                nombre_txt = f"{id_correlativo}.txt"
                ruta_txt = os.path.join(ruta_carpeta_expediente, nombre_txt)

                if os.path.exists(ruta_txt):
                    print(
                        f"    > Doc {id_correlativo}: Ya existe '{nombre_txt}', saltando."
                    )
                    continue

                print(
                    f"    > Doc {id_correlativo}: Descargando '{movimiento.get('nombre_escrito', 'doc')}'..."
                )

                # Este try/except es BUENO. Permite que el bucle
                # continúe si un *documento* individual falla.
                try:
                    datos_documento = scraper_tasks.raspar_contenido_documento(
                        session, url_doc
                    )

                    if datos_documento:
                        utils.guardar_a_txt(
                            datos_documento,
                            nombre_txt,
                            subdirectory=ruta_carpeta_expediente,
                        )
                    else:
                        print(
                            f"    > ADVERTENCIA: No se pudo extraer contenido del Doc {id_correlativo}."
                        )

                    time.sleep(0.5)

                except Exception as e:
                    print(
                        f"    > !!! ERROR (Documento {id_correlativo}) en {nro_expediente}: {e}"
                    )
                    pass

        print(f"  > Descarga de documentos finalizada para {nro_expediente}.")

        # --- 7. Compilar PDF ---
        if movimientos and contador_documentos > 0:
            nombre_pdf = f"{nombre_carpeta_expediente}.pdf"
            ruta_pdf = os.path.join(config.DOCUMENTOS_OUTPUT_DIR, nombre_pdf)

            if os.path.exists(ruta_pdf):
                print(f"  > PDF '{nombre_pdf}' ya existe, saltando compilación.")
            else:
                utils.compilar_textos_a_pdf(ruta_carpeta_expediente, ruta_pdf)

    mensaje = f"Proceso de documentos y PDF completado. Total de expedientes: {total_expedientes}."
    return mensaje  # <<< CAMBIO: Solo devolvemos el mensaje final
