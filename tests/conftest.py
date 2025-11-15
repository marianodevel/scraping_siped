import pytest
from app import app as flask_app  # Importa tu aplicación Flask
import config  # Importa tu configuración
import os

# --- Fixtures de Datos (HTML Falsos) ---
# Usaremos esto para probar los parsers sin tocar la red.


@pytest.fixture
def html_login_refresh():
    """HTML de la página de login que redirige."""
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/servicios/inicio.php">
        </head>
    </html>
    """


@pytest.fixture
def html_menu_principal():
    """HTML del menú principal con el enlace al token."""
    return """
    <html>
        <body>
            <a href="/siped?token=abc123xyz">Acceso a SIPED</a>
        </body>
    </html>
    """


@pytest.fixture
def html_lista_expedientes_pagina_1():
    """HTML de una página de lista de expedientes."""
    return """
    <html>
        <body>
            <table class="table-striped">
                <tr><th>Expediente</th><th>Caratula</th><th>Partes</th><th>Estado</th><th>Fec. Ult. Mov.</th><th>Localidad</th><th>Dependencia</th><th>Secretaria</th></tr>
                <tr>
                    <td><a href="detalle.php?id=100">EXP-100/2025</a></td>
                    <td>PEREZ, JUAN C/ GOMEZ, MARIA</td>
                    <td>PARTES...</td>
                    <td>ESTADO...</td>
                    <td>FECHA...</td>
                    <td>LOCALIDAD...</td>
                    <td>DEP...</td>
                    <td>SEC...</td>
                </tr>
            </table>
            <button onclick="document.form.inicio.value=10; form.submit();">SIGUIENTE</button>
        </body>
    </html>
    """


@pytest.fixture
def html_lista_expedientes_pagina_final():
    """HTML de la última página (sin botón 'SIGUIENTE')."""
    return """
    <html>
        <body>
            <table class="table-striped">
                 <tr><th>Expediente</th><th>Caratula</th><th>Partes</th><th>Estado</th><th>Fec. Ult. Mov.</th><th>Localidad</th><th>Dependencia</th><th>Secretaria</th></tr>
                <tr>
                    <td><a href="detalle.php?id=110">EXP-110/2025</a></td>
                    <td>GONZALEZ, LUIS C/ DIAZ, ANA</td>
                    <td>PARTES...</td>
                    <td>ESTADO...</td>
                    <td>FECHA...</td>
                    <td>LOCALIDAD...</td>
                    <td>DEP...</td>
                    <td>SEC...</td>
                </tr>
            </table>
            </body>
    </html>
    """


@pytest.fixture
def html_detalle_expediente():
    """HTML de la página de detalle (para extraer params AJAX)."""
    return """
    <html>
        <body>
            <input type="hidden" name="id" value="100">
            <script>
                var dependencia_ide=12;
                var tj_fuero=3;
                var exp_organismo_origen=45;
                //... ver_mas_escritosAjax.php ...
            </script>
        </body>
    </html>
    """


@pytest.fixture
def html_ajax_movimientos():
    """HTML devuelto por la llamada AJAX de movimientos."""
    return """
    <table class="table-hover">
        <tr><th></th><th>Nombre</th><th>Fecha Presentación</th><th>Tipo</th><th>Estado</th><th>Generado Por</th><th>Descripción</th><th>Fecha Firma</th><th>Fecha Publicación</th></tr>
        <tr>
            <td></td>
            <td><form action="ver_escrito.php?id=999"></form>PROVEIDO</td>
            <td>01/01/2025</td>
            <td>TIPO...</td>
            <td>ESTADO...</td>
            <td>GENERADO...</td>
            <td><font title="Descripción..."></font></td>
            <td>FECHA...</td>
            <td>FECHA...</td>
        </tr>
    </table>
    """


@pytest.fixture
def html_pagina_documento():
    """HTML de la página final del documento/escrito."""
    return """
    <html>
        <body>
            <table>
                <tr><td><img src="SCescudo.png"></td></tr>
                <tr><td><strong class="Estilo1">Expediente: EXP-100/2025</strong></td></tr>
                <tr><td><strong>Dependencia X</strong></td></tr>
                <tr><td><strong>Secretaria Y</strong></td></tr>
                <tr><td>...</td></tr>
                <tr><td><strong>Cáratula: PEREZ, JUAN C/ GOMEZ, MARIA</strong></td></tr>
            </table>
            
            <table>
                <tr><td><strong>Código de Validación: ABC123DEF</strong></td></tr>
                <tr><td>...</td></tr>
                <tr>
                    <td>Nombre: PROVEIDO</td>
                    <td><strong>Código de Validación: ABC123DEF</strong></td>
                </tr>
            </table>

            <div id="editor-container">
                Texto principal del documento.
                Segunda línea.
            </div>

            <table>
                <tr><td><strong>Firmado electrónicamente por:</strong></td></tr>
                <tr><td>Cargo</td><td>Apellido y Nombre</td><td>Fecha</td></tr>
                <tr>
                    <td>JUEZ</td>
                    <td>DR. MARIANO DEVEL</td>
                    <td>01/01/2025 10:00</td>
                </tr>
            </table>
        </body>
    </html>
    """


# --- Fixtures de Aplicación (Flask) ---


# *** CORRECCIÓN AQUÍ ***
# Añadimos scope="session" para que coincida con el scope de "live_server"
@pytest.fixture(scope="session")
def app():
    """Fixture de la aplicación Flask para pruebas."""
    # Configura la app para testing
    flask_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,  # Deshabilita CSRF en formularios de prueba
        }
    )

    # Asegurarnos de que los directorios de salida existan (para 'descargar')
    os.makedirs(config.DOCUMENTOS_OUTPUT_DIR, exist_ok=True)  #

    yield flask_app


@pytest.fixture
def client(app):
    """Cliente de prueba de Flask (para tests E2E de backend)."""
    return app.test_client()
