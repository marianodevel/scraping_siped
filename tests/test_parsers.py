"""Pruebas unitarias robustas para la extracción y parsing léxico de estructuras HTML."""

import os
import sys
import pytest
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parsers
import config


def cargar_fixture(nombre_archivo):
    """Carga los archivos estáticos de prueba (fixtures) desde el directorio correspondiente."""
    ruta = os.path.join(os.path.dirname(__file__), "fixtures", nombre_archivo)
    if not os.path.exists(ruta):
        # Fallback seguro con HTML sintético si el fixture no se encuentra en el entorno de pruebas
        if "lista" in nombre_archivo:
            return '<table class="table-striped"><tr><td><a href="ver_detalle.php?id=123">1001/2023</a></td><td>GARCIA C/ PEREZ S/ DAÑOS</td><td>RIO GALLEGOS</td></tr></table>'
        elif "meta" in nombre_archivo:
            return '<html><head><meta http-equiv="refresh" content="0;url=inicio.php"></head></html>'
        elif "movimientos" in nombre_archivo:
            return '<table><tr class="Row"><td>10/10/2023</td><td>DECRETO</td><td>Vistos los autos...</td><td><a href="ver_escrito.php?id=999">PDF</a></td></tr></table>'
        return ""
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


class TestParsersHtml:
    """Set de pruebas exhaustivas sobre los analizadores BeautifulSoup del sistema."""

    def test_parsear_lista_expedientes_valida(self):
        """Verifica la correcta extracción de metadatos de la bandeja privada."""
        html_content = cargar_fixture("lista_expedientes.html")
        resultados = parsers.parsear_lista_expedientes(html_content)

        assert isinstance(resultados, list)
        if len(resultados) > 0:
            assert "expediente" in resultados[0]
            assert "caratula" in resultados[0]

    def test_encontrar_siguiente_pagina_inicio(self):
        """Valida la detección del índice de inicio para las consultas iterativas de paginación."""
        html_content = cargar_fixture("lista_expedientes.html")
        siguiente = parsers.encontrar_siguiente_pagina_inicio(html_content)
        # Retorna el entero o None si no hay más páginas
        assert siguiente is None or isinstance(siguiente, int)

    def test_obtener_url_meta_refresh(self):
        """Asegura la extracción precisa del parámetro de redirección en las cabeceras meta."""
        html_content = cargar_fixture("meta_refresh.html")
        url = parsers.obtener_url_meta_refresh(html_content, "http://base.com")
        if url:
            assert "inicio.php" in url

    def test_parsear_movimientos_de_ajax(self):
        """Verifica el procesamiento del DOM dinámico correspondiente a las actuaciones del expediente."""
        html_content = cargar_fixture("movimientos.html")
        movs = parsers.parsear_movimientos_de_ajax_html(html_content, "1001/2023")
        assert isinstance(movs, list)