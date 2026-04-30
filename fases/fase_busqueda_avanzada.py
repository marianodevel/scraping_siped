import os
import session_manager
import scraper_tasks
import utils

def ejecutar_fase_busqueda_avanzada(cookies, username, filtros):
    """
    Orquesta la ejecucion de una busqueda avanzada con filtros inyectados.
    Guarda los resultados en un CSV independiente con nombre dinamico.
    """
    print(f"--- Iniciando Busqueda Avanzada para el usuario: {username} ---")
    
    session = session_manager.crear_sesion_con_cookies(cookies)
    
    try:
        expedientes_filtrados = scraper_tasks.raspar_busqueda_parametrizada(session, filtros)
        
        ruta_usuario = utils.obtener_ruta_usuario(username)
        nombre_archivo = utils.generar_nombre_busqueda_avanzada(filtros)
        
        if expedientes_filtrados:
            utils.guardar_a_csv(
                expedientes_filtrados,
                nombre_archivo,
                subdirectory=ruta_usuario,
            )
            print(f"Busqueda avanzada guardada como '{nombre_archivo}'. Total registros: {len(expedientes_filtrados)}")
            return {
                "status": "success", 
                "count": len(expedientes_filtrados), 
                "file": nombre_archivo
            }
        else:
            print("La busqueda no arrojo resultados con esos parametros.")
            return {"status": "empty", "count": 0}
            
    except Exception as e:
        print(f"Error de ejecucion en Busqueda Avanzada: {e}")
        return {"status": "error", "message": str(e)}