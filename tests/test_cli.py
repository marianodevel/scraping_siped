import pytest
from script.cli_lista_expedientes import main_lista
from script.cli_movimientos import main_movimientos
from script.cli_un_expediente import main as main_un_expediente

def test_cli_lista_exitoso(mocker):
    mocker.patch("builtins.input", return_value="user")
    mocker.patch("getpass.getpass", return_value="pass")
    mocker.patch("session_manager.autenticar_en_siped", return_value={"cookie": "ok"})
    mocker.patch("session_manager.crear_sesion_con_cookies")
    mocker.patch("scraper_tasks.raspar_lista_expedientes", return_value=[{"expediente": "001"}])
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp")
    mocker.patch("utils.guardar_a_csv")
    mock_print = mocker.patch("builtins.print")
    
    main_lista()
    assert any("Total: 1" in str(call) for call in mock_print.call_args_list)

def test_cli_movimientos_exitoso(mocker):
    mocker.patch("builtins.input", return_value="user")
    mocker.patch("getpass.getpass", return_value="pass")
    mocker.patch("session_manager.autenticar_en_siped", return_value={"cookie": "ok"})
    mocker.patch("session_manager.crear_sesion_con_cookies")
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp")
    mocker.patch("utils.leer_csv_a_diccionario", return_value=[{"expediente": "001", "link_detalle": "http"}])
    mocker.patch("scraper_tasks.raspar_movimientos_de_expediente", return_value=[{"tramite": "TEST"}])
    mocker.patch("utils.guardar_a_csv")
    mock_print = mocker.patch("builtins.print")
    
    main_movimientos()
    assert any("1 expedientes" in str(call) for call in mock_print.call_args_list)

def test_cli_movimientos_sin_maestro(mocker):
    mocker.patch("builtins.input", return_value="user")
    mocker.patch("getpass.getpass", return_value="pass")
    mocker.patch("session_manager.autenticar_en_siped", return_value={"cookie": "ok"})
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp")
    mocker.patch("utils.leer_csv_a_diccionario", return_value=None) 
    mock_print = mocker.patch("builtins.print")
    
    main_movimientos()
    assert any("Ejecute Fase 1" in str(call) for call in mock_print.call_args_list)

def test_cli_un_expediente_exitoso(mocker):
    # args: usuario, índice de expediente (1-based) en lugar de la carátula
    mocker.patch("builtins.input", side_effect=["user", "1"])
    mocker.patch("getpass.getpass", return_value="pass")
    mocker.patch("session_manager.autenticar_en_siped", return_value={"cookie": "ok"})
    mocker.patch("session_manager.crear_sesion_con_cookies")
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp")
    mocker.patch("utils.leer_csv_a_diccionario", return_value=[{"expediente": "001/2026", "caratula": "TEST", "link_detalle": "http"}])
    mocker.patch("scraper_tasks.raspar_movimientos_de_expediente", return_value=[{"tramite": "TEST", "link_escrito": "http"}])
    mocker.patch("utils.guardar_a_csv")
    mocker.patch("scraper_tasks.raspar_contenido_documento", return_value={"url_pdf_principal": "http://pdf", "adjuntos": []})
    mocker.patch("scraper_tasks.descargar_archivo", return_value=True)
    mocker.patch("utils.fusionar_pdfs")
    mock_print = mocker.patch("builtins.print")
    
    main_un_expediente()
    assert any("Proceso completado" in str(call) for call in mock_print.call_args_list)