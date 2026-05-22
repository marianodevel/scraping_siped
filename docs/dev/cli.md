# Herramientas de Línea de Comandos (CLI)

Los scripts interactivos de consola permiten la ejecución independiente de las fases de extracción sin requerir la instanciación del servidor web o los *workers* de Celery. 

## Fases Principales Interactivos

### Extracción de Lista Maestra
::: script.cli_lista_expedientes

### Sincronización de Movimientos
::: script.cli_movimientos

### Consolidación Documental (Masiva)
::: script.cli_movimientos_pdf

### Actualización de Expediente Único
::: script.cli_un_expediente

## Búsquedas e Indexación

### Búsqueda Pública Masiva
::: script.cli_busqueda_publica

### Actualización de Catálogos
::: script.extract_tipos
