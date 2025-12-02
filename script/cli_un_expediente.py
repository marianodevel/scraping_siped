import os
import sys
import getpass
import time

# Permitir importar módulos de la raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
import scraper_tasks
import utils
import config


def main():
    print("\n=== CLI: PROCESAR UN ÚNICO EXPEDIENTE (MOVIMIENTOS + PDF) ===")

    # 1. Cargar lista maestra para selección
    expedientes = utils.leer_csv_a_diccionario(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes:
        print(
            f"❌ Error: No se encontró '{config.LISTA_EXPEDIENTES_CSV}'. Ejecute Fase 1 primero."
        )
        return

    # 2. Mostrar selección
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

    # 3. Autenticación
    usuario = input("\nIngrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    if not usuario or not clave:
        print("Error: Credenciales requeridas.")
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

    # --- PASO 1: Actualizar Movimientos (Lógica Unitaria) ---
    # Es necesario actualizar los movimientos para obtener los links de descarga vigentes.
    print("1. Actualizando movimientos...")

    try:
        movimientos = scraper_tasks.raspar_movimientos_de_expediente(
            session, expediente_elegido
        )

        nro_limpio = utils.limpiar_nombre_archivo(nro_expediente)
        caratula_limpia = utils.limpiar_nombre_archivo(caratula_exp)
        nombre_csv = f"{nro_limpio} - {caratula_limpia}.csv"

        if movimientos:
            utils.guardar_a_csv(
                movimientos, nombre_csv, subdirectory=config.MOVIMIENTOS_OUTPUT_DIR
            )
            print(f"  > Movimientos actualizados: {len(movimientos)}")
        else:
            print("  > No se encontraron movimientos nuevos.")
            # Intentar usar local si existe
            path_csv = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, nombre_csv)
            if os.path.exists(path_csv):
                print("  > Usando CSV local existente.")
                movimientos = utils.leer_csv_a_diccionario(path_csv)
            else:
                print("  > No hay datos para continuar.")
                return

    except Exception as e:
        print(f"❌ Error crítico obteniendo movimientos: {e}")
        return

    # --- PASO 2: Descargar PDFs (Lógica del Script 3, adaptada) ---
    print("\n2. Gestionando descargas de PDF...")

    nombre_carpeta_expediente = f"{nro_limpio} - {caratula_limpia}"
    ruta_carpeta_expediente = os.path.join(
        config.DOCUMENTOS_OUTPUT_DIR, nombre_carpeta_expediente
    )
    os.makedirs(ruta_carpeta_expediente, exist_ok=True)

    contador_documentos = 0
    total_pdfs_descargados = 0

    for movimiento in movimientos:
        url_doc = movimiento.get("link_escrito")

        if url_doc and url_doc.strip():
            contador_documentos += 1
            id_correlativo = str(contador_documentos).zfill(2)

            try:
                # 2.1 Obtener metadatos del documento (links a PDFs)
                datos_documento = scraper_tasks.raspar_contenido_documento(
                    session, url_doc
                )

                if datos_documento:
                    pdfs_a_descargar = []

                    # 2.2 Identificar PDF Principal
                    url_main = datos_documento.get("url_pdf_principal")
                    if url_main:
                        nombre_pdf_main = f"{id_correlativo}_principal.pdf"
                        pdfs_a_descargar.append(
                            {
                                "url": url_main,
                                "nombre": nombre_pdf_main,
                                "tipo": "Principal",
                            }
                        )

                    # 2.3 Identificar Adjuntos
                    adjuntos = datos_documento.get("adjuntos", [])
                    for idx_adj, adj in enumerate(adjuntos):
                        url_adj = adj["url"]
                        nombre_orig = utils.limpiar_nombre_archivo(adj["nombre"])
                        nombre_base = nombre_orig.replace(".PDF", "").replace(
                            ".pdf", ""
                        )
                        nombre_archivo_adj = (
                            f"{id_correlativo}_adjunto_{idx_adj + 1}_{nombre_base}.pdf"
                        )

                        pdfs_a_descargar.append(
                            {
                                "url": url_adj,
                                "nombre": nombre_archivo_adj,
                                "tipo": f"Adjunto {idx_adj + 1}",
                            }
                        )

                    # 2.4 Ejecutar descargas
                    if pdfs_a_descargar:
                        # Solo imprimimos si hay actividad real
                        # print(f"    > Doc {id_correlativo}: Verificando {len(pdfs_a_descargar)} archivos...")

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
                            else:
                                # Ya existe, saltamos silenciosamente o con log mínimo
                                pass

                # Pausa para no saturar
                time.sleep(0.1)

            except Exception as e:
                print(f"    > Error en Doc {id_correlativo}: {e}")

    print(f"  > Descargas finalizadas. Archivos nuevos: {total_pdfs_descargados}")

    # --- PASO 3: Consolidar (Lógica del Script 3, adaptada) ---
    print("\n3. Generando PDF consolidado...")

    nombre_pdf_final = f"{nombre_carpeta_expediente} (Consolidado).pdf"
    ruta_pdf_final = os.path.join(config.DOCUMENTOS_OUTPUT_DIR, nombre_pdf_final)

    # Eliminamos el consolidado anterior para forzar la actualización con los nuevos PDFs
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
