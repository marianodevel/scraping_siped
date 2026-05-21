"""Modelos de la base de datos para la aplicación SIPED."""

from extensions import db


class Expediente(db.Model):
    """Modelo que representa un expediente judicial en el sistema."""

    __tablename__ = "expedientes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_asignado = db.Column(db.String(50), nullable=False, index=True)
    numero_expediente = db.Column(db.String(50), nullable=False)
    caratula = db.Column(db.String(255), nullable=False)
    partes = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    fec_ult_mov = db.Column(db.String(20), nullable=True)
    localidad = db.Column(db.String(100), nullable=True)
    dependencia = db.Column(db.String(100), nullable=True)
    secretaria = db.Column(db.String(100), nullable=True)
    link_detalle = db.Column(db.String(255), nullable=True)

    origen = db.Column(db.String(50), default="PRIVADO", index=True)
    movimientos = db.relationship(
        "Movimiento", backref="expediente", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Expediente {self.numero_expediente} ({self.usuario_asignado}) - {self.origen}>"


class Movimiento(db.Model):
    """Modelo que representa un movimiento o escrito dentro de un expediente."""

    __tablename__ = "movimientos"

    id = db.Column(db.Integer, primary_key=True)
    expediente_id = db.Column(
        db.Integer, db.ForeignKey("expedientes.id"), nullable=False
    )
    fecha_presentacion = db.Column(db.String(50), nullable=True)
    nombre_escrito = db.Column(db.String(255), nullable=True)
    tipo = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    generado_por = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_firma = db.Column(db.String(50), nullable=True)
    fecha_publicacion = db.Column(db.String(50), nullable=True)
    link_escrito = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Movimiento {self.nombre_escrito} - {self.fecha_presentacion}>"

