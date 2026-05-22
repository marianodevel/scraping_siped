# Manual de Usuario - Sistema SIPED

Este manual detalla los procedimientos operativos para la utilización de la interfaz web del Sistema Integrado de Extracción y Consolidación de Expedientes (SIPED).

## 1. Acceso al Sistema (Autenticación)
El acceso a la plataforma SIPED requiere las mismas credenciales utilizadas para el ingreso a la Intranet del Poder Judicial:
* **Usuario:** Número de CUIL o DNI.
* **Contraseña:** Su clave personal de acceso.

El sistema no almacena su contraseña de forma permanente; la utiliza únicamente para interactuar con los servidores y obtener un token de sesión seguro (cookie) que autoriza las transacciones durante su uso.

## 2. Panel de Control (Dashboard)
Una vez autenticado, ingresará al Panel de Control principal. Desde aquí podrá monitorear el estado de las tareas en segundo plano, visualizar los expedientes sincronizados y acceder a los documentos generados. Las operaciones se ejecutan de manera asíncrona, permitiéndole continuar navegando sin bloqueos.

## 3. Flujo de Trabajo Principal (Bandeja Privada)
El procesamiento masivo de los expedientes asignados a su cuenta se divide en tres fases secuenciales. Es imperativo respetar el orden de ejecución para garantizar la integridad de los datos.

* **Fase 1 (Sincronización Maestra):** Extrae el listado completo de expedientes vinculados a su usuario. Genera un archivo CSV general y actualiza el índice en la base de datos.
* **Fase 2 (Extracción de Movimientos):** Recorre cada expediente registrado y extrae el historial detallado de actuaciones. Genera archivos CSV individuales.
* **Fase 3 (Consolidación Documental):** Descarga todos los documentos principales y adjuntos vinculados a los movimientos extraídos, procediendo a fusionarlos cronológicamente en un único archivo PDF por expediente.

## 4. Operaciones Específicas e Individuales
* **Actualización de Expediente Único:** Seleccione un expediente desde el menú desplegable para actualizar su historial y consolidar sus documentos de manera urgente (ejecuta las Fases 2 y 3 para ese elemento).
* **Búsqueda Avanzada:** Permite localizar expedientes fuera de la bandeja privada mediante parámetros de filtrado rigurosos (Número, Año, Localidad, Dependencia, DNI, etc.).
* **Descarga Pública de Expedientes:** A partir de los resultados de una Búsqueda Avanzada, permite extraer movimientos y descargar documentos bajo el nivel de acceso público.
* **Extracción Pública Masiva:** Ejecuta una consulta iterativa estructurada a lo largo de todas las dependencias y localidades para extraer el directorio completo de expedientes públicos.

## 5. Gestión y Descarga de Archivos
Todos los archivos generados quedan a su disposición para descarga directa desde la sección inferior del Panel de Control:
* **Archivos PDF:** Documentos unificados listos para impresión o revisión.
* **Archivos de Movimientos y Búsquedas (CSV):** Historiales detallados y resultados tabulados.

