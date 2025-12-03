import scraper_tasks
import utils
import config
from utils import manejar_fase_con_sesion


@manejar_fase_con_sesion("FASE 1: OBTENER LISTA DE EXPEDIENTES")
def ejecutar_fase_1_lista(session, username):
    """
    FASE 1: Obtiene la lista maestra de expedientes y la guarda en un CSV.
    La 'session' es inyectada por el decorador 'manejar_fase_con_sesion'.
    """
    ruta_usuario = utils.obtener_ruta_usuario(username)
    lista_expedientes = scraper_tasks.raspar_lista_expedientes(session)

    if lista_expedientes:
        utils.guardar_a_csv(
            lista_expedientes, config.LISTA_EXPEDIENTES_CSV, subdirectory=ruta_usuario
        )
        mensaje = f"Lista de expedientes guardada en '{ruta_usuario}/{config.LISTA_EXPEDIENTES_CSV}'. Total: {len(lista_expedientes)}"
        return mensaje
    else:
        mensaje = "No se encontraron expedientes."
        return mensaje
