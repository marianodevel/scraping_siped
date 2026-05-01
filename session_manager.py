import requests
import config
import parsers
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
from logger import get_logger

logger = get_logger(__name__)

def autenticar_en_siped(usuario, clave):
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
            logger.error("Error de autenticacion: Redireccion fallida.")
            return None

        logger.info("Accediendo al menu principal.")
        r_menu = session.get(url_inicio)
        r_menu.raise_for_status()

        url_token = parsers.obtener_enlace_token_siped(r_menu.text)

        if not url_token:
            logger.error("Token de sesion no encontrado.")
            return None

        logger.info("Procesando token de sesion.")
        r_token_page = session.get(url_token)
        r_token_page.raise_for_status()

        url_dashboard = parsers.obtener_url_meta_refresh(
            r_token_page.text, f"{config.BASE_URL}/siped"
        )

        if not url_dashboard:
            logger.error("Destino principal inaccesible (Sin redireccion).")
            return None

        if "frame_principal.php" not in url_dashboard and "menu.php" not in url_dashboard:
            logger.warning(f"Destino inusual detectado: {url_dashboard}. Intentando continuar...")

        logger.info("Verificando acceso al sistema y seteando cookies definitivas.")
        session.get(url_dashboard)

        logger.info(f"Autenticacion completada para el usuario: {usuario}.")
        return dict_from_cookiejar(session.cookies)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexion durante la autenticacion: {e}")
        return None
    except Exception as e:
        logger.error(f"Error interno durante la autenticacion: {e}", exc_info=True)
        return None

def crear_sesion_con_cookies(cookies_dict):
    session = requests.Session()
    session.headers.update(config.BROWSER_HEADERS)
    if cookies_dict:
        session.cookies = cookiejar_from_dict(cookies_dict)
    return session