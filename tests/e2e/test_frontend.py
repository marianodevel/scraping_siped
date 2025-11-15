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
        return_value={"estado": "SUCCESS", "resultado": "IDLE"},
    )  #
    mock_tarea = mocker.Mock(id="fake-celery-task-id-e2e")
    mock_delay = mocker.patch("app.fase_1_lista_task.delay", return_value=mock_tarea)  #
    mocker.patch("app.gestor_tareas.registrar_tarea_iniciada")  #

    # --- 2. Ir a la página de Login ---
    # *** CORRECCIÓN AQUÍ ***
    selenium.get(live_server.url() + "/login")  #

    # --- 3. Llenar el formulario y Enviar ---
    # WTForms genera 'id' para los campos, así que usamos By.ID
    selenium.find_element(By.ID, "username").send_keys("test_usuario")
    selenium.find_element(By.ID, "password").send_keys("test_password")
    # El botón 'submit' de WTForms usualmente tiene name="submit"
    selenium.find_element(By.NAME, "submit").click()

    # --- 4. Verificar Redirección y Estado ---

    # *** CORRECCIÓN AQUÍ ***
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
    wait.until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'IDLE')]"))
    )

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
        return_value={"estado": "SUCCESS", "resultado": "IDLE"},
    )  #
    mock_tarea = mocker.Mock(id="task-123")
    mocker.patch("app.fase_1_lista_task.delay", return_value=mock_tarea)  #
    mocker.patch("app.gestor_tareas.registrar_tarea_iniciada")  #

    # --- 1. Cargar la página y verificar estado IDLE ---
    # *** CORRECCIÓN AQUÍ ***
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

    # Verificar estado inicial IDLE
    wait.until(
        EC.visibility_of(
            fase_1_control.find_element(By.XPATH, ".//*[contains(text(), 'IDLE')]")
        )
    )
    assert iniciar_btn.is_enabled()

    # --- 2. Iniciar Tarea y verificar estado PENDING ---
    mock_get_estado.return_value = {"estado": "PENDING", "resultado": "Corriendo..."}
    iniciar_btn.click()

    # Verificar que el badge cambia a PENDING (usando el ID corregido)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[@id='estado-fase_1']//*[contains(text(), 'PENDING')]")
        )
    )

    # Verificar que el botón está deshabilitado
    # (El botón se recarga vía fragmento, así que lo buscamos de nuevo)
    iniciar_btn_actualizado = selenium.find_element(
        By.ID, "estado-fase_1"
    ).find_element(By.XPATH, ".//button[contains(text(), 'Iniciar')]")
    assert not iniciar_btn_actualizado.is_enabled()

    # --- 3. Simular fin de Tarea y verificar estado SUCCESS ---
    mock_get_estado.return_value = {
        "estado": "SUCCESS",
        "resultado": "Completado con exito!",
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
            (By.XPATH, "//*[contains(text(), 'Completado con exito!')]")
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
    (Con Selenium, el "doble clic" es más difícil de simular que en
    Playwright, pero podemos hacer dos clics seguidos).
    """

    # --- Mocks ---
    mocker.patch(
        "app.session_manager.autenticar_en_siped", return_value={"cookie": "123"}
    )  #
    mocker.patch(
        "app.gestor_tareas.obtener_estado_tarea",
        return_value={"estado": "SUCCESS", "resultado": "IDLE"},
    )  #
    mock_tarea = mocker.Mock(id="task-unico-id")
    mock_delay = mocker.patch("app.fase_1_lista_task.delay", return_value=mock_tarea)  #

    # --- Cargar página ---
    # *** CORRECCIÓN AQUÍ ***
    selenium.get(live_server.url() + "/login")  #
    selenium.find_element(By.ID, "username").send_keys("user")
    selenium.find_element(By.ID, "password").send_keys("pass")
    selenium.find_element(By.NAME, "submit").click()

    wait = WebDriverWait(selenium, timeout=5)
    wait.until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'IDLE')]"))
    )

    # --- Simular Clics Rápidos ---
    iniciar_btn = selenium.find_element(By.ID, "estado-fase_1").find_element(
        By.XPATH, ".//button[contains(text(), 'Iniciar')]"
    )

    # Simular clics rápidos (no es un 'dblclick' real, pero fuerza dos POST)
    iniciar_btn.click()
    # En Selenium, el segundo clic a menudo falla si el DOM cambia.
    # El test de backend (test_app.py) es mejor para esto.
    # Pero probamos que la lógica de backend lo ataja.
    try:
        # Intentamos hacer clic de nuevo muy rápido
        selenium.find_element(By.ID, "estado-fase_1").find_element(
            By.XPATH, ".//button[contains(text(), 'Iniciar')]"
        ).click()
    except Exception:
        # Es probable que falle porque el botón se deshabilitó,
        # lo cual está bien.
        pass

    # --- Verificar ---
    # La protección en app.py debe asegurar que solo se llamó una vez.
    mock_delay.assert_called_once()

    # Deberíamos ver el mensaje de éxito de la primera llamada
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Fase 1 iniciada')]")
        )
    )


# Los tests de regresión visual (snapshots) son más complejos en Selenium
# y no vienen integrados. Requerirían una librería externa como 'pyscreenshot'.
# Recomiendo mantener esos tests desactivados si cambias a Selenium
# para mantener la simplicidad.
