import os
import sys
import getpass

# Agregar directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
import scraper_tasks
import utils
import config


def main_lista():
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

        if expedientes_list:
            utils.guardar_a_csv(expedientes_list, config.LISTA_EXPEDIENTES_CSV)
            print(
                f"\n✅ Lista guardada en '{config.LISTA_EXPEDIENTES_CSV}'. Total: {len(expedientes_list)}"
            )
        else:
            print("\n⚠️ No se encontraron expedientes.")

    except Exception as e:
        print(f"❌ Error fatal en la Fase 1: {e}")


if __name__ == "__main__":
    main_lista()
