import os
import sys
import getpass

# 1. Configuración del Path: Permitir importar módulos de la raíz (config, utils, fases, session_manager)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
from fases.fase_3 import ejecutar_fase_3_documentos


def main():
    print("\n=== SCRIPT CLI: FASE 3 (DESCARGA Y CONSOLIDACIÓN DE PDFs) ===")
    print(
        "Nota: Se requiere autenticación manual ya que no se usan credenciales guardadas.\n"
    )

    # 2. Autenticación Interactiva (Sin .env)
    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    if not usuario or not clave:
        print("Error: Usuario y contraseña son obligatorios.")
        return

    print(f"\nAutenticando a {usuario} en SIPED...")

    # 3. Obtener Cookies
    cookies = session_manager.autenticar_en_siped(usuario, clave)

    if not cookies:
        print("❌ Error: Credenciales inválidas o fallo en la conexión.")
        return

    print("✅ Autenticación exitosa.\n")

    # 4. Ejecutar la lógica centralizada (Reutilizando fases/fase_3.py)
    # El decorador @manejar_fase_con_sesion en fase_3 se encarga de crear la sesión con estas cookies.
    try:
        ejecutar_fase_3_documentos(cookies=cookies)

    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado durante la ejecución: {e}")


if __name__ == "__main__":
    main()
