import pytest
import time

# --- ¡Nuevos imports para Selenium! ---
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Esta fixture 'live_server' (de pytest-flask) sigue siendo la misma.
# La fixture 'selenium' (de pytest-selenium) reemplaza a 'page'.
# 'mocker' (de pytest-mock) sigue siendo el mismo.


def test_flujo_login_y_arrancar_fase(selenium, live_server, mocker):
    """
    Prueba el flujo completo desde el punto de vista del usuario
    con Selenium.
    """

    # --- 1. Mocks (¡Exactamente igual que antes!) ---
    fake_cookies = {"JSESSIONID": "e2e-selenium-test-cookie"}
    mock_auth = mocker.patch(
        "app.session_manager.autenticar_en_siped", return_value=fake_cookies
    )  #
    mocker.patch(
        "app.gestor_tareas.obtener_estado_tarea",
        return_value={"estado": "IDLE", "resultado": "En espera"},
    )  #
    mock_tarea = mocker.Mock(id="fake-celery-task-id-e2e")
    mock_delay = mocker.patch("app.fase_1_lista_task.delay", return_value=mock_tarea)  #
    mocker.patch("app.gestor_tareas.registrar_tarea_iniciada")  #

    # --- 2. Ir a la página de Login ---
    selenium.get(live_server.url() + "/login")  #

    # --- 3. Llenar el formulario y Enviar ---
    # WTForms genera 'id' para los campos, así que usamos By.ID
    selenium.find_element(By.ID, "username").send_keys("test_usuario")
    selenium.find_element(By.ID, "password").send_keys("test_password")
    # El botón 'submit' de WTForms usualmente tiene name="submit"
    selenium.find_element(By.NAME, "submit").click()

    # --- 4. Verificar Redirección y Estado ---

    # Esperamos a que la URL cambie al índice (ruta "/")
    WebDriverWait(selenium, timeout=5).until(EC.url_contains(live_server.url() + "/"))

    # Verificar que el mock de autenticación fue llamado
    mock_auth.assert_called_with("test_usuario", "test_password")

    # Esperamos a que aparezca el mensaje de bienvenida y el estado
    wait = WebDriverWait(selenium, timeout=5)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), '¡Bienvenido, test_usuario!')]")
        )
    )

    # --- INICIO DE LA CORRECCIÓN DEL TEST ---
    # Buscamos el nuevo texto "En espera" y el badge "IDLE"
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'En espera')]")
        )
    )
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='estado-fase_1']//*[contains(text(), 'IDLE')]")
        )
    )
    # --- FIN DE LA CORRECCIÓN DEL TEST ---

    # --- 5. Iniciar la Fase 1 ---

    # Cambiamos el mock para el polling
    mocker.patch(
        "app.gestor_tareas.obtener_estado_tarea",
        return_value={"estado": "PENDING", "resultado": "Tarea iniciada..."},
    )  #

    # El ID es 'estado-fase_1' (con guion bajo)
    fase_1_control = selenium.find_element(By.ID, "estado-fase_1")
    fase_1_control.find_element(
        By.XPATH, ".//button[contains(text(), 'Iniciar')]"
    ).click()

    # --- 6. Verificar el resultado (Polling) ---

    # Esperamos a que el texto "PENDING" aparezca (usando el ID corregido)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='estado-fase_1']//*[contains(text(), 'PENDING')]")
        )
    )

    # Verificamos el mensaje flash
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                f"//*[contains(text(), 'Fase 1 iniciada con ID: {mock_tarea.id}')]",
            )
        )
    )


def test_flujo_completo_de_estado_ui_polling(selenium, live_server, mocker):
    """
    Testea el ciclo de vida completo de la UI para una tarea con Selenium:
    IDLE -> PENDING -> SUCCESS -> IDLE
    """

    # --- Mocks Iniciales ---
    mocker.patch(
        "app.session_manager.autenticar_en_siped", return_value={"cookie": "123"}
    )  #
    mock_get_estado = mocker.patch(
        "app.gestor_tareas.obtener_estado_tarea",
        return_value={"estado": "IDLE", "resultado": "En espera"},
    )  #
    mock_tarea = mocker.Mock(id="task-123")
    mocker.patch("app.fase_1_lista_task.delay", return_value=mock_tarea)  #
    mocker.patch("app.gestor_tareas.registrar_tarea_iniciada")  #

    # --- 1. Cargar la página y verificar estado IDLE ---
    selenium.get(live_server.url() + "/login")  #
    selenium.find_element(By.ID, "username").send_keys("user")
    selenium.find_element(By.ID, "password").send_keys("pass")
    selenium.find_element(By.NAME, "submit").click()

    # Esperar a que cargue el índice
    wait = WebDriverWait(selenium, timeout=5)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), '¡Bienvenido, user!')]")
        )
    )

    # Localizar el contenedor de la Fase 1 (usando el ID corregido)
    fase_1_control = selenium.find_element(By.ID, "estado-fase_1")
    iniciar_btn = fase_1_control.find_element(
        By.XPATH, ".//button[contains(text(), 'Iniciar')]"
    )

    # --- INICIO DE LA CORRECCIÓN DEL TEST ---
    # Verificar estado inicial IDLE y texto "En espera"
    wait.until(
        EC.visibility_of(
            fase_1_control.find_element(By.XPATH, ".//*[contains(text(), 'IDLE')]")
        )
    )
    wait.until(
        EC.visibility_of(
            fase_1_control.find_element(By.XPATH, ".//*[contains(text(), 'En espera')]")
        )
    )
    assert iniciar_btn.is_enabled()
    # --- FIN DE LA CORRECCIÓN DEL TEST ---

    # --- 2. Iniciar Tarea y verificar estado PENDING ---
    # Actualizamos mock para que devuelva "En cola..." (más semántico)
    mock_get_estado.return_value = {"estado": "PENDING", "resultado": "En cola..."}
    iniciar_btn.click()

    # Verificar que el badge cambia a PENDING (usando el ID corregido)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='estado-fase_1']//*[contains(text(), 'PENDING')]")
        )
    )
    # Verificar que el texto cambia a "En cola..."
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='estado-fase_1']//*[contains(text(), 'En cola...')]")
        )
    )

    # Verificar que el botón está deshabilitado
    iniciar_btn_actualizado = selenium.find_element(
        By.ID, "estado-fase_1"
    ).find_element(By.XPATH, ".//button[contains(text(), 'Iniciar')]")
    assert not iniciar_btn_actualizado.is_enabled()

    # --- 3. Simular fin de Tarea y verificar estado SUCCESS ---
    mock_get_estado.return_value = {
        "estado": "SUCCESS",
        "resultado": "Completado!",
    }

    # Esperar a que el polling detecte el estado SUCCESS (usando el ID corregido)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='estado-fase_1']//*[contains(text(), 'SUCCESS')]")
        )
    )

    # Verificar que el resultado se muestra
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Completado!')]")
        )
    )

    # El botón 'Iniciar' debería volver a estar habilitado
    iniciar_btn_final = selenium.find_element(By.ID, "estado-fase_1").find_element(
        By.XPATH, ".//button[contains(text(), 'Iniciar')]"
    )
    assert iniciar_btn_final.is_enabled()


def test_race_condition_doble_clic(selenium, live_server, mocker):
    """
    Testea qué pasa si el usuario hace doble clic muy rápido en 'Iniciar'.
    """

    # --- Mocks ---
    mocker.patch(
        "app.session_manager.autenticar_en_siped", return_value={"cookie": "123"}
    )  #
    mocker.patch(
        "app.gestor_tareas.obtener_estado_tarea",
        return_value={"estado": "IDLE", "resultado": "En espera"},
    )  #
    mock_tarea = mocker.Mock(id="task-unico-id")
    mock_delay = mocker.patch("app.fase_1_lista_task.delay", return_value=mock_tarea)  #

    # --- Cargar página ---
    selenium.get(live_server.url() + "/login")  #
    selenium.find_element(By.ID, "username").send_keys("user")
    selenium.find_element(By.ID, "password").send_keys("pass")
    selenium.find_element(By.NAME, "submit").click()

    wait = WebDriverWait(selenium, timeout=5)

    # --- INICIO DE LA CORRECCIÓN DEL TEST ---
    # Buscamos el nuevo texto "En espera"
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'En espera')]")
        )
    )
    # --- FIN DE LA CORRECCIÓN DEL TEST ---

    # --- Simular Clics Rápidos ---
    iniciar_btn = selenium.find_element(By.ID, "estado-fase_1").find_element(
        By.XPATH, ".//button[contains(text(), 'Iniciar')]"
    )

    iniciar_btn.click()
    try:
        selenium.find_element(By.ID, "estado-fase_1").find_element(
            By.XPATH, ".//button[contains(text(), 'Iniciar')]"
        ).click()
    except Exception:
        pass

    # --- Verificar ---
    mock_delay.assert_called_once()

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Fase 1 iniciada')]")
        )
    )


# ==================================================
# ===== INICIO DEL TEST Y FIXTURE AÑADIDOS =====
# ==================================================


@pytest.fixture
def mock_backend(mocker):
    """
    Fixture para mockear el backend.
    Simula el login y la base de datos de estados de tareas.
    """

    # 1. Mockear el login (usando el prefijo 'app.' como en los otros tests)
    mocker.patch(
        "app.session_manager.autenticar_en_siped",
        return_value={"siped_cookies": "dummy-auth-token"},
    )

    # 2. Mockear el inicio de las tareas (para que no se llamen a Celery)
    mocker.patch("app.tasks.fase_1_lista_task.delay")
    mocker.patch("app.tasks.fase_2_movimientos_task.delay")
    mocker.patch("app.tasks.fase_3_documentos_task.delay")

    # 3. Simular la base de datos de estado de tareas (p.ej. Redis)
    #    Esto nos da control total sobre lo que ve el frontend.
    test_states = {
        "fase_1": {"estado": "IDLE", "resultado": "Sin iniciar"},
        "fase_2": {"estado": "IDLE", "resultado": "Sin iniciar"},
        "fase_3": {"estado": "IDLE", "resultado": "Sin iniciar"},
    }

    # 4. Mockear la función que lee los estados
    def get_mock_state(task_id, nombre_fase):
        # El task_id es ignorado, solo usamos el nombre_fase
        # para devolver el estado que definimos en este test.
        return test_states.get(
            nombre_fase, {"estado": "FAILURE", "resultado": "Fase desconocida"}
        )

    mocker.patch("app.gestor_tareas.obtener_estado_tarea", side_effect=get_mock_state)

    # Devolvemos el dict de estados para que
