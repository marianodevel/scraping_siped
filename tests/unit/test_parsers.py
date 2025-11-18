# tests/unit/test_parsers.py
import parsers
import config

# --- Pruebas de Navegación/Login ---


def test_obtener_url_meta_refresh(html_login_refresh):
    url_base = f"{config.BASE_URL}/servicios"
    url = parsers.obtener_url_meta_refresh(html_login_refresh, url_base)
    assert url == f"{config.BASE_URL}/servicios/inicio.php"


def test_obtener_enlace_token_siped(html_menu_principal):
    url = parsers.obtener_enlace_token_siped(html_menu_principal)
    assert url == f"{config.BASE_URL}/siped?token=abc123xyz"


# --- Pruebas de Fase 1 (Lista) ---


def test_parsear_lista_expedientes(html_lista_expedientes_pagina_1):
    expedientes = parsers.parsear_lista_expedientes(html_lista_expedientes_pagina_1)
    assert len(expedientes) == 1
    assert expedientes[0]["expediente"] == "EXP-100/2025"
    assert expedientes[0]["caratula"] == "PEREZ, JUAN C/ GOMEZ, MARIA"
    assert (
        expedientes[0]["link_detalle"]
        == f"{config.BASE_URL}/siped/expediente/buscar/detalle.php?id=100"
    )


def test_encontrar_siguiente_pagina_inicio(html_lista_expedientes_pagina_1):
    inicio = parsers.encontrar_siguiente_pagina_inicio(html_lista_expedientes_pagina_1)
    assert inicio == 10


def test_encontrar_siguiente_pagina_fin(html_lista_expedientes_pagina_final):
    inicio = parsers.encontrar_siguiente_pagina_inicio(
        html_lista_expedientes_pagina_final
    )
    assert inicio is None


# --- Pruebas de Fase 2 (Movimientos) ---


def test_parsear_detalle_para_ajax_params(html_detalle_expediente):
    params = parsers.parsear_detalle_para_ajax_params(html_detalle_expediente)
    assert params["exp_id"] == "100"
    assert params["dependencia_ide"] == "12"
    assert params["tj_fuero"] == "3"
    assert params["exp_organismo_origen"] == "45"


def test_parsear_movimientos_de_ajax_html(html_ajax_movimientos):
    movimientos = parsers.parsear_movimientos_de_ajax_html(
        html_ajax_movimientos, "EXP-100/2025"
    )
    assert len(movimientos) == 1
    assert movimientos[0]["expediente_nro"] == "EXP-100/2025"
    assert movimientos[0]["nombre_escrito"] == "PROVEIDO"
    assert (
        movimientos[0]["link_escrito"]
        == f"{config.BASE_URL}/siped/expediente/buscar/ver_escrito.php?id=999"
    )


# --- Pruebas de Lógica de Normalización de URL (NUEVO) ---


def test_normalizar_url_pdf_principal():
    # Caso 1: URL relativa incompleta (pdfabogado.php)
    url_rel = "agrega_plantilla/pdfabogado.php?id=123"
    res = parsers.normalizar_url_pdf(url_rel, "principal")
    assert (
        res
        == "https://intranet.jussantacruz.gob.ar/siped/agrega_plantilla/pdfabogado.php?id=123"
    )

    # Caso 2: URL absoluta incorrecta (falta /siped/)
    url_abs_bad = (
        "https://intranet.jussantacruz.gob.ar/agrega_plantilla/pdfabogado.php?id=123"
    )
    res = parsers.normalizar_url_pdf(url_abs_bad, "principal")
    assert (
        res
        == "https://intranet.jussantacruz.gob.ar/siped/agrega_plantilla/pdfabogado.php?id=123"
    )

    # Caso 3: URL absoluta incorrecta con variante (pdfabogadoanterior.php)
    url_antigua = "https://intranet.jussantacruz.gob.ar/agrega_plantilla/pdfabogadoanterior.php?id=456"
    res = parsers.normalizar_url_pdf(url_antigua, "principal")
    assert (
        res
        == "https://intranet.jussantacruz.gob.ar/siped/agrega_plantilla/pdfabogadoanterior.php?id=456"
    )


def test_normalizar_url_pdf_adjunto():
    # Caso 1: URL relativa sin siped
    url_rel = "ver_adjunto_escrito.php?id=789"
    res = parsers.normalizar_url_pdf(url_rel, "adjunto")
    assert (
        res
        == "https://intranet.jussantacruz.gob.ar/siped/expediente/buscar/ver_adjunto_escrito.php?id=789"
    )

    # Caso 2: URL absoluta incorrecta (falta /siped/expediente/buscar/)
    url_abs_bad = "https://intranet.jussantacruz.gob.ar/ver_adjunto_escrito.php?id=789"
    res = parsers.normalizar_url_pdf(url_abs_bad, "adjunto")
    assert (
        res
        == "https://intranet.jussantacruz.gob.ar/siped/expediente/buscar/ver_adjunto_escrito.php?id=789"
    )


# --- Pruebas de Fase 3 (Documento con PDFs) ---


def test_parsear_pagina_documento_pdf_links(html_pagina_documento_pdfs):
    """
    Prueba la nueva lógica de parsing con el fixture actualizado.
    """
    data = parsers.parsear_pagina_documento(html_pagina_documento_pdfs)

    # 1. Verificar metadatos (extraídos del div.titulo o fallback)
    assert data["expediente_nro"] == "EXP-100/2025"
    assert data["caratula"] == "PEREZ, JUAN C/ GOMEZ, MARIA"

    # 2. Verificar que se extrajo y normalizó el PDF principal (pdfabogadoanterior)
    assert data["url_pdf_principal"] is not None
    # El fixture usa la versión "anterior" mal formada para probar la corrección
    assert "siped/agrega_plantilla/pdfabogadoanterior.php" in data["url_pdf_principal"]

    # 3. Verificar adjuntos
    assert len(data["adjuntos"]) == 2
    assert data["adjuntos"][0]["nombre"] == "OFI00134404.PDF"
    # Verificar que la URL del adjunto se normalizó (se agregó /siped/expediente/buscar/)
    assert (
        "siped/expediente/buscar/ver_adjunto_escrito.php" in data["adjuntos"][0]["url"]
    )

    # 4. Verificar texto placeholder
    assert data["texto_providencia"] == "Se prioriza descarga de PDF."
