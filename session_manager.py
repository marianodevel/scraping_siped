# session_manager.py
import requests
import config
import parsers


class SessionManager:
    def __init__(self):
        """Prepara la sesión y realiza la autenticación."""
        print("Iniciando Session Manager...")
        if not config.USUARIO or not config.CLAVE:
            raise ValueError(
                "Las variables USUARIO_INTRANET y CLAVE_INTRANET no están cargadas."
            )

        self.session = requests.Session()
        self.session.headers.update(config.BROWSER_HEADERS)
        self._authenticate()

    def _authenticate(self):
        """Contiene toda la lógica de login y navegación hasta el dashboard."""
        try:
            # FASE 1: LOGIN (POST)
            print(f"Iniciando sesión como {config.USUARIO}...")
            credenciales = {"usuario": config.USUARIO, "pass": config.CLAVE}
            r_login = self.session.post(config.LOGIN_URL, data=credenciales)
            r_login.raise_for_status()

            # FASE 2: SEGUIR META REFRESH a 'inicio.php'
            url_inicio = parsers.obtener_url_meta_refresh(
                r_login.text, f"{config.BASE_URL}/servicios"
            )
            if not url_inicio:
                raise Exception("Login falló: No se pudo encontrar la URL 'inicio.php'")

            print("Navegando al menú principal...")
            r_menu = self.session.get(url_inicio)
            r_menu.raise_for_status()

            # FASE 3: ENCONTRAR Y SEGUIR ENLACE 'siped?token='
            url_token = parsers.obtener_enlace_token_siped(r_menu.text)
            if not url_token:
                raise Exception(
                    "Error de Flujo: No se pudo encontrar el enlace token en el menú."
                )

            print("Siguiendo enlace token...")
            r_token_page = self.session.get(url_token)
            r_token_page.raise_for_status()

            # FASE 4: SEGUIR META REFRESH FINAL a 'frame_principal'
            url_dashboard = parsers.obtener_url_meta_refresh(
                r_token_page.text, f"{config.BASE_URL}/siped"
            )
            if not url_dashboard or "frame_principal.php" not in url_dashboard:
                raise Exception(
                    "Error de Flujo: No se pudo encontrar la URL 'frame_principal.php'."
                )

            print("Aterrizando en el Dashboard...")
            self.session.get(url_dashboard)
            print("¡Sesión autenticada y lista!")

        except requests.exceptions.RequestException as e:
            print(f"Error fatal de conexión durante la autenticación: {e}")
            raise
        except Exception as e:
            print(f"Error durante la autenticación: {e}")
            raise

    def get_session(self):
        """Devuelve la sesión autenticada."""
        return self.session
