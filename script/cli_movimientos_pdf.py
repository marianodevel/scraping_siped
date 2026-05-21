"""Script de línea de comandos para la ejecución de la Fase 3: Descarga de PDFs consolidados."""

import os
import sys
import getpass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import session_manager
from fases.fase_3 import ejecutar_fase_3_documentos


def main() -> None:
    """Punto de entrada interactivo para invocar la fase masiva de documentación."""
    print("\n=== CLI FASE 3: DESCARGA Y CONSOLIDACIÓN DE PDFs ===")
    print("Nota: Se requiere autenticación manual.\n")

    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    if not usuario or not clave:
        print("Error: Usuario y contraseña son obligatorios.")
        return

    print(f"\nAutenticando a {usuario} en SIPED...")
    cookies = session_manager.autenticar_en_siped(usuario, clave)

    if not cookies:
        print("❌ Error: Credenciales inválidas o fallo en la conexión.")
        return

    print("✅ Autenticación exitosa. Iniciando descarga...\n")

    try:
        mensaje_resultado = ejecutar_fase_3_documentos(
            cookies=cookies, username=usuario
        )
        print(f"\n{mensaje_resultado}")
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado durante la ejecución: {e}")


if __name__ == "__main__":
    main()
