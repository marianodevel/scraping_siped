"""Script de línea de comandos para la ejecución de la Fase 1: Lista de Expedientes."""

import os
import sys
import getpass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import scraper_tasks
import session_manager
import utils


def main_lista() -> None:
    """Punto de entrada interactivo para la extracción de la lista maestra privada."""
    print("--- CLI FASE 1: OBTENER LISTA DE EXPEDIENTES ---")

    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    print(f"\nAutenticando a {usuario} en SIPED...")
    cookies = session_manager.autenticar_en_siped(usuario, clave)

    if not cookies:
        print("❌ Error de autenticación.")
        return

    try:
        session = session_manager.crear_sesion_con_cookies(cookies)
        expedientes_list = scraper_tasks.raspar_lista_expedientes(session)
        ruta_usuario = utils.obtener_ruta_usuario(usuario)

        if expedientes_list:
            utils.guardar_a_csv(
                expedientes_list,
                config.LISTA_EXPEDIENTES_CSV,
                subdirectory=ruta_usuario,
            )
            print(
                f"\n✅ Lista guardada en '{ruta_usuario}/{config.LISTA_EXPEDIENTES_CSV}'. Total: {len(expedientes_list)}"
            )
        else:
            print("\n⚠️ No se encontraron expedientes.")

    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado durante la ejecución: {e}")


if __name__ == "__main__":
    main_lista()
