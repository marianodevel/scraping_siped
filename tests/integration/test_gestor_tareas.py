import gestor_tareas
from celery.result import AsyncResult
import pytest


# --- INICIO DEL NUEVO TEST ---
def test_obtener_estado_tarea_inicial_sin_id():
    """
    Prueba que el estado devuelto sea 'IDLE' y 'En espera'
    cuando no se proporciona ningún ID de tarea.
    """
    # Reseteamos cualquier estado anterior
    gestor_tareas.resetear_id_tarea("fase_1")  #

    # Llamamos a la función sin ID (id_tarea = None)
    estado = gestor_tareas.obtener_estado_tarea(None, "fase_1")  #

    # Verificamos el nuevo estado inicial corregido
    assert estado["estado"] == "IDLE"
    assert estado["resultado"] == "En espera"


# --- FIN DEL NUEVO TEST ---


# Usamos mocker para simular el objeto AsyncResult de Celery
def test_registrar_y_obtener_id(mocker):
    # Simulamos un objeto 'tarea' simple con un 'id'
    tarea_simulada = mocker.Mock()
    tarea_simulada.id = "task-123"

    gestor_tareas.registrar_tarea_iniciada("fase_1", tarea_simulada)  #
    assert gestor_tareas.obtener_id_tarea("fase_1") == "task-123"  #


def test_resetear_id_tarea(mocker):
    tarea_simulada = mocker.Mock()
    tarea_simulada.id = "task-456"

    gestor_tareas.registrar_tarea_iniciada("fase_2", tarea_simulada)  #
    assert gestor_tareas.obtener_id_tarea("fase_2") == "task-456"  #

    gestor_tareas.resetear_id_tarea("fase_2")  #
    assert gestor_tareas.obtener_id_tarea("fase_2") is None  #


def test_obtener_estado_tarea_exitosa(mocker):
    # Reseteamos el estado antes de empezar
    gestor_tareas.resetear_id_tarea("fase_1")  #

    # 1. Registramos una tarea
    tarea_simulada = mocker.Mock()
    tarea_simulada.id = "task-success"
    gestor_tareas.registrar_tarea_iniciada("fase_1", tarea_simulada)  #

    # 2. Simulamos la respuesta de AsyncResult
    mock_async_result = mocker.Mock(spec=AsyncResult)
    mock_async_result.state = "SUCCESS"
    mock_async_result.result = "Tarea completada"

    # 3. 'Parchamos' la importación de AsyncResult DENTRO de gestor_tareas
    mocker.patch("gestor_tareas.AsyncResult", return_value=mock_async_result)  #

    # 4. Verificamos el estado
    estado = gestor_tareas.obtener_estado_tarea("task-success", "fase_1")  #

    assert estado["estado"] == "SUCCESS"
    assert estado["resultado"] == "Tarea completada"

    # 5. Verificamos que se limpió el ID
    assert gestor_tareas.obtener_id_tarea("fase_1") is None  #
    # 6. Verificamos que 'forget' fue llamado
    mock_async_result.forget.assert_called_once()


def test_obtener_estado_tarea_pendiente(mocker):
    gestor_tareas.resetear_id_tarea("fase_1")  #

    tarea_simulada = mocker.Mock()
    tarea_simulada.id = "task-pending"
    gestor_tareas.registrar_tarea_iniciada("fase_1", tarea_simulada)  #

    mock_async_result = mocker.Mock(spec=AsyncResult)
    mock_async_result.state = "PENDING"
    mock_async_result.result = None

    mocker.patch("gestor_tareas.AsyncResult", return_value=mock_async_result)  #

    estado = gestor_tareas.obtener_estado_tarea("task-pending", "fase_1")  #

    assert estado["estado"] == "PENDING"
    # --- INICIO DE LA CORRECCIÓN DEL TEST ---
    # El resultado debería ser "En cola..." (basado en el nuevo gestor_tareas.py)
    assert estado["resultado"] == "En cola..."
    # --- FIN DE LA CORRECCIÓN DEL TEST ---
    # No debe limpiarse el ID
    assert gestor_tareas.obtener_id_tarea("fase_1") == "task-pending"  #
    mock_async_result.forget.assert_not_called()
