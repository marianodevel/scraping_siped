import os
import sys
import getpass

# 1. Configuración del Path: Permitir importar módulos de la raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
from fases.fase_3 import ejecutar_fase_3_documentos


def main():
    print("\n=== CLI FASE 3: DESCARGA Y CONSOLIDACIÓN DE PDFs ===")
    print("Nota: Se requiere autenticación manual.\n")

    # 2. Autenticación Interactiva
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

    print("✅ Autenticación exitosa. Iniciando descarga...\n")

    # 4. Ejecutar la lógica centralizada
    try:
        # CORRECCIÓN: Pasamos username para respetar el namespace
        ejecutar_fase_3_documentos(cookies=cookies, username=usuario)

    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado durante la ejecución: {e}")


if __name__ == "__main__":
    main()
