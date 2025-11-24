import requests
import config
import parsers
from requests.utils import dict_from_cookiejar, cookiejar_from_dict


def autenticar_en_siped(usuario, clave):
    """
    Intenta autenticar un usuario y clave contra SIPED.
    Si tiene éxito, devuelve un dict de cookies.
    Si falla, devuelve None.
    """
    if not usuario or not clave:
        print("Error: Se requieren usuario y clave.")
        return None

    session = requests.Session()
    session.headers.update(config.BROWSER_HEADERS)

    try:
        # FASE 1: LOGIN (POST)
        print(f"Iniciando sesión como {usuario}...")
        credenciales = {"usuario": usuario, "pass": clave}
        r_login = session.post(config.LOGIN_URL, data=credenciales)
        r_login.raise_for_status()

        # FASE 2: SEGUIR META REFRESH a 'inicio.php'
        url_inicio = parsers.obtener_url_meta_refresh(
            r_login.text, f"{config.BASE_URL}/servicios"
        )
        if not url_inicio:
            print("Login falló: No se pudo encontrar la URL 'inicio.php'")
            return None

        print("Navegando al menú principal...")
        r_menu = session.get(url_inicio)
        r_menu.raise_for_status()

        # FASE 3: ENCONTRAR Y SEGUIR ENLACE 'siped?token='
        url_token = parsers.obtener_enlace_token_siped(r_menu.text)
        if not url_token:
            print("Error de Flujo: No se pudo encontrar el enlace token en el menú.")
            return None

        print("Siguiendo enlace token...")
        r_token_page = session.get(url_token)
        r_token_page.raise_for_status()

        # FASE 4: SEGUIR META REFRESH FINAL a 'frame_principal'
        url_dashboard = parsers.obtener_url_meta_refresh(
            r_token_page.text, f"{config.BASE_URL}/siped"
        )
        if not url_dashboard or "frame_principal.php" not in url_dashboard:
            print("Error de Flujo: No se pudo encontrar la URL 'frame_principal.php'.")
            return None

        print("Aterrizando en el Dashboard...")
        session.get(url_dashboard)

        print(f"¡Sesión para {usuario} autenticada y lista!")

        return dict_from_cookiejar(session.cookies)

    except requests.exceptions.RequestException as e:
        print(f"Error fatal de conexión durante la autenticación: {e}")
        return None
    except Exception as e:
        print(f"Error durante la autenticación: {e}")
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
