"""Script de línea de comandos para la prueba de extracción de expedientes públicos."""

import os
import sys
import json
import getpass

# Añadir el directorio raíz al PYTHONPATH para poder importar los módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import session_manager
import scraper_tasks
from catalogos.localidades import LOCALIDADES


def main() -> None:
    """Ejecuta el flujo interactivo por consola para la búsqueda pública."""
    print("--- Iniciando prueba de scraping masivo de Expedientes Públicos ---")

    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()

    if not usuario or not clave:
        print("[ERROR] Faltan credenciales.")
        sys.exit(1)

    print(f"\nAutenticando a {usuario} en SIPED...")

    # Se obtienen las cookies a través del método procedimental
    cookies_dict = session_manager.autenticar_en_siped(usuario, clave)

    if not cookies_dict:
        print("[ERROR] No se pudo obtener una sesión válida de la intranet.")
        sys.exit(1)

    # Se inicializa el objeto requests.Session
    session = session_manager.crear_sesion_con_cookies(cookies_dict)
    print("[EXITO] Sesión obtenida correctamente.\n")

    try:
        print(
            "Iniciando la iteración por localidades. Esto puede tardar varios minutos...\n"
        )
        expedientes_totales = []

        # Estrategia "Dividir y Conquistar" usando el catálogo de localidades
        for id_loc, nombre_loc in LOCALIDADES.items():
            print(f"-> Extrayendo expedientes de: {nombre_loc} (ID: {id_loc})...")

            filtros_loc = {
                "organismo_origen": "2",  # Nivel de acceso PÚBLICO
                "id_localidad": str(id_loc),
            }

            expedientes_loc = scraper_tasks.raspar_busqueda_parametrizada(
                session, filtros_loc
            )

            if expedientes_loc:
                expedientes_totales.extend(expedientes_loc)
                print(f"   [OK] {len(expedientes_loc)} expedientes recuperados.")
            else:
                print("   [-] Sin resultados.")

        print("\n--- Resumen de extracción ---")
        print(f"Total de expedientes extraídos: {len(expedientes_totales)}")

        if expedientes_totales:
            print("\nMuestra de los primeros 3 expedientes:")
            for i, exp in enumerate(expedientes_totales[:3]):
                print(f"\n[{i + 1}] Expediente: {exp.get('expediente')}")
                print(f"    Carátula: {exp.get('caratula')}")
                print(f"    Dependencia: {exp.get('dependencia')}")
                print(f"    Fecha Alta: {exp.get('fecha_alta')}")
                print(f"    Link Detalle: {exp.get('link_detalle')}")

            dump_file = "dump_publicos.json"
            with open(dump_file, "w", encoding="utf-8") as f:
                json.dump(expedientes_totales, f, ensure_ascii=False, indent=4)
            print(
                f"\nSe ha guardado un volcado completo de los datos en '{dump_file}'."
            )

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error inesperado durante la ejecución: {e}")


if __name__ == "__main__":
    main()

