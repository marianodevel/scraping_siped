import requests
import config
import parsers
from requests.utils import dict_from_cookiejar, cookiejar_from_dict


def autenticar_en_siped(usuario, clave):
    if not usuario or not clave:
        print("Error: Credenciales incompletas.")
        return None

    session = requests.Session()
    session.headers.update(config.BROWSER_HEADERS)

    try:
        print(f"Autenticando usuario: {usuario}.")
        credenciales = {"usuario": usuario, "pass": clave}
        r_login = session.post(config.LOGIN_URL, data=credenciales)
        r_login.raise_for_status()

        url_inicio = parsers.obtener_url_meta_refresh(
            r_login.text, f"{config.BASE_URL}/servicios"
        )
        if not url_inicio:
            print("Error de autenticación: Redirección fallida.")
            return None

        print("Accediendo al menú principal.")
        r_menu = session.get(url_inicio)
        r_menu.raise_for_status()

        url_token = parsers.obtener_enlace_token_siped(r_menu.text)
        if not url_token:
            print("Error: Token de sesión no encontrado.")
            return None

        print("Procesando token de sesión.")
        r_token_page = session.get(url_token)
        r_token_page.raise_for_status()

        url_dashboard = parsers.obtener_url_meta_refresh(
            r_token_page.text, f"{config.BASE_URL}/siped"
        )
        if not url_dashboard or "frame_principal.php" not in url_dashboard:
            print("Error: Destino principal inaccesible.")
            return None

        print("Verificando acceso al sistema.")
        session.get(url_dashboard)

        print(f"Autenticación completada para el usuario: {usuario}.")

        return dict_from_cookiejar(session.cookies)

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión durante la autenticación: {e}")
        return None
    except Exception as e:
        print(f"Error interno durante la autenticación: {e}")
        return None


def crear_sesion_con_cookies(cookies_dict):
    session = requests.Session()
    session.headers.update(config.BROWSER_HEADERS)

    if cookies_dict:
        session.cookies = cookiejar_from_dict(cookies_dict)

    return session
