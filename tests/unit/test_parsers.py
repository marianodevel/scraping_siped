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


# --- Pruebas de Fase 3 (Documento) ---


def test_parsear_pagina_documento(html_pagina_documento):
    data = parsers.parsear_pagina_documento(html_pagina_documento)

    # Datos del expediente
    assert data["expediente_nro"] == "EXP-100/2025"
    assert data["caratula"] == "PEREZ, JUAN C/ GOMEZ, MARIA"

    # Datos del escrito
    assert data["nombre_escrito"] == "PROVEIDO"
    assert data["codigo_validacion"] == "ABC123DEF"

    # Texto principal
    assert "Texto principal del documento." in data["texto_providencia"]
    assert "Segunda línea." in data["texto_providencia"]

    # Firmantes
    assert len(data["firmantes"]) == 1
    assert data["firmantes"][0]["cargo"] == "JUEZ"
    assert data["firmantes"][0]["nombre"] == "DR. MARIANO DEVEL"
    assert data["firmantes"][0]["fecha"] == "01/01/2025 10:00"
