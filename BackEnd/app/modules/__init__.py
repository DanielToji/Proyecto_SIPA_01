"""
Módulos del sistema SIPA
Cada módulo contiene: router, schemas, crud, services
"""

from app.modules import auth
from app.modules import usuarios
from app.modules import bitacoras
from app.modules import empresas
from app.modules import procesos
from app.modules import charlas
from app.modules import modalidades
from app.modules import programas_fichas
from app.modules import seguimientos
from app.modules import notificaciones
from app.modules import dashboards
from app.modules import reportes
from app.modules import importacion
from app.modules import busqueda
from app.modules import auditoria

__all__ = [
    "auth",
    "usuarios",
    "bitacoras",
    "empresas",
    "procesos",
    "charlas",
    "modalidades",
    "programas_fichas",
    "seguimientos",
    "notificaciones",
    "dashboards",
    "reportes",
    "importacion",
    "busqueda",
    "auditoria",
]