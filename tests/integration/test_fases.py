import pytest
from fases.fase_1 import ejecutar_fase_1_lista  #
from fases.fase_2 import ejecutar_fase_2_movimientos  #
import config  #
import utils  #

# --- Pruebas para Fase 1 ---


def test_ejecutar_fase_1_exito(mocker):
    """Prueba el flujo exitoso de la Fase 1."""

    # 1. Datos simulados que devolverá el scraper
    datos_simulados = [
        {"expediente": "EXP-100/2025", "caratula": "PEREZ..."},
        {"expediente": "EXP-101/2025", "caratula": "GOMEZ..."},
    ]

    # 2. Mockear las dependencias
    # No necesitamos 'session' real, pero el decorador la crea.
    # Simulamos 'raspar_lista_expedientes' para que devuelva nuestros datos.
    mock_scraper = mocker.patch(
        "fases.fase_1.scraper_tasks.raspar_lista_expedientes",
        return_value=datos_simulados,
    )  #

    # Simulamos 'guardar_a_csv' para espiar si se llama correctamente.
    mock_guardar = mocker.patch("fases.fase_1.utils.guardar_a_csv")  #

    # Simulamos el decorador para que no intente crear una sesión real
    # *** CORRECCIÓN AQUÍ ***
    # Apuntamos a 'utils.session_manager', que es donde se importa
    mocker.patch(
        "utils.session_manager.crear_sesion_con_cookies", return_value=mocker.Mock()
    )  #

    # 3. Ejecutar la función
    # Pasamos cookies falsas, serán usadas por el decorador (mockeado)
    resultado = ejecutar_fase_1_lista(cookies={"fake": "cookie"})

    # 4. Verificar resultados

    # Se llamó al scraper
    mock_scraper.assert_called_once()

    # Se llamó a guardar_a_csv con los datos correctos y el nombre de archivo correcto
    mock_guardar.assert_called_with(datos_simulados, config.LISTA_EXPEDIENTES_CSV)  #

    # El mensaje de resultado es correcto
    assert "Total: 2" in resultado


def test_ejecutar_fase_1_sin_expedientes(mocker):
    """Prueba qué pasa si el scraper no devuelve nada."""

    # 1. Scraper devuelve lista vacía
    mock_scraper = mocker.patch(
        "fases.fase_1.scraper_tasks.raspar_lista_expedientes", return_value=[]
    )  #
    mock_guardar = mocker.patch("fases.fase_1.utils.guardar_a_csv")  #

    # *** CORRECCIÓN AQUÍ ***
    mocker.patch(
        "utils.session_manager.crear_sesion_con_cookies", return_value=mocker.Mock()
    )  #

    # 2. Ejecutar
    resultado = ejecutar_fase_1_lista(cookies={"fake": "cookie"})

    # 3. Verificar
    mock_scraper.assert_called_once()
    # No se debe llamar a guardar si no hay datos
    mock_guardar.assert_not_called()
    assert "No se encontraron expedientes" in resultado


# --- Pruebas para Fase 2 ---


def test_ejecutar_fase_2(mocker, fs):
    """Prueba el flujo de la Fase 2 usando un sistema de archivos falso."""

    # 1. Datos simulados (lista de expedientes leída de CSV)
    lista_expedientes_csv = [
        {"expediente": "EXP-100", "caratula": "PEREZ"},
        {"expediente": "EXP-200", "caratula": "GOMEZ (YA EXISTE)"},
    ]

    # 2. Movimientos simulados (devueltos por el scraper)
    movimientos_exp_100 = [{"nombre_escrito": "Mov 1"}, {"nombre_escrito": "Mov 2"}]

    # 3. Crear el CSV falso de la Fase 1 (fs)
    # (Necesitaríamos la función 'guardar_a_csv' real o simularla aquí)
    # Por simplicidad, simulamos 'leer_csv_a_diccionario'
    mocker.patch(
        "fases.fase_2.utils.leer_csv_a_diccionario", return_value=lista_expedientes_csv
    )  #

    # 4. Crear un archivo CSV de movimientos "existente"
    fs.create_dir(config.MOVIMIENTOS_OUTPUT_DIR)  #
    ruta_existente = f"{config.MOVIMIENTOS_OUTPUT_DIR}/EXP-200 - GOMEZ (YA EXISTE).csv"
    fs.create_file(ruta_existente)

    # 5. Mockear el scraper de movimientos
    mock_scraper_mov = mocker.patch(
        "fases.fase_2.scraper_tasks.raspar_movimientos_de_expediente",
        return_value=movimientos_exp_100,
    )  #

    # 6. Mockear el guardado de CSV
    mock_guardar = mocker.patch("fases.fase_2.utils.guardar_a_csv")  #

    # *** CORRECCIÓN AQUÍ ***
    mocker.patch(
        "utils.session_manager.crear_sesion_con_cookies", return_value=mocker.Mock()
    )  #

    # 7. Ejecutar Fase 2
    resultado = ejecutar_fase_2_movimientos(cookies={"fake": "cookie"})

    # 8. Verificar

    # Solo se debe llamar al scraper UNA VEZ (para EXP-100),
    # ya que EXP-200 se salta.
    mock_scraper_mov.assert_called_once()

    # Se debe llamar a guardar UNA VEZ
    ruta_esperada_nuevo = "EXP-100 - PEREZ.csv"
    mock_guardar.assert_called_once_with(
        movimientos_exp_100,
        ruta_esperada_nuevo,
        subdirectory=config.MOVIMIENTOS_OUTPUT_DIR,  #
    )

    assert "Total de movimientos descargados (nuevos): 2" in resultado
