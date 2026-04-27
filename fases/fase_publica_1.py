import os
import session_manager
import scraper_tasks
import utils
import config

def ejecutar_fase_publica(cookies, username):
    """
    Orquesta la extraccion masiva de expedientes publicos accesibles.
    Instancia la sesion HTTP mediante cookies, invoca la rutina de scraping
    y almacena el dataset resultante en un archivo CSV especifico del usuario.
    
    Args:
        cookies (dict): Diccionario de cookies de sesion autenticada.
        username (str): Identificador del usuario (ej. CUIL/DNI) para ruteo de archivos.
        
    Returns:
        dict: Diccionario con el estado de la ejecucion, conteo de registros y archivo destino.
    """
    print(f"--- Iniciando Fase Publica Masiva para el usuario: {username} ---")
    
    session = session_manager.crear_sesion_con_cookies(cookies)
    
    try:
        expedientes_publicos = scraper_tasks.raspar_busqueda_publica_masiva(session)
        
        ruta_usuario = utils.obtener_ruta_usuario(username)
        nombre_archivo = "expedientes_publicos.csv" 
        
        if expedientes_publicos:
            utils.guardar_a_csv(
                expedientes_publicos,
                nombre_archivo,
                subdirectory=ruta_usuario,
            )
            print(f"Extraccion publica guardada exitosamente. Total registros: {len(expedientes_publicos)}")
            return {
                "status": "success", 
                "count": len(expedientes_publicos), 
                "file": nombre_archivo
            }
        else:
            print("Advertencia: La extraccion no devolvio resultados validos.")
            return {
                "status": "empty", 
                "count": 0
            }
            
    except Exception as e:
        print(f"Error de ejecucion en Fase Publica: {e}")
        return {
            "status": "error", 
            "message": str(e)
        }