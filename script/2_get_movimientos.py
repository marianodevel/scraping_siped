import os
import sys
import getpass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
import scraper_tasks
import utils
import config


def main_movimientos():
    print("--- CLI FASE 2: OBTENER MOVIMIENTOS ---")

    expedientes_a_procesar = utils.leer_csv_a_diccionario(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        print(
            f"❌ No se encontró '{config.LISTA_EXPEDIENTES_CSV}'. Ejecute Fase 1 primero."
        )
        return

    print(f"Se procesarán {len(expedientes_a_procesar)} expedientes.")

    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    cookies = session_manager.autenticar_en_siped(usuario, clave)
    if not cookies:
        print("❌ Error de autenticación.")
        return

    try:
        session = session_manager.crear_sesion_con_cookies(cookies)

        for i, expediente in enumerate(expedientes_a_procesar):
            print(
                f"\nProcesando {i + 1}/{len(expedientes_a_procesar)}: {expediente['expediente']}"
            )

            nro = utils.limpiar_nombre_archivo(expediente.get("expediente"))
            caratula = utils.limpiar_nombre_archivo(expediente.get("caratula"))
            filename = f"{nro} - {caratula}.csv"
            filepath = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, filename)

            if os.path.exists(filepath):
                print(f"  > Ya existe, saltando.")
                continue

            try:
                movements = scraper_tasks.raspar_movimientos_de_expediente(
                    session, expediente
                )

                if movements:
                    utils.guardar_a_csv(
                        movements, filename, subdirectory=config.MOVIMIENTOS_OUTPUT_DIR
                    )
                    print(f"  > Guardados {len(movements)} movimientos.")
                else:
                    print("  > No se encontraron movimientos.")

            except Exception as e:
                print(f"  > !!! ERROR al procesar {expediente['expediente']}: {e}")

    except Exception as e:
        print(f"❌ Error fatal durante la Fase 2: {e}")


if __name__ == "__main__":
    main_movimientos()
