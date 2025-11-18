# tests/conftest.py
import pytest
import config
from app import app as flask_app  # Importación necesaria para el fixture app


@pytest.fixture
def app():
    """
    Fixture de la aplicación Flask requerido por pytest-flask.
    Configura la app en modo TESTING.
    """
    flask_app.config.update(
        {
            "TESTING": True,
        }
    )
    return flask_app


@pytest.fixture
def html_login_refresh():
    return """
    <html>
    <head>
    <meta http-equiv="Refresh" content="0; url=/servicios/inicio.php">
    </head>
    <body>...</body>
    </html>
    """


@pytest.fixture
def html_menu_principal():
    return f"""
    <html>
    <body>
    <a href="{config.BASE_URL}/siped?token=abc123xyz">SIPED</a>
    </body>
    </html>
    """


@pytest.fixture
def html_lista_expedientes_pagina_1():
    """
    Fixture de lista de expedientes.
    Debe tener la estructura exacta que espera parsers.py (8 columnas).
    """
    return f"""
    <html>
    <body>
        <table class="table-striped">
            <tr><td>Expediente</td><td>Caratula</td><td>Partes</td><td>Estado</td><td>Fec. Ult. Mov.</td><td>Localidad</td><td>Dependencia</td><td>Secretaria</td></tr>
            <tr>
                <td><a href="detalle.php?id=100">EXP-100/2025</a></td>
                <td>PEREZ, JUAN C/ GOMEZ, MARIA</td>
                <td>Parte A, Parte B</td>
                <td>TRAMITE</td>
                <td>01/01/2025</td>
                <td>RG</td>
                <td>JUZGADO</td>
                <td>SECRETARIA 1</td>
            </tr>
        </table>
        <button onclick="document.form.inicio.value=10; document.form.submit();">SIGUIENTE</button>
    </body>
    </html>
    """


@pytest.fixture
def html_lista_expedientes_pagina_final():
    return """
    <html>
    <body>
        <table class="table-striped">
            <tr><td>Expediente</td><td>Caratula</td><td>Partes</td><td>Estado</td><td>Fec. Ult. Mov.</td><td>Localidad</td><td>Dependencia</td><td>Secretaria</td></tr>
            </table>
    </body>
    </html>
    """


@pytest.fixture
def html_detalle_expediente():
    """
    Fixture para probar la extracción de parámetros AJAX.
    Incluye variables JS con espacios para probar la robustez del regex.
    """
    return """
    <html>
    <head>
    <script>
        var dependencia_ide = 12; 
        var tj_fuero = 3;
        var exp_organismo_origen = 45;
        // Comentarios extra...
    </script>
    </head>
    <body>
        <form name="form">
            <input type="hidden" name="id" value="100">
        </form>
    </body>
    </html>
    """


@pytest.fixture
def html_ajax_movimientos():
    """
    Fixture para tabla de movimientos.
    Debe tener al menos 9 columnas.
    """
    return f"""
    <table class="table-hover">
        <thead><tr><th>#</th><th>Escrito</th><th>Fecha Pres.</th><th>Tipo</th><th>Estado</th><th>Generado por</th><th>Descripción</th><th>Fecha Firma</th><th>Fecha Pub.</th></tr></thead>
        <tbody>
            <tr>
                <td>1</td>
                <td><form action="{config.BASE_URL}/siped/expediente/buscar/ver_escrito.php?id=999">PROVEIDO</form></td>
                <td>01/01/2025</td>
                <td>TIPO A</td>
                <td>PUBLICADO</td>
                <td>USUARIO X</td>
                <td><font title="DESCRIPCION CORTA">...</font></td>
                <td>01/01/2025</td>
                <td>01/01/2025</td>
            </tr>
        </tbody>
    </table>
    """


@pytest.fixture
def html_pagina_documento_pdfs():
    """
    Fixture para documento individual.
    Simula URLs mal formadas para probar la normalización.
    """
    return f"""
    <html>
    <body>
        <div class="titulo">
            <h2>Expediente: EXP-100/2025</h2>
        </div>
        
        <table class="tabla_borsua">
             <tr><td colspan="6"><strong class="Estilo1">Expediente: FALLBACK-000</strong></td></tr>
             <tr><td colspan="6"><strong>Cáratula: PEREZ, JUAN C/ GOMEZ, MARIA</strong></td></tr>
        </table>
        
        <div>
            <div align="center"> 
                 <a class="btn btn-primary" href="https://intranet.jussantacruz.gob.ar/agrega_plantilla/pdfabogadoanterior.php?id_escrito=2552363">
                    <i class="fa fa-download"></i> Descargar archivo PDF
                 </a> 
            </div>
        </div>
        
        <div class="container">    
            <table class="tabla_borsua">
                <tr><td class="alert-warning">
                    <a href="ver_adjunto_escrito.php?adjunto=UNO"> OFI00134404.PDF </a>
                </td></tr>
                <tr><td class="alert-warning">
                    <a href="ver_adjunto_escrito.php?adjunto=DOS"> ESCRITO_EXTRA.PDF </a>
                </td></tr>
            </table>
        </div>
        
        <table>
            <tr><td>Cargo</td></tr>
            <tr><td>JUEZ</td><td>DR. MARIANO DEVEL</td><td>01/01/2025</td></tr>
        </table>
    </body>
    </html>
    """
