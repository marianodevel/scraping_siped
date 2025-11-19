# 1_get_lista_expedientes.py
from session_manager import SessionManager
import scraper_tasks
import utils
import config


def main_lista():
    print("--- INICIANDO FASE 1: OBTENER LISTA DE EXPEDIENTES ---")
    try:
        manager = SessionManager()
        session = manager.get_session()

        expedientes_list = scraper_tasks.scrape_lista_expedientes(session)

        if expedientes_list:
            utils.save_to_csv(expedientes_list, config.LISTA_EXPEDIENTES_CSV)
            print(
                f"\nLista de expedientes guardada en '{config.LISTA_EXPEDIENTES_CSV}'."
            )
        else:
            print("\nNo se encontraron expedientes.")

    except Exception as e:
        print(f"Error fatal en la Fase 1: {e}")


if __name__ == "__main__":
    main_lista()
