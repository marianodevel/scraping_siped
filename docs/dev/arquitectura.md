# Arquitectura del Sistema SIPED

SIPED se estructura como una aplicación distribuida orientada a la extracción y consolidación de información jurídica, separando estrictamente la presentación de las tareas de cómputo intensivo.

## Topología de Componentes

1. **Interfaz Web (Flask):** Actúa como el panel de control del operador. Maneja la autenticación y despacha comandos hacia el encolador de tareas. No ejecuta procesos de red externos para evitar bloqueos del hilo principal.
2. **Gestor de Colas (Redis):** Intermediario de mensajería (Broker) que almacena el estado y los resultados temporales de las ejecuciones.
3. **Workers Asíncronos (Celery):** Procesos en segundo plano encargados de ejecutar las fases. Dependen estrictamente del módulo `scraper_tasks`.
4. **Persistencia Híbrida:**
   - **Estructurada (SQLite):** A través de `db_manager`, gestiona el índice relacional de expedientes y sus historiales.
   - **Física (Archivos):** Los documentos consolidados y los resúmenes en CSV se vuelcan directamente al sistema de almacenamiento persistente (`datos_usuarios/`), facilitando la portabilidad operativa.

## Patrones de Diseño Centrales

- **Inyección de Sesiones:** La autenticación se evalúa únicamente en los puntos de entrada (rutas Flask o inicio de scripts CLI). Posteriormente, el `session_manager` inyecta las credenciales en estado activo hacia los módulos inferiores.
- **Diferimiento de Procesamiento Lógico:** El análisis de los DOMs HTML ocurre de forma aislada en `parsers.py`, blindando a `scraper_tasks.py` frente a variaciones estructurales de los portales externos.
