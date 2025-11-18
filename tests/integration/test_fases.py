# tests/integration/test_fases.py
import pytest
from fases.fase_1 import ejecutar_fase_1_lista
from fases.fase_2 import ejecutar_fase_2_movimientos
from fases.fase_3 import ejecutar_fase_3_documentos
import config
import utils

# --- Pruebas para Fase 1 ---


def test_ejecutar_fase_1_exito(mocker):
    # Datos simulados
    datos_simulados = [
        {"expediente": "EXP-100/2025", "caratula": "PEREZ..."},
        {"expediente": "EXP-101/2025", "caratula": "GOMEZ..."},
    ]

    mock_scraper = mocker.patch(
        "fases.fase_1.scraper_tasks.raspar_lista_expedientes",
        return_value=datos_simulados,
    )
    mock_guardar = mocker.patch("fases.fase_1.utils.guardar_a_csv")
    mocker.patch(
        "utils.session_manager.crear_sesion_con_cookies", return_value=mocker.Mock()
    )

    resultado = ejecutar_fase_1_lista(cookies={"fake": "cookie"})

    mock_scraper.assert_called_once()
    mock_guardar.assert_called_with(datos_simulados, config.LISTA_EXPEDIENTES_CSV)
    assert "Total: 2" in resultado


def test_ejecutar_fase_1_sin_expedientes(mocker):
    mock_scraper = mocker.patch(
        "fases.fase_1.scraper_tasks.raspar_lista_expedientes", return_value=[]
    )
    mock_guardar = mocker.patch("fases.fase_1.utils.guardar_a_csv")
    mocker.patch(
        "utils.session_manager.crear_sesion_con_cookies", return_value=mocker.Mock()
    )

    resultado = ejecutar_fase_1_lista(cookies={"fake": "cookie"})

    mock_scraper.assert_called_once()
    mock_guardar.assert_not_called()
    assert "No se encontraron expedientes" in resultado


# --- Pruebas para Fase 2 ---


def test_ejecutar_fase_2(mocker, fs):
    lista_expedientes_csv = [
        {"expediente": "EXP-100", "caratula": "PEREZ"},
        {"expediente": "EXP-200", "caratula": "GOMEZ (YA EXISTE)"},
    ]
    movimientos_exp_100 = [{"nombre_escrito": "Mov 1"}, {"nombre_escrito": "Mov 2"}]

    mocker.patch(
        "fases.fase_2.utils.leer_csv_a_diccionario", return_value=lista_expedientes_csv
    )

    fs.create_dir(config.MOVIMIENTOS_OUTPUT_DIR)
    ruta_existente = f"{config.MOVIMIENTOS_OUTPUT_DIR}/EXP-200 - GOMEZ (YA EXISTE).csv"
    fs.create_file(ruta_existente)

    mock_scraper_mov = mocker.patch(
        "fases.fase_2.scraper_tasks.raspar_movimientos_de_expediente",
        return_value=movimientos_exp_100,
    )
    mock_guardar = mocker.patch("fases.fase_2.utils.guardar_a_csv")
    mocker.patch(
        "utils.session_manager.crear_sesion_con_cookies", return_value=mocker.Mock()
    )

    resultado = ejecutar_fase_2_movimientos(cookies={"fake": "cookie"})

    mock_scraper_mov.assert_called_once()
    mock_guardar.assert_called_once_with(
        movimientos_exp_100,
        "EXP-100 - PEREZ.csv",
        subdirectory=config.MOVIMIENTOS_OUTPUT_DIR,
    )
    assert "Total de movimientos descargados (nuevos): 2" in resultado


# --- Pruebas para Fase 3 (Descarga y Fusión) ---


def test_ejecutar_fase_3_descarga_y_fusion(mocker, fs):
    """
    Prueba el flujo de Fase 3 con URLs simuladas.
    """
    # 1. Datos
    expedientes_simulados = [{"expediente": "EXP-100/2025", "caratula": "PEREZ"}]
    movimientos_simulados = [
        {"link_escrito": "url_mov_1"},
        {"link_escrito": "url_mov_2"},
    ]

    # 2. Mock del resultado del parser (simulando URLs YA normalizadas por el parser)
    pdf_data_mov_1 = {
        "url_pdf_principal": "https://intranet.jussantacruz.gob.ar/siped/agrega_plantilla/pdfabogado.php?id=1",
        "adjuntos": [
            {
                "nombre": "adjunto_a.pdf",
                "url": "https://intranet.jussantacruz.gob.ar/siped/expediente/buscar/ver_adjunto_escrito.php?id=a",
            }
        ],
        "texto_providencia": "Se prioriza descarga de PDF.",
        "expediente_nro": "EXP-100/2025",
        "caratula": "PEREZ",
    }
    pdf_data_mov_2 = {
        "url_pdf_principal": "https://intranet.jussantacruz.gob.ar/siped/agrega_plantilla/pdfabogadoanterior.php?id=2",
        "adjuntos": [],
        "texto_providencia": "Se prioriza descarga de PDF.",
        "expediente_nro": "EXP-100/2025",
        "caratula": "PEREZ",
    }

    # 3. Mocks
    mocker.patch(
        "fases.fase_3.utils.leer_csv_a_diccionario",
        side_effect=[expedientes_simulados, movimientos_simulados],
    )

    # Mock raspar_contenido_documento para devolver los datos con URLs correctas
    mock_scraper_doc = mocker.patch(
        "fases.fase_3.scraper_tasks.raspar_contenido_documento",
        side_effect=[pdf_data_mov_1, pdf_data_mov_2],
    )

    # Mock descarga
    mock_descargar = mocker.patch(
        "fases.fase_3.scraper_tasks.descargar_archivo", return_value=True
    )

    # Mock fusión
    mock_fusionar = mocker.patch("fases.fase_3.utils.fusionar_pdfs")

    # FS
    exp_dir_name = (
        utils.limpiar_nombre_archivo("EXP-100/2025")
        + " - "
        + utils.limpiar_nombre_archivo("PEREZ")
    )
    exp_dir = f"{config.DOCUMENTOS_OUTPUT_DIR}/{exp_dir_name}"
    fs.create_dir(config.DOCUMENTOS_OUTPUT_DIR)
    fs.create_dir(exp_dir)

    # Simular que el PDF principal del Mov 2 ya existe (para probar el skip)
    pdf_a_saltar = f"{exp_dir}/02_principal.pdf"
    fs.create_file(pdf_a_saltar)

    mocker.patch(
        "utils.session_manager.crear_sesion_con_cookies", return_value=mocker.Mock()
    )

    # Ejecutar
    resultado = ejecutar_fase_3_documentos(cookies={"fake": "cookie"})

    # Validar
    assert mock_scraper_doc.call_count == 2

    # Verificar llamadas a descargar:
    # 1. Mov 1 Principal
    # 2. Mov 1 Adjunto
    # (Mov 2 Principal SKIPPED)
    assert mock_descargar.call_count == 2

    # Verificar fusión
    ruta_final = f"{config.DOCUMENTOS_OUTPUT_DIR}/{exp_dir_name} (Consolidado).pdf"
    mock_fusionar.assert_called_once_with(exp_dir, ruta_final)
    assert "Proceso de descarga" in resultado
