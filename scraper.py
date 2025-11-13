# scraper.py
from fases.fase_1 import ejecutar_fase_1_lista
from fases.fase_2 import ejecutar_fase_2_movimientos
from fases.fase_3 import ejecutar_fase_3_documentos

# Este archivo ahora solo sirve como el punto de importación para Celery/Flask
# y re-exporta las funciones modulares.
