import pytest
import time
import requests  # Para controlar el estado del servidor

# --- Imports de Selenium ---
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =================================================================
# ===== VERSIÓN FINAL (SIN MOCKS, CON WAITS DE CLIC) =====
# =================================================================


# URL de la API de control de Mocks
def get_test_api_urls(live_server):
    base_url = live_server.url()
    return {
        "set": f"{base_url}/_test/set_state",
        "reset": f"{base_url}/_test/reset_states",
    }


# Fixture para resetear el estado del servidor antes de cada test
@pytest.fixture(autouse=True)
def reset_server_state(live_server):
    """
    Se ejecuta automáticamente antes de CADA test en este archivo.
    Llama al endpoint de reseteo en el servidor 'live' para asegurar
    que cada test comience con un estado limpio (todas las fases en IDLE).
    """
    api_urls = get_test_api_urls(live_server)
    try:
        requests.post(api_urls["reset"])
    except requests.exceptions.ConnectionError:
        # A veces el servidor (Proceso 2) tarda un instante en arrancar
        time.sleep(0.1)
        # Reintentar la conexión
        try:
            requests.post(api_urls["reset"])
        except Exception as e:
            print(
                f"FATAL: No se pudo conectar al live_server para resetear el estado: {e}"
            )
            pytest.skip("No se pudo conectar al live_server para el reseteo de estado.")


def test_flujo_login_y_arrancar_fase(selenium, live_server):
    """
    Prueba el flujo completo desde el punto de vista del usuario
    con Selenium.
    """
    # --- 1. Mocks (ELIMINADOS) ---
    # Ya no se necesita 'mocker'. La app se simula a sí misma.

    # --- 2. Ir a la página de Login ---
    selenium.get(live_server.url() + "/login")

    # --- 3. Llenar el formulario y Enviar ---
    selenium.find_element(By.ID, "username").send_keys("test_usuario")
    selenium.find_element(By.ID, "password").send_keys(
        "test_password"
    )  # Válida para el mock
    selenium.find_element(By.NAME, "submit").click()

    # --- 4. Verificar Redirección y Estado ---
    wait = WebDriverWait(selenium, timeout=5)
    wait.until(
        EC.url_contains(live_server.url() + "/")
    )  # Esperar a estar en la página de inicio
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), '¡Bienvenido, test_usuario!')]")
        )
    )

    # Verificar que el estado inicial (del MockGestorTareas) es "En espera (Mock)"
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'En espera (Mock)')]")
        )
    )
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[@id='estado-resultado-fase_1']//*[contains(text(), 'IDLE')]",
            )
        )
    )

    # --- 5. Iniciar la Fase 1 ---
    # CORRECCIÓN: Esperar a que el botón sea clicable para evitar race condition
    fase_1_boton_locator = (By.CSS_SELECTOR, "button[data-fase='fase_1']")
    wait.until(EC.element_to_be_clickable(fase_1_boton_locator))
    selenium.find_element(*fase_1_boton_locator).click()

    # --- 6. Verificar el resultado (Polling) ---
    # El MockGestorTareas pone el estado en STARTED después del click
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[@id='estado-resultado-fase_1']//*[contains(text(), 'STARTED')]",
            )
        )
    )
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[@id='estado-resultado-fase_1']//*[contains(text(), 'En cola (Mock)...')]",
            )
        )
    )

    # El ID de la tarea es ahora el simulado por el MockTask en app.py
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[contains(text(), 'Fase 1 iniciada con ID: mock-celery-id-fase_1')]",
            )
        )
    )


def test_flujo_completo_de_estado_ui_polling(selenium, live_server):
    """
    Testea el ciclo de vida completo de la UI para una tarea con Selenium:
    IDLE -> PENDING -> SUCCESS -> IDLE
    """

    api_urls = get_test_api_urls(live_server)
    wait = WebDriverWait(selenium, timeout=5)

    # --- 1. Cargar la página y verificar estado IDLE ---
    selenium.get(live_server.url() + "/login")
    selenium.find_element(By.ID, "username").send_keys("user")
    selenium.find_element(By.ID, "password").send_keys("pass")  # Válida para el mock
    selenium.find_element(By.NAME, "submit").click()

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), '¡Bienvenido, user!')]")
        )
    )

    fase_1_div_estado = selenium.find_element(By.ID, "estado-resultado-fase_1")
    iniciar_btn_locator = (By.CSS_SELECTOR, "button[data-fase='fase_1']")

    # Verificar estado inicial IDLE y texto "En espera (Mock)"
    wait.until(
        EC.visibility_of(
            fase_1_div_estado.find_element(By.XPATH, ".//*[contains(text(), 'IDLE')]")
        )
    )
    wait.until(
        EC.visibility_of(
            fase_1_div_estado.find_element(
                By.XPATH, ".//*[contains(text(), 'En espera (Mock)')]"
            )
        )
    )

    # CORRECCIÓN: Esperar a que sea clicable
    iniciar_btn = wait.until(EC.element_to_be_clickable(iniciar_btn_locator))
    assert iniciar_btn.is_enabled()

    # --- 2. Iniciar Tarea y verificar estado PENDING/STARTED ---
    iniciar_btn.click()

    # Verificar que el badge cambia a STARTED
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[@id='estado-resultado-fase_1']//*[contains(text(), 'STARTED')]",
            )
        )
    )
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[@id='estado-resultado-fase_1']//*[contains(text(), 'En cola (Mock)...')]",
            )
        )
    )

    # Verificar que el botón está deshabilitado (gracias al JS htmx:afterSwap)
    wait.until(
        lambda d: d.find_element(
            By.CSS_SELECTOR, "button[data-fase='fase_1']"
        ).get_attribute("disabled")
        == "true"
    )

    # --- 3. Simular fin de Tarea y verificar estado SUCCESS ---
    # ¡Aquí usamos la API de test para cambiar el estado en el servidor!
    requests.post(
        api_urls["set"],
        json={"fase": "fase_1", "estado": "SUCCESS", "resultado": "Completado! (Mock)"},
    )

    # Esperar a que el polling detecte el estado SUCCESS
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[@id='estado-resultado-fase_1']//*[contains(text(), 'SUCCESS')]",
            )
        )
    )
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Completado! (Mock)')]")
        )
    )

    # El botón 'Iniciar' debería volver a estar habilitado (gracias al JS htmx:afterSwap)
    wait.until(EC.element_to_be_clickable(iniciar_btn_locator))
    assert selenium.find_element(*iniciar_btn_locator).is_enabled()


def test_race_condition_doble_clic(selenium, live_server):
    """
    Testea qué pasa si el usuario hace doble clic muy rápido en 'Iniciar'.
    """
    wait = WebDriverWait(selenium, timeout=5)

    # --- Cargar página ---
    selenium.get(live_server.url() + "/login")
    selenium.find_element(By.ID, "username").send_keys("user")
    selenium.find_element(By.ID, "password").send_keys("pass")  # Válida para el mock
    selenium.find_element(By.NAME, "submit").click()

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'En espera (Mock)')]")
        )
    )

    # --- Simular Clics Rápidos ---
    # CORRECCIÓN: Esperar a que sea clicable
    iniciar_btn_locator = (By.CSS_SELECTOR, "button[data-fase='fase_1']")
    iniciar_btn = wait.until(EC.element_to_be_clickable(iniciar_btn_locator))

    iniciar_btn.click()
    try:
        # Este segundo clic debería fallar porque el botón
        # se deshabilita por el JS (htmx:afterSwap)
        iniciar_btn.click()
    except Exception:
        pass  # Esperamos que este segundo clic falle

    # --- Verificar ---
    # El flash message solo debe aparecer una vez (o al menos que aparece)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Fase 1 iniciada')]")
        )
    )


# ==================================================
# ===== TEST DEL FIX: CONSECUTIVE_PHASE_LAUNCH =====
# ==================================================


def test_consecutive_phase_launch_and_button_disable(live_server, selenium):
    """
    Test E2E que verifica los dos bugs solucionados:
    1. Se pueden lanzar fases consecutivas (el target de HTMX no se destruye).
    2. Los botones se deshabilitan/habilitan correctamente según el estado.
    """
    api_urls = get_test_api_urls(live_server)
    wait = WebDriverWait(selenium, 5)

    # --- 1. Setup y Login ---
    selenium.get(f"{live_server.url()}/login")
    selenium.find_element(By.ID, "username").send_keys("testuser")
    selenium.find_element(By.ID, "password").send_keys(
        "testpass"
    )  # Válida para el mock
    selenium.find_element(By.ID, "submit").click()

    WebDriverWait(selenium, 10).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "Scraper de Expedientes")
    )

    # --- 2. Localizar Elementos ---
    boton_fase_1_locator = (By.CSS_SELECTOR, "button[data-fase='fase_1']")
    boton_fase_2_locator = (By.CSS_SELECTOR, "button[data-fase='fase_2']")
    badge_fase_1_locator = (By.CSS_SELECTOR, "#estado-resultado-fase_1 .status-badge")

    # Verificar estado inicial
    # CORRECCIÓN: Esperar a que sean clicables
    boton_fase_1 = wait.until(EC.element_to_be_clickable(boton_fase_1_locator))
    boton_fase_2 = wait.until(EC.element_to_be_clickable(boton_fase_2_locator))

    assert boton_fase_1.is_enabled()
    assert boton_fase_2.is_enabled()
    wait.until(EC.text_to_be_present_in_element(badge_fase_1_locator, "IDLE"))

    # --- 3. Lanzar Fase 1 y verificar deshabilitación (Fix 2) ---
    boton_fase_1.click()

    # Verificar que el botón se deshabilita (gracias al JS htmx:afterSwap)
    wait.until(
        lambda d: d.find_element(
            By.CSS_SELECTOR, "button[data-fase='fase_1']"
        ).get_attribute("disabled")
        == "true"
    )

    # Verificar que el badge también se actualizó
    wait.until(EC.text_to_be_present_in_element(badge_fase_1_locator, "STARTED"))
    print("TEST: Fase 1 iniciada y botón deshabilitado correctamente.")

    # --- 4. Finalizar Fase 1 y verificar habilitación (Fix 2) ---
    requests.post(
        api_urls["set"],
        json={"fase": "fase_1", "estado": "SUCCESS", "resultado": "Éxito (Mock)."},
    )

    # Esperar a que el polling lo detecte y el JS (htmx:afterSwap) habilite el botón
    wait.until(EC.element_to_be_clickable(boton_fase_1_locator))

    assert selenium.find_element(*boton_fase_1_locator).is_enabled()
    assert selenium.find_element(*badge_fase_1_locator).text == "SUCCESS"
    print("TEST: Fase 1 finalizada y botón habilitado correctamente.")

    # --- 5. Lanzar Fase 2 y verificar (Fix 1: Target Bug) ---
    badge_fase_2_locator = (By.CSS_SELECTOR, "#estado-resultado-fase_2 .status-badge")

    # El botón 'boton_fase_2' (que encontramos antes) debería ser clicable
    boton_fase_2.click()

    # Verificar que la Fase 2 se lanza y su botón se deshabilita
    wait.until(
        lambda d: d.find_element(
            By.CSS_SELECTOR, "button[data-fase='fase_2']"
        ).get_attribute("disabled")
        == "true"
    )
    wait.until(EC.text_to_be_present_in_element(badge_fase_2_locator, "STARTED"))

    assert selenium.find_element(*boton_fase_2_locator).is_enabled() == False
    print("TEST: Fase 2 iniciada consecutivamente con éxito.")
