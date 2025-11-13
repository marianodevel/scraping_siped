# scraper.py
import os
import time
from session_manager import SessionManager
import scraper_tasks
import utils
import config


def run_phase_1_list():
    """
    FASE 1: Obtiene la lista maestra de expedientes y la guarda en un CSV.
    """
    print("--- INICIANDO FASE 1: OBTENER LISTA DE EXPEDIENTES ---")
    try:
        manager = SessionManager()
        session = manager.get_session()

        expedientes_list = scraper_tasks.scrape_lista_expedientes(session)

        if expedientes_list:
            utils.save_to_csv(expedientes_list, config.LISTA_EXPEDIENTES_CSV)
            message = f"Lista de expedientes guardada en '{config.LISTA_EXPEDIENTES_CSV}'. Total: {len(expedientes_list)}"
            print(message)
            return message
        else:
            message = "No se encontraron expedientes."
            print(message)
            return message

    except Exception as e:
        message = f"Error fatal en la Fase 1: {e}"
        print(message)
        # Es crucial hacer 'raise' para que Celery marque la tarea como 'FAILURE'
        raise Exception(message)


def run_phase_2_movements():
    """
    FASE 2: Descarga los movimientos para CADA expediente de la lista maestra
    y los guarda en archivos CSV individuales.
    """
    print("--- INICIANDO FASE 2: OBTENER MOVIMIENTOS ---")

    expedientes_a_procesar = utils.read_csv_to_dict(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        message = f"Error: No se encontró el archivo maestro '{config.LISTA_EXPEDIENTES_CSV}'. Ejecute Fase 1 primero."
        print(message)
        return message

    total_expedientes = len(expedientes_a_procesar)
    print(f"Se encontraron {total_expedientes} expedientes para procesar.")

    try:
        manager = SessionManager()
        session = manager.get_session()

        movements_count = 0

        for i, expediente in enumerate(expedientes_a_procesar):
            nro_expediente = expediente["expediente"]
            print(f"\nProcesando {i + 1}/{total_expedientes}: {nro_expediente}")

            # Crear nombre de archivo
            nro = utils.sanitize_filename(expediente.get("expediente"))
            caratula = utils.sanitize_filename(expediente.get("caratula"))
            filename = f"{nro} - {caratula}.csv"

            # Saltar si ya existe
            filepath = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, filename)
            if os.path.exists(filepath):
                print(f"  > Ya existe '{filename}', saltando.")
                continue

            try:
                movements = scraper_tasks.scrape_movimientos_de_expediente(
                    session, expediente
                )

                if movements:
                    utils.save_to_csv(
                        movements, filename, subdirectory=config.MOVIMIENTOS_OUTPUT_DIR
                    )
                    movements_count += len(movements)
                    print(f"  > Guardados {len(movements)} movimientos.")
                else:
                    print("  > No se encontraron movimientos.")

            except Exception as e:
                print(f"  > !!! ERROR al procesar {expediente['expediente']}: {e}")
                pass

        message = f"Proceso de movimientos completado. Total de movimientos descargados (nuevos): {movements_count}"
        print(message)
        return message

    except Exception as e:
        message = f"Error fatal durante la Fase 2: {e}"
        print(message)
        raise Exception(message)


def run_phase_3_documents():
    """
    FASE 3: Descarga el texto y compila el PDF para cada movimiento.
    """
    print("--- INICIANDO FASE 3: OBTENER DOCUMENTOS Y COMPILAR PDF ---")

    expedientes_a_procesar = utils.read_csv_to_dict(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        message = "Error: No se encontró el archivo maestro. Ejecute Fase 1 primero."
        print(message)
        return message

    total_expedientes = len(expedientes_a_procesar)
    print(f"Se encontraron {total_expedientes} expedientes para procesar.")

    try:
        manager = SessionManager()
        session = manager.get_session()
        print("Sesión iniciada para el bucle de documentos.")

        for i, expediente in enumerate(expedientes_a_procesar):
            nro_expediente = expediente.get("expediente", "SIN_NRO")
            caratula_exp = expediente.get("caratula", "SIN_CARATULA")

            print(
                f"\n--- Procesando Expediente {i + 1}/{total_expedientes}: {nro_expediente} ---"
            )

            # --- Definir rutas de archivos ---
            nro_sanitized = utils.sanitize_filename(nro_expediente)
            caratula_sanitized = utils.sanitize_filename(caratula_exp)
            expediente_folder_name = f"{nro_sanitized} - {caratula_sanitized}"
            expediente_folder_path = os.path.join(
                config.DOCUMENTOS_OUTPUT_DIR, expediente_folder_name
            )

            os.makedirs(expediente_folder_path, exist_ok=True)

            csv_filename = f"{nro_sanitized} - {caratula_sanitized}.csv"
            csv_filepath = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, csv_filename)

            # Intentar leer el CSV de movimientos (debe existir de la Fase 2)
            movements = utils.read_csv_to_dict(csv_filepath)

            if not movements:
                print(
                    f"  > ADVERTENCIA: No se encontró CSV de movimientos para {nro_expediente}. Ejecute Fase 2."
                )
                continue

            print(
                f"  > Iniciando descarga de textos de {len(movements)} movimientos..."
            )

            document_count = 0

            for movement in movements:
                doc_url = movement.get("link_escrito")

                if doc_url and doc_url.strip():
                    document_count += 1

                    correlative_id = str(document_count).zfill(2)
                    txt_filename = f"{correlative_id}.txt"
                    txt_filepath = os.path.join(expediente_folder_path, txt_filename)

                    if os.path.exists(txt_filepath):
                        print(
                            f"    > Doc {correlative_id}: Ya existe '{txt_filename}', saltando."
                        )
                        continue

                    print(
                        f"    > Doc {correlative_id}: Descargando '{movement.get('nombre_escrito', 'doc')}'..."
                    )

                    try:
                        document_data = scraper_tasks.scrape_document_content(
                            session, doc_url
                        )

                        if document_data:
                            utils.save_to_txt(
                                document_data,
                                txt_filename,
                                subdirectory=expediente_folder_path,
                            )
                        else:
                            print(
                                f"    > ADVERTENCIA: No se pudo extraer contenido del Doc {correlative_id}."
                            )

                        time.sleep(0.5)

                    except Exception as e:
                        print(
                            f"    > !!! ERROR (Documento {correlative_id}) en {nro_expediente}: {e}"
                        )
                        pass

            print(f"  > Descarga de documentos finalizada para {nro_expediente}.")

            # --- 7. Compilar PDF ---
            if movements and document_count > 0:
                pdf_filename = f"{expediente_folder_name}.pdf"
                pdf_output_path = os.path.join(
                    config.DOCUMENTOS_OUTPUT_DIR, pdf_filename
                )

                if os.path.exists(pdf_output_path):
                    print(f"  > PDF '{pdf_filename}' ya existe, saltando compilación.")
                else:
                    utils.compile_texts_to_pdf(expediente_folder_path, pdf_output_path)

        message = f"Proceso de documentos y PDF completado. Total de expedientes: {total_expedientes}."
        print(message)
        return message

    except Exception as e:
        message = f"Error fatal durante la Fase 3: {e}"
        print(message)
        raise Exception(message)
