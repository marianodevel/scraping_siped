# Referencia de la API Interna (Core)

Esta sección expone los contratos, parámetros y retornos de los módulos fundamentales del sistema SIPED. La documentación se extrae directamente del código fuente para garantizar su fidelidad funcional.

## Extracción y Análisis Lógico

### Tareas de Scraping (`scraper_tasks`)
Módulo encargado de la orquestación de las peticiones de red y la extracción de datos.
::: scraper_tasks

### Parsers Lógicos (`parsers`)
Módulo de análisis léxico (HTML) y expresiones regulares.
::: parsers

## Gestión de Datos y Estado

### Administrador de Base de Datos (`db_manager`)
Persistencia y consulta de expedientes y movimientos utilizando SQLAlchemy.
::: db_manager

### Gestor de Sesiones (`session_manager`)
Manejo de autenticación, cookies y ciclo de vida de peticiones HTTP.
::: session_manager

### Gestor de Almacenamiento (`gestor_almacenamiento`)
Lectura y validación del sistema de archivos físicos (PDFs, CSVs).
::: gestor_almacenamiento

## Utilidades

### Herramientas Transversales (`utils`)
Funciones auxiliares para manipulación de cadenas, directorios y unificación de archivos.
::: utils
