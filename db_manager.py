"""Módulo para la gestión de la base de datos y persistencia de expedientes."""

import os
from typing import Any, Dict, List

import sqlalchemy.exc
from flask import Flask

from extensions import db
from models import Expediente, Movimiento

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:////app/datos_usuarios/siped.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"timeout": 30}}

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
    except sqlalchemy.exc.OperationalError:
        pass


def upsert_expedientes(
    username: str, lista_datos: List[Dict[str, Any]], origen: str = "PRIVADO"
) -> None:
    """
    Inserta o actualiza una lista de expedientes asociados a un usuario.

    Args:
        username: Identificador del usuario propietario de los datos.
        lista_datos: Lista de diccionarios con la información de cada expediente.
        origen: Clasificador del origen de los datos (e.g., PRIVADO, PUBLICO, BUSQUEDA_AVANZADA).
    """
    with app.app_context():
        for data in lista_datos:
            nro_exp = data.get("expediente")
            if not nro_exp:
                continue

            exp = Expediente.query.filter_by(
                usuario_asignado=username, numero_expediente=nro_exp, origen=origen
            ).first()
            if not exp:
                exp = Expediente(
                    usuario_asignado=username,
                    numero_expediente=nro_exp,
                    caratula=data.get("caratula", ""),
                    partes=data.get("partes", "") or data.get("partes_count", ""),
                    estado=data.get("estado", ""),
                    fec_ult_mov=data.get("fec_ult_mov", "")
                    or data.get("fecha_alta", ""),
                    localidad=data.get("localidad", ""),
                    dependencia=data.get("dependencia", ""),
                    secretaria=data.get("secretaria", ""),
                    link_detalle=data.get("link_detalle", ""),
                    origen=origen,
                )
                db.session.add(exp)
            else:
                exp.caratula = data.get("caratula", exp.caratula)
                exp.estado = data.get("estado", exp.estado)
                exp.fec_ult_mov = data.get("fec_ult_mov", exp.fec_ult_mov) or data.get(
                    "fecha_alta", exp.fec_ult_mov
                )
                exp.link_detalle = data.get("link_detalle", exp.link_detalle)
        db.session.commit()


def obtener_expedientes(username: str, origen: str = "PRIVADO") -> List[Dict[str, Any]]:
    """
    Recupera los expedientes almacenados de un usuario específico.

    Args:
        username: Identificador del usuario.
        origen: Clasificador del origen de los datos a filtrar.

    Returns:
        Lista de diccionarios con los metadatos básicos de los expedientes.
    """
    with app.app_context():
        expedientes = Expediente.query.filter_by(
            usuario_asignado=username, origen=origen
        ).all()
        return [
            {
                "id": e.id,
                "expediente": e.numero_expediente,
                "caratula": e.caratula,
                "link_detalle": e.link_detalle,
            }
            for e in expedientes
        ]


def upsert_movimientos(
    expediente_id: int, lista_movimientos: List[Dict[str, Any]]
) -> None:
    """
    Sincroniza el historial de movimientos reemplazando los registros anteriores del expediente.

    Args:
        expediente_id: ID interno (clave primaria) del expediente en la tabla padre.
        lista_movimientos: Lista de diccionarios representando los movimientos actuales.
    """
    with app.app_context():
        if not lista_movimientos:
            return

        Movimiento.query.filter_by(expediente_id=expediente_id).delete()

        for data in lista_movimientos:
            mov = Movimiento(
                expediente_id=expediente_id,
                fecha_presentacion=data.get("fecha_presentacion", ""),
                nombre_escrito=data.get("nombre_escrito", ""),
                tipo=data.get("tipo", ""),
                estado=data.get("estado", ""),
                generado_por=data.get("generado_por", ""),
                descripcion=data.get("descripcion", ""),
                fecha_firma=data.get("fecha_firma", ""),
                fecha_publicacion=data.get("fecha_publicacion", ""),
                link_escrito=data.get("link_escrito", ""),
            )
            db.session.add(mov)

        db.session.commit()


def obtener_movimientos(expediente_id: int) -> List[Dict[str, Any]]:
    """
    Recupera el historial de movimientos de un expediente.

    Args:
        expediente_id: ID interno del expediente.

    Returns:
        Lista de diccionarios ordenados cronológicamente con la información de los movimientos.
    """
    with app.app_context():
        movs = (
            Movimiento.query.filter_by(expediente_id=expediente_id)
            .order_by(Movimiento.id.asc())
            .all()
        )
        return [
            {
                "fecha_presentacion": m.fecha_presentacion,
                "nombre_escrito": m.nombre_escrito,
                "tipo": m.tipo,
                "estado": m.estado,
                "generado_por": m.generado_por,
                "descripcion": m.descripcion,
                "fecha_firma": m.fecha_firma,
                "fecha_publicacion": m.fecha_publicacion,
                "link_escrito": m.link_escrito,
            }
            for m in movs
        ]

