import requests
import config
import parsers
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
from logger import get_logger

logger = get_logger(__name__)

def autenticar_en_siped(usuario, clave):
    """
    Intenta autenticar un usuario y clave contra SIPED.
    Si tiene éxito, devuelve un diccionario de cookies. Si falla, devuelve None.
    """
    if not usuario or not clave:
        logger.error("Credenciales incompletas.")
        return None

    session = requests.Session()
    session.headers.update(config.BROWSER_HEADERS)

    try:
        logger.info(f"Autenticando usuario: {usuario}.")
        credenciales = {"usuario": usuario, "pass": clave}
        r_login = session.post(config.LOGIN_URL, data=credenciales)
        r_login.raise_for_status()

        url_inicio = parsers.obtener_url_meta_refresh(
            r_login.text, f"{config.BASE_URL}/servicios"
        )

        if not url_inicio:
            logger.error("Error de autenticación: Redirección fallida.")
            return None

        logger.info("Accediendo al menú principal.")
        r_menu = session.get(url_inicio)
        r_menu.raise_for_status()

        url_token = parsers.obtener_enlace_token_siped(r_menu.text)

        if not url_token:
            logger.error("Token de sesión no encontrado.")
            return None

        logger.info("Procesando token de sesión.")
        r_token_page = session.get(url_token)
        r_token_page.raise_for_status()

        url_dashboard = parsers.obtener_url_meta_refresh(
            r_token_page.text, f"{config.BASE_URL}/siped"
        )
        
        # Validamos estrictamente frame_principal.php como medida de seguridad
        if not url_dashboard or "frame_principal.php" not in url_dashboard:
            logger.error("Destino principal inaccesible.")
            return None

        logger.info("Verificando acceso al sistema.")
        session.get(url_dashboard)

        logger.info(f"Autenticación completada para el usuario: {usuario}.")
        return dict_from_cookiejar(session.cookies)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión durante la autenticación: {e}")
        return None
    except Exception as e:
        logger.error("Error interno durante la autenticación", exc_info=True)
        return None

def crear_sesion_con_cookies(cookies_dict):
    """
    Crea una nueva sesión de 'requests' y le carga las cookies.
    Devuelve la sesión lista para usar.
    """
    session = requests.Session()
    session.headers.update(config.BROWSER_HEADERS)
    if cookies_dict:
        session.cookies = cookiejar_from_dict(cookies_dict)
    return session