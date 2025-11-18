# fases/fase_3.py
import os
import time
import scraper_tasks
import utils
import config
from utils import manejar_fase_con_sesion


@manejar_fase_con_sesion("FASE 3: OBTENER DOCUMENTOS PDF Y CONSOLIDAR")
def ejecutar_fase_3_documentos(session):
    """
    FASE 3: Descarga los PDFs (principal y adjuntos) para cada movimiento
    y luego fusiona todos los PDFs descargados por expediente.
    """
    expedientes_a_procesar = utils.leer_csv_a_diccionario(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        mensaje = "Error: No se encontró el archivo maestro. Ejecute Fase 1 primero."
        print(mensaje)
        return mensaje

    total_expedientes = len(expedientes_a_procesar)
    print(f"Se encontraron {total_expedientes} expedientes para procesar.")

    print("Sesión iniciada para el bucle de descarga y consolidación de PDFs.")

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

        movimientos = utils.leer_csv_a_diccionario(ruta_csv)

        if not movimientos:
            print(
                f"  > ADVERTENCIA: No se encontró CSV de movimientos para {nro_expediente}. Ejecute Fase 2."
            )
            continue

        print(f"  > Iniciando procesamiento de {len(movimientos)} movimientos...")

        contador_documentos = 0
        total_pdfs_descargados = 0

        for movimiento in movimientos:
            url_doc = movimiento.get("link_escrito")

            if url_doc and url_doc.strip():
                contador_documentos += 1
                id_correlativo = str(contador_documentos).zfill(2)

                try:
                    # 1. Obtenemos URLs de PDFs (Raspado)
                    datos_documento = scraper_tasks.raspar_contenido_documento(
                        session, url_doc
                    )

                    if datos_documento:
                        pdfs_a_descargar = []

                        # 2. Añadir PDF Principal (si existe)
                        url_main = datos_documento.get("url_pdf_principal")
                        if url_main:
                            # Nomenclatura: 01_principal.pdf (para ordenación cronológica y tipo)
                            nombre_pdf_main = f"{id_correlativo}_principal.pdf"
                            pdfs_a_descargar.append(
                                {
                                    "url": url_main,
                                    "nombre": nombre_pdf_main,
                                    "tipo": "Principal",
                                }
                            )

                        # 3. Añadir Adjuntos (si existen)
                        adjuntos = datos_documento.get("adjuntos", [])
                        if adjuntos:
                            for idx, adj in enumerate(adjuntos):
                                url_adj = adj["url"]
                                nombre_orig = utils.limpiar_nombre_archivo(
                                    adj["nombre"]
                                )
                                # Nomenclatura: 01_adjunto_1_NombreOriginal.pdf
                                nombre_base = nombre_orig.replace(".PDF", "").replace(
                                    ".pdf", ""
                                )
                                nombre_archivo_adj = f"{id_correlativo}_adjunto_{idx + 1}_{nombre_base}.pdf"
                                pdfs_a_descargar.append(
                                    {
                                        "url": url_adj,
                                        "nombre": nombre_archivo_adj,
                                        "tipo": f"Adjunto {idx + 1}",
                                    }
                                )

                        # 4. Descargar los PDFs encontrados
                        if pdfs_a_descargar:
                            print(
                                f"    > Doc {id_correlativo}: Encontrados {len(pdfs_a_descargar)} PDFs para descargar."
                            )
                            for pdf_info in pdfs_a_descargar:
                                ruta_pdf = os.path.join(
                                    ruta_carpeta_expediente, pdf_info["nombre"]
                                )

                                if not os.path.exists(ruta_pdf):
                                    print(
                                        f"      > Descargando {pdf_info['tipo']}: {pdf_info['nombre']}"
                                    )
                                    if scraper_tasks.descargar_archivo(
                                        session, pdf_info["url"], ruta_pdf
                                    ):
                                        total_pdfs_descargados += 1
                                else:
                                    print(
                                        f"      > {pdf_info['tipo']} ya existe, saltando: {pdf_info['nombre']}"
                                    )

                    time.sleep(0.5)

                except Exception as e:
                    print(
                        f"    > !!! ERROR (Doc {id_correlativo}) en {nro_expediente}: {e}"
                    )
                    pass

        print(
            f"  > Descarga de PDFs finalizada para {nro_expediente}. (Descargados: {total_pdfs_descargados})"
        )

        # --- 5. Fusionar PDF final ---
        nombre_pdf_final = f"{nombre_carpeta_expediente} (Consolidado).pdf"
        ruta_pdf_final = os.path.join(config.DOCUMENTOS_OUTPUT_DIR, nombre_pdf_final)

        archivos_existentes_en_carpeta = [
            f for f in os.listdir(ruta_carpeta_expediente) if f.lower().endswith(".pdf")
        ]

        if os.path.exists(ruta_pdf_final):
            print(
                f"  > PDF Consolidado '{nombre_pdf_final}' ya existe, saltando fusión."
            )
        elif archivos_existentes_en_carpeta:
            utils.fusionar_pdfs(ruta_carpeta_expediente, ruta_pdf_final)
        else:
            print(f"  > No hay PDFs para consolidar en {nro_expediente}.")

    mensaje = f"Proceso de descarga y consolidación de PDFs completado. Total de expedientes: {total_expedientes}."
    return mensaje
