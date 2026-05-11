import os

# Forzamos la ruta local de la base de datos antes de importar db_manager
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///datos_usuarios/siped.db"

import db_manager

usuario = "SU_USUARIO_AQUI"
nro_expediente = "NRO_DEL_EXPEDIENTE_AQUI"

expedientes = db_manager.obtener_expedientes(usuario, origen="PRIVADO")
exp = next((e for e in expedientes if e["expediente"] == nro_expediente), None)

if exp:
    movs = db_manager.obtener_movimientos(exp["id"])
    print(f"Total movimientos en BD para {nro_expediente}: {len(movs)}")
    print("--- ÚLTIMOS 5 MOVIMIENTOS ---")
    for m in movs[-5:]:
        tiene_link = bool(m.get('link_escrito'))
        print(f"Fecha: {m['fecha_presentacion']} | Link PDF: {tiene_link} | Archivo: {m['nombre_escrito'][:30]}")
else:
    print("Expediente no encontrado en la base de datos.")