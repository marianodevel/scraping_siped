import os
import sys
import getpass
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
import scraper_tasks
import utils
import config


def main():
    print("\n=== CLI: PROCESAR UN ÚNICO EXPEDIENTE (MOVIMIENTOS + PDF) ===")

    # 1. Identificación Primero (Namespace)
    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    if not usuario or not clave:
        print("Error: Credenciales requeridas.")
        return

    ruta_usuario = utils.obtener_ruta_usuario(usuario)
    ruta_csv_maestro = os.path.join(ruta_usuario, config.LISTA_EXPEDIENTES_CSV)

    # 2. Cargar lista maestra
    expedientes = utils.leer_csv_a_diccionario(ruta_csv_maestro)
    if not expedientes:
        print(
            f"❌ Error: No se encontró lista maestra en {ruta_usuario}. Ejecute Fase 1 primero."
        )
        return

    # 3. Mostrar selección
    print(f"Se encontraron {len(expedientes)} expedientes disponibles:")
    for i, exp in enumerate(expedientes):
        print(f"  [{i + 1}] {exp['expediente']} - {exp['caratula']}")

    seleccion = input("\nSeleccione el número de expediente a procesar: ").strip()

    try:
        idx = int(seleccion) - 1
        if idx < 0 or idx >= len(expedientes):
            print("❌ Selección fuera de rango.")
            return
        expediente_elegido = expedientes[idx]
    except ValueError:
        print("❌ Debe ingresar un número válido.")
        return

    print(f"\nAutenticando a {usuario}...")
    cookies = session_manager.autenticar_en_siped(usuario, clave)

    if not cookies:
        print("❌ Error de autenticación.")
        return

    session = session_manager.crear_sesion_con_cookies(cookies)

    # Datos del expediente
    nro_expediente = expediente_elegido.get("expediente", "SIN_NRO")
    caratula_exp = expediente_elegido.get("caratula", "SIN_CARATULA")

    print(f"\n--- Procesando: {nro_expediente} ---")

    # Rutas internas
    dir_movimientos = os.path.join(ruta_usuario, config.MOVIMIENTOS_OUTPUT_DIR)
    dir_docs = os.path.join(ruta_usuario, config.DOCUMENTOS_OUTPUT_DIR)

    # --- PASO 1: Actualizar Movimientos ---
    print("1. Actualizando movimientos...")

    try:
        movimientos = scraper_tasks.raspar_movimientos_de_expediente(
            session, expediente_elegido
        )

        nro_limpio = utils.limpiar_nombre_archivo(nro_expediente)
        caratula_limpia = utils.limpiar_nombre_archivo(caratula_exp)
        nombre_base = f"{nro_limpio} - {caratula_limpia}"
        nombre_csv = f"{nombre_base}.csv"

        if movimientos:
            utils.guardar_a_csv(movimientos, nombre_csv, subdirectory=dir_movimientos)
            print(f"  > Movimientos actualizados: {len(movimientos)}")
        else:
            print("  > No se encontraron movimientos nuevos.")
            path_csv = os.path.join(dir_movimientos, nombre_csv)
            if os.path.exists(path_csv):
                print("  > Usando CSV local existente.")
                movimientos = utils.leer_csv_a_diccionario(path_csv)
            else:
                print("  > No hay datos para continuar.")
                return

    except Exception as e:
        print(f"❌ Error crítico obteniendo movimientos: {e}")
        return

    # --- PASO 2: Descargar PDFs ---
    print("\n2. Gestionando descargas de PDF...")

    ruta_carpeta_expediente = os.path.join(dir_docs, nombre_base)
    os.makedirs(ruta_carpeta_expediente, exist_ok=True)

    contador_documentos = 0
    total_pdfs_descargados = 0

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
                    pdfs_a_descargar = []
                    # ... (Lógica de detección de PDFs idéntica) ...
                    # Copiamos la lógica de detección para brevedad, es la misma que antes
                    # 2.2 Identificar PDF Principal
                    url_main = datos_documento.get("url_pdf_principal")
                    if url_main:
                        pdfs_a_descargar.append(
                            {
                                "url": url_main,
                                "nombre": f"{id_correlativo}_principal.pdf",
                                "tipo": "Principal",
                            }
                        )
                    # 2.3 Identificar Adjuntos
                    adjuntos = datos_documento.get("adjuntos", [])
                    for idx_adj, adj in enumerate(adjuntos):
                        nombre_adj = (
                            utils.limpiar_nombre_archivo(adj["nombre"])
                            .replace(".pdf", "")
                            .replace(".PDF", "")
                        )
                        pdfs_a_descargar.append(
                            {
                                "url": adj["url"],
                                "nombre": f"{id_correlativo}_adjunto_{idx_adj + 1}_{nombre_adj}.pdf",
                                "tipo": f"Adjunto {idx_adj + 1}",
                            }
                        )

                    if pdfs_a_descargar:
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

    # --- PASO 3: Consolidar ---
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
