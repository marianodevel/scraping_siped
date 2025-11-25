import os
import pytest
import sys
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parsers
import config


# --- Utilería para cargar fixtures ---
def cargar_fixture(nombre_archivo):
    ruta = os.path.join(os.path.dirname(__file__), "fixtures", nombre_archivo)
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# --- Tests Unitarios ---


def test_parsear_lista_expedientes():
    """Verifica que se extraigan correctamente los dicts de la tabla de expedientes."""
    html_content = cargar_fixture("lista_expedientes.html")

    resultados = parsers.parsear_lista_expedientes(html_content)

    # Verificaciones
    assert len(resultados) == 2, "Debería haber encontrado 2 expedientes"

    # Chequear el primer expediente
    exp1 = resultados[0]
    assert exp1["expediente"] == "1001/2023"
    assert exp1["caratula"] == "GARCIA C/ PEREZ S/ DAÑOS"
    assert exp1["localidad"] == "RIO GALLEGOS"
    # Verificar que construyó la URL absoluta correctamente usando config.LISTA_EXPEDIENTES_URL
    assert "ver_detalle.php?id=123" in exp1["link_detalle"]


def test_encontrar_siguiente_pagina():
    """Verifica que detecte el número de inicio para la paginación."""
    html_content = cargar_fixture("lista_expedientes.html")
    siguiente = parsers.encontrar_siguiente_pagina_inicio(html_content)
    assert siguiente == 10


def test_obtener_url_meta_refresh():
    """Verifica la extracción de la URL del meta tag refresh."""
    html_content = cargar_fixture("meta_refresh.html")
    # Pasamos una base_path ficticia
    url = parsers.obtener_url_meta_refresh(html_content, "http://base.com")
    assert "inicio.php" in url


def test_parsear_movimientos():
    """Verifica que se extraigan los movimientos de la tabla AJAX."""
    html_content = cargar_fixture("movimientos.html")
    # Simulamos que esto pertenece al exp 1001/2023
    movs = parsers.parsear_movimientos_de_ajax_html(html_content, "1001/2023")

    assert len(movs) == 1
    mov = movs[0]
    assert mov["expediente_nro"] == "1001/2023"
    assert "DECRETO" in mov["nombre_escrito"]
    assert mov["fecha_presentacion"] == "10/10/2023"
    assert mov["descripcion"] == "Vistos los autos..."
    # Verificar link
    assert "ver_escrito.php?id=999" in mov["link_escrito"]


def test_normalizar_url_pdf():
    """Test aislado para la lógica de limpieza de URLs de PDF."""
    # Caso 1: URL relativa simple
    url = parsers.normalizar_url_pdf("archivo.pdf", "principal")
    assert url.startswith(config.BASE_URL)

    # Caso 2: Corrección de path 'pdfabogado' (Lógica específica de tu parser)
    url_sucia = "/pdfabogado.php?id=1"
    url_limpia = parsers.normalizar_url_pdf(url_sucia, "principal")
    assert "/siped/agrega_plantilla/" in url_limpia
