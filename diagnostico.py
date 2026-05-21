"""Script de diagnóstico para verificar el estado de expedientes y movimientos en la base de datos."""

import os

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///datos_usuarios/siped.db"

import db_manager


def ejecutar_diagnostico(usuario: str, nro_expediente: str) -> None:
    """
    Verifica la integridad de los datos de un expediente en la base local.

    Args:
        usuario: Identificador del usuario propietario.
        nro_expediente: Número de expediente a auditar.
    """
    expedientes = db_manager.obtener_expedientes(usuario, origen="PRIVADO")
    exp = next((e for e in expedientes if e["expediente"] == nro_expediente), None)

    if exp:
        movs = db_manager.obtener_movimientos(exp["id"])
        print(f"Total movimientos en BD para {nro_expediente}: {len(movs)}")
        print("--- ÚLTIMOS 5 MOVIMIENTOS ---")

        for m in movs[-5:]:
            tiene_link = bool(m.get("link_escrito"))
            nombre_corto = str(m.get("nombre_escrito", ""))[:30]
            print(
                f"Fecha: {m.get('fecha_presentacion')} | Link PDF: {tiene_link} | Archivo: {nombre_corto}"
            )
    else:
        print("Expediente no encontrado en la base de datos.")


if __name__ == "__main__":
    # Variables de prueba configurables localmente
    USUARIO_PRUEBA = "SU_USUARIO_AQUI"
    EXPEDIENTE_PRUEBA = "NRO_DEL_EXPEDIENTE_AQUI"

    ejecutar_diagnostico(USUARIO_PRUEBA, EXPEDIENTE_PRUEBA)

