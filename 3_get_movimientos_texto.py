# 3_get_movimientos_and_docs.py
import os
import time
from session_manager import SessionManager
import scraper_tasks
import utils
import config


def main_movimientos_y_documentos():
    print("--- INICIANDO FASE 3: OBTENER MOVIMIENTOS Y DOCUMENTOS DE TEXTO ---")

    # 1. Leer la lista maestra de expedientes
    expedientes_a_procesar = utils.read_csv_to_dict(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        print(f"Error: No se encontró '{config.LISTA_EXPEDIENTES_CSV}'.")
        print("Por favor, ejecuta '1_get_lista_expedientes.py' primero.")
        return

    total_expedientes = len(expedientes_a_procesar)
    print(f"Se encontraron {total_expedientes} expedientes para procesar.")

    try:
        # 2. Iniciar sesión UNA SOLA VEZ
        manager = SessionManager()
        session = manager.get_session()

        # 3. Bucle principal de expedientes
        for i, expediente in enumerate(expedientes_a_procesar):
            nro_expediente = expediente.get("expediente", "SIN_NRO")
            caratula_exp = expediente.get("caratula", "SIN_CARATULA")

            print(
                f"\n--- Procesando Expediente {i + 1}/{total_expedientes}: {nro_expediente} ---"
            )

            # --- 4. Definir y Crear Carpeta Específica del Expediente ---
            nro_sanitized = utils.sanitize_filename(nro_expediente)
            caratula_sanitized = utils.sanitize_filename(caratula_exp)

            # Crear nombre de carpeta para este expediente
            expediente_folder_name = f"{nro_sanitized} - {caratula_sanitized}"
            # Crear ruta completa de la carpeta
            expediente_folder_path = os.path.join(
                config.DOCUMENTOS_OUTPUT_DIR, expediente_folder_name
            )

            # Crear la carpeta si no existe
            os.makedirs(expediente_folder_path, exist_ok=True)
            print(f"  > Guardando en: '{expediente_folder_path}'")

            # --- 5. Obtener Movimientos (Lógica de Fase 2) ---
            csv_filename = f"{nro_sanitized} - {caratula_sanitized}.csv"
            csv_filepath = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, csv_filename)

            # Intentar leer el CSV de movimientos si ya existe
            movements = utils.read_csv_to_dict(csv_filepath)

            if movements:
                print(
                    f"  > Se leyó el CSV existente: '{csv_filename}' ({len(movements)} movimientos)."
                )
            else:
                # Si no existe, descargar los movimientos
                print(
                    f"  > CSV no encontrado. Descargando movimientos para {nro_expediente}..."
                )
                try:
                    movements = scraper_tasks.scrape_movimientos_de_expediente(
                        session, expediente
                    )

                    if movements:
                        # Guardar el CSV para futura referencia
                        utils.save_to_csv(
                            movements,
                            csv_filename,
                            subdirectory=config.MOVIMIENTOS_OUTPUT_DIR,
                        )
                        print(f"  > Guardados {len(movements)} movimientos en CSV.")
                    else:
                        print("  > No se encontraron movimientos para este expediente.")
                        continue  # Pasar al siguiente expediente

                except Exception as e:
                    print(
                        f"  > !!! ERROR (Movimientos) al procesar {nro_expediente}: {e}"
                    )
                    continue  # Saltar al siguiente expediente

            # --- 6. Bucle de Descarga de Documentos (Nueva Lógica) ---

            if not movements:
                print(f"  > No hay movimientos para procesar en {nro_expediente}.")
                continue

            print(
                f"  > Iniciando descarga de textos de {len(movements)} movimientos..."
            )
            document_count = 0

            # Iterar sobre los movimientos para descargar cada documento
            for movement in movements:
                doc_url = movement.get("link_escrito")

                # Solo procesar si tiene un link_escrito
                if doc_url:
                    document_count += 1

                    # Nombre de archivo TXT correlativo (01.txt, 02.txt)
                    correlative_id = str(document_count).zfill(2)
                    txt_filename = f"{correlative_id}.txt"
                    # La ruta de guardado es DENTRO de la carpeta del expediente
                    txt_filepath = os.path.join(expediente_folder_path, txt_filename)

                    # (Mejora): Saltar si el TXT ya existe
                    if os.path.exists(txt_filepath):
                        print(
                            f"    > Doc {correlative_id}: Ya existe '{txt_filename}', saltando."
                        )
                        continue

                    print(
                        f"    > Doc {correlative_id}: Descargando '{movement.get('nombre_escrito', 'doc')}'..."
                    )

                    try:
                        # Tarea de scraping del documento (devuelve un dict)
                        document_data = scraper_tasks.scrape_document_content(
                            session, doc_url
                        )

                        if document_data:
                            # Guardar el dict formateado en .txt
                            utils.save_to_txt(
                                document_data,
                                txt_filename,
                                subdirectory=expediente_folder_path,
                            )
                        else:
                            print(
                                f"    > ADVERTENCIA: No se pudo extraer contenido del Doc {correlative_id}."
                            )

                        time.sleep(0.5)  # Pausa cortés entre cada petición de documento

                    except Exception as e:
                        print(
                            f"    > !!! ERROR (Documento {correlative_id}) en {nro_expediente}: {e}"
                        )
                        pass  # Continuar con el siguiente documento

            print(f"  > Descarga de documentos finalizada para {nro_expediente}.")

    except Exception as e:
        print(f"\nError fatal durante la Fase 3: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main_movimientos_y_documentos()
