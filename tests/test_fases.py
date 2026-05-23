import pytest
from fases.fase_1 import ejecutar_fase_1_lista
from fases.fase_2 import ejecutar_fase_2_movimientos
from fases.fase_3 import ejecutar_fase_3_documentos
from fases.fase_unico import ejecutar_fase_unico

def test_fase_1_exitoso(mocker):
    # Pasamos un diccionario simulado de cookies en lugar de un objeto Mock
    mocker.patch("session_manager.crear_sesion_con_cookies", return_value=mocker.Mock())
    mocker.patch("scraper_tasks.raspar_lista_expedientes", return_value=[{"expediente": "123/2026", "caratula": "TEST"}])
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp/test")
    mocker.patch("utils.guardar_a_csv")
    mocker.patch("db_manager.upsert_expedientes")
    
    resultado = ejecutar_fase_1_lista({"cookie": "ok"}, "user")
    assert "Total: 1" in resultado

def test_fase_1_sin_resultados(mocker):
    mocker.patch("session_manager.crear_sesion_con_cookies", return_value=mocker.Mock())
    mocker.patch("scraper_tasks.raspar_lista_expedientes", return_value=[])
    
    resultado = ejecutar_fase_1_lista({"cookie": "ok"}, "user")
    assert "No se encontraron" in resultado

def test_fase_2_movimientos_exitoso(mocker):
    mocker.patch("session_manager.crear_sesion_con_cookies", return_value=mocker.Mock())
    mocker.patch("db_manager.obtener_expedientes", return_value=[{"expediente": "001", "link_detalle": "http"}])
    mocker.patch("scraper_tasks.raspar_movimientos_de_expediente", return_value=[{"tramite": "Escrito"}])
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp/test")
    mocker.patch("utils.guardar_a_csv")
    
    # Se ignora el guardado en base de datos si la función no existe en tu db_manager actual
    mocker.patch("db_manager.guardar_movimientos", create=True)
    
    resultado = ejecutar_fase_2_movimientos({"cookie": "ok"}, "user")
    assert "1 expedientes" in resultado

def test_fase_2_sin_expedientes(mocker):
    mocker.patch("session_manager.crear_sesion_con_cookies", return_value=mocker.Mock())
    mocker.patch("db_manager.obtener_expedientes", return_value=[])
    resultado = ejecutar_fase_2_movimientos({"cookie": "ok"}, "user")
    assert "No hay expedientes" in resultado

def test_fase_3_documentos_exitoso(mocker):
    mocker.patch("session_manager.crear_sesion_con_cookies", return_value=mocker.Mock())
    mocker.patch("db_manager.obtener_expedientes", return_value=[{"expediente": "001", "caratula": "TEST", "id": 1}])
    mocker.patch("db_manager.obtener_movimientos", return_value=[{"id": 10, "link_escrito": "http://doc"}])
    mocker.patch("scraper_tasks.raspar_contenido_documento", return_value={"url_pdf_principal": "http://pdf", "adjuntos": []})
    mocker.patch("scraper_tasks.descargar_archivo", return_value=True)
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp/test")
    
    # Corrección: tu función se llama fusionar_pdfs, no unir_pdfs
    mocker.patch("utils.fusionar_pdfs")
    mocker.patch("db_manager.actualizar_estado_movimiento", create=True)
    
    resultado = ejecutar_fase_3_documentos({"cookie": "ok"}, "user")
    assert "PDFs consolidados" in resultado

def test_fase_unico_exitoso(mocker):
    mocker.patch("session_manager.crear_sesion_con_cookies", return_value=mocker.Mock())
    mocker.patch("db_manager.obtener_expedientes", return_value=[{"expediente": "111/2026", "caratula": "TEST", "link_detalle": "http"}])
    mocker.patch("scraper_tasks.raspar_movimientos_de_expediente", return_value=[{"tramite": "TEST", "link_escrito": "http://doc"}])
    mocker.patch("utils.obtener_ruta_usuario", return_value="/tmp/test")
    mocker.patch("utils.guardar_a_csv")
    mocker.patch("db_manager.guardar_movimientos", create=True)
    mocker.patch("db_manager.obtener_movimientos", return_value=[{"id": 10, "link_escrito": "http://doc"}])
    mocker.patch("scraper_tasks.raspar_contenido_documento", return_value={"url_pdf_principal": "http://pdf", "adjuntos": []})
    mocker.patch("scraper_tasks.descargar_archivo", return_value=True)
    mocker.patch("utils.fusionar_pdfs")
    
    resultado = ejecutar_fase_unico({"cookie": "ok"}, "111/2026", "user")
    assert "completado exitosamente" in resultado

def test_fase_unico_no_encontrado(mocker):
    mocker.patch("session_manager.crear_sesion_con_cookies", return_value=mocker.Mock())
    mocker.patch("db_manager.obtener_expedientes", return_value=[{"expediente": "OTRO"}])
    resultado = ejecutar_fase_unico({"cookie": "ok"}, "FALSO", "user")
    assert "No se encontro" in resultado or "No se encontró" in resultado