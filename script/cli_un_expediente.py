"""Script de línea de comandos para la extracción y consolidación de un expediente específico."""

import os
import sys
import getpass
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
import scraper_tasks
import utils
import config


def main() -> None:
    """Flujo interactivo completo de un expediente (Movimientos, PDFs, Consolidación)."""
    print("\n=== CLI: PROCESAR UN ÚNICO EXPEDIENTE (MOVIMIENTOS + PDF) ===")

    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    if not usuario or not clave:
        print("Error: Credenciales requeridas.")
        return

    ruta_usuario = utils.obtener_ruta_usuario(usuario)
    ruta_csv_maestro = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)

    expedientes = utils.leer_csv_a_diccionario(ruta_csv_maestro)
    if not expedientes:
        print(
            f"❌ Error: No se encontró lista maestra en {ruta_usuario}. Ejecute Fase 1 primero."
        )
        return

    print(f"Se encontraron {len(expedientes)} expedientes disponibles:")
    for i, exp in enumerate(expedientes):
        print(f"  [{i + 1}] {exp.get('expediente')} - {exp.get('caratula')}")

    seleccion = input("\nSeleccione el número de expediente a procesar: ").strip()

    try:
        idx = int(seleccion) - 1
        if idx < 0 or idx >= len(expedientes):
            raise ValueError
        expediente_data = expedientes[idx]
    except ValueError:
        print("❌ Selección inválida.")
        return

    nro_expediente = expediente_data.get("expediente", "SIN_NRO")
    nro = utils.limpiar_nombre_archivo(nro_expediente)
    caratula = utils.limpiar_nombre_archivo(
        expediente_data.get("caratula", "SIN_CARATULA")
    )
    nombre_base = f"{nro} - {caratula}"

    print(f"\nAutenticando a {usuario} en SIPED...")
    cookies = session_manager.autenticar_en_siped(usuario, clave)

    if not cookies:
        print("❌ Error: Credenciales inválidas.")
        return

    session = session_manager.crear_sesion_con_cookies(cookies)

    print("\n1. Extrayendo historial de movimientos...")
    movimientos = scraper_tasks.raspar_movimientos_de_expediente(
        session, expediente_data
    )

    if not movimientos:
        print(f"⚠️ No se encontraron movimientos para {nro_expediente}.")
        return

    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    utils.guardar_a_csv(movimientos, f"{nombre_base}.csv", subdirectory=dir_movimientos)
    print(f"  > Guardados {len(movimientos)} movimientos.")

    print("\n2. Gestionando descargas de PDF...")
    dir_docs = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)
    ruta_carpeta_expediente = os.path.join(dir_docs, nombre_base)
    os.makedirs(ruta_carpeta_expediente, exist_ok=True)

    contador_documentos = 0
    total_pdfs_descargados = 0

    for movimiento in movimientos:
        url_doc = movimiento.get("link_escrito")
        if url_doc and url_doc.strip():
            contador_documentos += 1
            id_correlativo = f"doc_{str(contador_documentos).zfill(3)}"

            try:
                datos_documento = scraper_tasks.raspar_contenido_documento(
                    session, url_doc
                )
                if datos_documento:
                    pdfs_a_descargar = []

                    if datos_documento.get("url_pdf_principal"):
                        pdfs_a_descargar.append(
                            {
                                "url": datos_documento["url_pdf_principal"],
                                "nombre": f"{id_correlativo}_principal.pdf",
                                "tipo": "Principal",
                            }
                        )

                    for idx_adj, adj in enumerate(datos_documento.get("adjuntos", [])):
                        nombre_adj = utils.limpiar_nombre_archivo(adj.get("nombre", ""))
                        nombre_adj = (
                            nombre_adj.lower().replace(".pdf", "").replace(".", "")
                        )
                        pdfs_a_descargar.append(
                            {
                                "url": adj.get("url"),
                                "nombre": f"{id_correlativo}_adjunto_{idx_adj + 1}_{nombre_adj}.pdf",
                                "tipo": f"Adjunto {idx_adj + 1}",
                            }
                        )

                    for pdf_info in pdfs_a_descargar:
                        ruta_pdf = os.path.join(
                            ruta_carpeta_expediente, pdf_info["nombre"]
                        )
                        if not os.path.exists(ruta_pdf):
                            print(
                                f"      > Descargando ({id_correlativo}) {pdf_info['tipo']}..."
                            )
                            if scraper_tasks.descargar_archivo(
                                session, pdf_info["url"], ruta_pdf
                            ):
                                total_pdfs_descargados += 1

                time.sleep(0.1)
            except Exception as e:
                print(f"    > Error en Doc {id_correlativo}: {e}")

    print("\n3. Generando PDF consolidado...")
    nombre_pdf_final = f"{nombre_base} (Consolidado).pdf"
    ruta_pdf_final = os.path.join(dir_docs, nombre_pdf_final)

    if os.path.exists(ruta_pdf_final):
        try:
            os.remove(ruta_pdf_final)
        except Exception:
            pass

    utils.fusionar_pdfs(ruta_carpeta_expediente, ruta_pdf_final)

    print(f"\n✅ Proceso completado para: {nro_expediente}")
    print(f"   Archivo: {ruta_pdf_final}")


if __name__ == "__main__":
    main()
