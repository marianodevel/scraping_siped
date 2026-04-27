import os
import sys
import json
import getpass

# Añadir el directorio raiz al PYTHONPATH para poder importar los modulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import session_manager
import scraper_tasks

def main():
    print("--- Iniciando prueba de scraping masivo de Expedientes Publicos ---")
    
    usuario = input("Ingrese Usuario (Cuil/DNI): ").strip()
    clave = getpass.getpass("Ingrese Contraseña: ").strip()
    
    if not usuario or not clave:
        print("[ERROR] Faltan credenciales.")
        sys.exit(1)
        
    print(f"\nAutenticando a {usuario} en SIPED...")
    
    # Se obtienen las cookies a traves del metodo procedimental
    cookies_dict = session_manager.autenticar_en_siped(usuario, clave)
    
    if not cookies_dict:
        print("[ERROR] No se pudo obtener una sesion valida de la intranet.")
        sys.exit(1)

    # Se inicializa el objeto requests.Session
    session = session_manager.crear_sesion_con_cookies(cookies_dict)
    print("[EXITO] Sesion obtenida correctamente.\n")

    try:
        print("Iniciando la iteracion de paginas. Esto puede tardar unos minutos...\n")
        expedientes = scraper_tasks.raspar_busqueda_publica_masiva(session)
        
        print("\n--- Resumen de extraccion ---")
        print(f"Total de expedientes extraidos: {len(expedientes)}")
        
        if expedientes:
            print("\nMuestra de los primeros 3 expedientes:")
            for i, exp in enumerate(expedientes[:3]):
                print(f"\n[{i+1}] Expediente: {exp.get('expediente')}")
                print(f"    Caratula: {exp.get('caratula')}")
                print(f"    Dependencia: {exp.get('dependencia')}")
                print(f"    Fecha Alta: {exp.get('fecha_alta')}")
                print(f"    Link Detalle: {exp.get('link_detalle')}")
            
            dump_file = "dump_publicos.json"
            with open(dump_file, "w", encoding="utf-8") as f:
                json.dump(expedientes, f, ensure_ascii=False, indent=4)
            print(f"\nSe ha guardado un volcado completo de los datos en '{dump_file}'.")

    except Exception as e:
        print(f"\n[ERROR] Ocurrio un error inesperado durante la ejecucion: {e}")

if __name__ == "__main__":
    main()