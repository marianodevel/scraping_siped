# fases/fase_unico.py
import os
import time
import scraper_tasks
import utils
import config
from utils import manejar_fase_con_sesion


@manejar_fase_con_sesion("FASE ÚNICA: PROCESAR UN EXPEDIENTE")
def ejecutar_fase_unico(session, nro_expediente_objetivo, username):
    """
    Realiza el ciclo completo para UN solo expediente seleccionado:
    1. Busca el expediente en la lista maestra.
    2. Actualiza sus movimientos (Scraping).
    3. Descarga los PDFs (Principal y Adjuntos).
    4. Genera el PDF consolidado.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    ruta_csv_maestro = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)

    expedientes = utils.leer_csv_a_diccionario(ruta_csv_maestro)
    if not expedientes:
        return f"Error: No se encontró '{config.LISTA_EXPEDIENTES_CSV}'. Ejecute Fase 1 primero."

    expediente_data = next(
        (e for e in expedientes if e["expediente"] == nro_expediente_objetivo), None
    )

    if not expediente_data:
        return f"Error: El expediente '{nro_expediente_objetivo}' no se encontró en la lista maestra."

    nro = utils.limpiar_nombre_archivo(expediente_data.get("expediente", "SIN_NRO"))
    caratula = utils.limpiar_nombre_archivo(
        expediente_data.get("caratula", "SIN_CARATULA")
    )
    nombre_base = f"{nro} - {caratula}"
    print(f"Iniciando proceso para: {nombre_base}")

    print("  > Actualizando movimientos...")
    movimientos = scraper_tasks.raspar_movimientos_de_expediente(
        session, expediente_data
    )

    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    dir_docs = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    nombre_csv = f"{nombre_base}.csv"
    if movimientos:
        utils.guardar_a_csv(movimientos, nombre_csv, subdirectory=dir_movimientos)
    else:
        print("  > No se encontraron movimientos nuevos, buscando local...")
        ruta_csv = os.path.join(dir_movimientos, nombre_csv)
        movimientos = utils.leer_csv_a_diccionario(ruta_csv)

    if not movimientos:
        return (
            f"Finalizado sin datos: No hay movimientos para {nro_expediente_objetivo}."
        )

    print("  > Gestionando descargas de PDF...")
    ruta_carpeta_expediente = os.path.join(dir_docs, nombre_base)
    os.makedirs(ruta_carpeta_expediente, exist_ok=True)

    contador_documentos = 0
    total_descargados = 0

    for movimiento in movimientos:
        url_doc = movimiento.get("link_escrito")
        if url_doc and url_doc.strip():
            contador_documentos += 1
            id_correlativo = str(contador_documentos).zfill(2)

            try:
                datos_documento = scraper_tasks.raspar_contenido_documento(
                    session, url_doc
                )
                if datos_documento:
                    pdfs = []
                    # Principal
                    if datos_documento.get("url_pdf_principal"):
                        pdfs.append(
                            {
                                "url": datos_documento["url_pdf_principal"],
                                "nombre": f"{id_correlativo}_principal.pdf",
                            }
                        )
                    # Adjuntos
                    for idx, adj in enumerate(datos_documento.get("adjuntos", [])):
                        nombre_adj = utils.limpiar_nombre_archivo(adj["nombre"])
                        nombre_adj = (
                            nombre_adj.lower().replace(".pdf", "").replace(".", "")
                        )
                        pdfs.append(
                            {
                                "url": adj["url"],
                                "nombre": f"{id_correlativo}_adjunto_{idx + 1}_{nombre_adj}.pdf",
                            }
                        )

                    # Descarga
                    for p in pdfs:
                        ruta_pdf = os.path.join(ruta_carpeta_expediente, p["nombre"])
                        if not os.path.exists(ruta_pdf):
                            if scraper_tasks.descargar_archivo(
                                session, p["url"], ruta_pdf
                            ):
                                total_descargados += 1
                                time.sleep(0.2)  # Pausa leve

            except Exception as e:
                print(f"    > Error procesando doc {id_correlativo}: {e}")

    print("  > Generando PDF consolidado...")
    nombre_pdf_final = f"{nombre_base} (Consolidado).pdf"
    ruta_pdf_final = os.path.join(dir_docs, nombre_pdf_final)

    if os.path.exists(ruta_pdf_final):
        os.remove(ruta_pdf_final)

    utils.fusionar_pdfs(ruta_carpeta_expediente, ruta_pdf_final)

    return f"Proceso completado para {nro_expediente_objetivo}. Descargas nuevas: {total_descargados}. PDF Generado."
