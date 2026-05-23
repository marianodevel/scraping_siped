import pytest
from models import Expediente, Movimiento
import db_manager

def test_upsert_y_obtener_expedientes(app, db_session):
    with app.app_context():
        # Usamos diccionarios para el upsert
        db_manager.upsert_expedientes([{"expediente": "1/2026", "caratula": "A"}], "USR_TEST")
        exps = db_manager.obtener_expedientes("USR_TEST")
        assert len(exps) >= 1
        # Accedemos como diccionario, ya que db_manager suele retornar dicts
        assert exps[0]["caratula"] == "A"

def test_guardar_y_obtener_movimientos(app, db_session):
    with app.app_context():
        db_manager.upsert_expedientes([{"expediente": "2/2026"}], "USR")
        db_manager.guardar_movimientos("2/2026", [{"fecha": "01", "tramite": "M1"}])
        
        # Obtenemos el expediente para sacar su ID
        exp = Expediente.query.filter_by(numero_expediente="2/2026").first()
        movs = db_manager.obtener_movimientos(exp.id)
        assert len(movs) >= 1
        assert movs[0]["tramite"] == "M1"