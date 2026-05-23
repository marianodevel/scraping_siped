import pytest
from datetime import datetime
import db_manager
from models import Expediente, Movimiento

def test_upsert_expediente_nuevo(app, db_session):
    """Verifica que se inserte un expediente que no existe previamente."""
    with app.app_context():
        expediente_data = {
            "expediente": "1234/2026",
            "caratula": "ACTOR C/ DEMANDADO S/ DAÑOS",
            "dependencia": "JUZGADO CIVIL 1",
            "tipo_juicio": "DAÑOS Y PERJUICIOS",
            "estado": "EN TRAMITE",
            "fecha_inicio": "01/01/2026",
            "usuario_id": "CUIL_123"
        }
        
        resultado = db_manager.upsert_expedientes([expediente_data], "CUIL_123")
        
        assert resultado is True
        
        exp_db = Expediente.query.filter_by(numero_expediente="1234/2026").first()
        assert exp_db is not None
        assert exp_db.caratula == "ACTOR C/ DEMANDADO S/ DAÑOS"
        assert exp_db.usuario_asignado == "CUIL_123"


def test_upsert_expediente_existente_actualiza(app, db_session):
    """Verifica que si un expediente ya existe, actualice sus datos en lugar de duplicar."""
    with app.app_context():
        # Insertar inicial
        exp_inicial = Expediente(
            numero_expediente="9999/2025",
            caratula="VIEJA CARATULA",
            usuario_asignado="CUIL_TEST"
        )
        db_session.add(exp_inicial)
        db_session.commit()
        
        # Nuevos datos para upsert
        exp_nuevo = {
            "expediente": "9999/2025",
            "caratula": "NUEVA CARATULA",
            "estado": "ARCHIVADO"
        }
        
        db_manager.upsert_expedientes([exp_nuevo], "CUIL_TEST")
        
        # Verificar que hay un solo registro con ese numero y se actualizó
        expedientes = Expediente.query.filter_by(numero_expediente="9999/2025").all()
        assert len(expedientes) == 1
        assert expedientes[0].caratula == "NUEVA CARATULA"
        assert expedientes[0].estado == "ARCHIVADO"


def test_guardar_movimientos_elimina_previos(app, db_session):
    """Verifica que al guardar movimientos nuevos, se limpien los anteriores del mismo expediente."""
    with app.app_context():
        # Crear expediente
        exp = Expediente(numero_expediente="111/2026", caratula="TEST MOV", usuario_asignado="CUIL_TEST")
        db_session.add(exp)
        db_session.commit()
        
        # Insertar movimiento viejo directamente
        mov_viejo = Movimiento(
            expediente_id=exp.id,
            fecha="01/01/2025",
            tramite="ESCRITO VIEJO",
            tipo="TIPO",
            estado="PROVEIDO",
            dependencia="JUZGADO"
        )
        db_session.add(mov_viejo)
        db_session.commit()
        
        # Guardar nuevos movimientos via manager
        nuevos_movimientos = [
            {
                "fecha": "02/02/2026",
                "tramite": "NUEVO ESCRITO",
                "tipo": "TIPO 2",
                "estado": "A DESPACHO",
                "dependencia": "JUZGADO 2"
            }
        ]
        
        db_manager.guardar_movimientos("111/2026", nuevos_movimientos)
        
        # Verificar
        movs_en_db = Movimiento.query.filter_by(expediente_id=exp.id).all()
        assert len(movs_en_db) == 1
        assert movs_en_db[0].tramite == "NUEVO ESCRITO"


def test_guardar_movimientos_expediente_inexistente(app, db_session):
    """Verifica el comportamiento cuando se intentan guardar movimientos de un exp no registrado."""
    with app.app_context():
        movs = [{"fecha": "01/01/2026", "tramite": "TEST"}]
        # No debe crashear, debe manejar el caso de expediente no encontrado
        resultado = db_manager.guardar_movimientos("EXP_FANTASMA", movs)
        
        # Asumiendo que la funcion retorna False o None al fallar silenciosamente
        # o maneja la excepcion devolviendo False
        assert resultado is False or resultado is None
