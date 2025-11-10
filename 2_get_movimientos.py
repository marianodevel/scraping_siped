# 2_get_movimientos.py
import os
from session_manager import SessionManager
import scraper_tasks
import utils
import config


def main_movimientos():
    print("--- INICIANDO FASE 2: OBTENER MOVIMIENTOS ---")

    expedientes_a_procesar = utils.read_csv_to_dict(config.LISTA_EXPEDIENTES_CSV)
    if not expedientes_a_procesar:
        return

    print(f"Se encontraron {len(expedientes_a_procesar)} expedientes para procesar.")

    try:
        # Iniciamos sesión UNA SOLA VEZ al principio
        manager = SessionManager()
        session = manager.get_session()

        for i, expediente in enumerate(expedientes_a_procesar):
            print(
                f"\nProcesando {i + 1}/{len(expedientes_a_procesar)}: {expediente['expediente']}"
            )

            # Crear nombre de archivo
            nro = utils.sanitize_filename(expediente.get("expediente"))
            caratula = utils.sanitize_filename(expediente.get("caratula"))
            filename = f"{nro} - {caratula}.csv"

            # (Mejora): Saltar si ya existe
            filepath = os.path.join(config.MOVIMIENTOS_OUTPUT_DIR, filename)
            if os.path.exists(filepath):
                print(f"  > Ya existe '{filename}', saltando.")
                continue

            try:
                # Scrapear movimientos
                movements = scraper_tasks.scrape_movimientos_de_expediente(
                    session, expediente
                )

                if movements:
                    utils.save_to_csv(
                        movements, filename, subdirectory=config.MOVIMIENTOS_OUTPUT_DIR
                    )
                    print(f"  > Guardados {len(movements)} movimientos.")
                else:
                    print("  > No se encontraron movimientos.")

            except Exception as e:
                # Si falla un expediente, lo registramos y continuamos con el siguiente
                print(f"  > !!! ERROR al procesar {expediente['expediente']}: {e}")
                # Opcional: guardar este error en un log
                pass

    except Exception as e:
        print(f"Error fatal durante la Fase 2: {e}")


if __name__ == "__main__":
    main_movimientos()
