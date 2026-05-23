import pytest
from flask import Flask

@pytest.fixture
def app():
    """Instancia y configura una aplicación Flask aislada en memoria para testing."""
    app = Flask(__name__)
    
    app.config["TESTING"] = True
    # Usamos una base de datos SQLite efímera en memoria para no tocar los datos reales
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "clave-secreta-testing"
    
    with app.app_context():
        from extensions import db
        db.init_app(app)
        db.create_all()
        
        yield app  # Aquí se ejecutan los tests
        
        # Limpieza de la base de datos después de cada prueba
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Proporciona un cliente HTTP para realizar peticiones web simuladas."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Proporciona acceso directo a la sesión transaccional de la base de datos."""
    from extensions import db
    with app.app_context():
        yield db.session