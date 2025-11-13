# fases/fase_1.py
import os
import scraper_tasks
import utils
import config
from session_manager import SessionManager


def ejecutar_fase_1_lista():
    """
    FASE 1: Obtiene la lista maestra de expedientes y la guarda en un CSV.
    """
    print("--- INICIANDO FASE 1: OBTENER LISTA DE EXPEDIENTES ---")
    try:
        manager = SessionManager()
        session = manager.get_session()

        lista_expedientes = scraper_tasks.raspar_lista_expedientes(session)

        if lista_expedientes:
            utils.guardar_a_csv(lista_expedientes, config.LISTA_EXPEDIENTES_CSV)
            mensaje = f"Lista de expedientes guardada en '{config.LISTA_EXPEDIENTES_CSV}'. Total: {len(lista_expedientes)}"
            print(mensaje)
            return mensaje
        else:
            mensaje = "No se encontraron expedientes."
            print(mensaje)
            return mensaje

    except Exception as e:
        mensaje = f"Error fatal en la Fase 1: {e}"
        print(mensaje)
        raise Exception(mensaje)
