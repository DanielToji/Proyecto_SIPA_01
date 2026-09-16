"""
Módulo de Bitácoras
- Gestión de bitácoras por proceso
- Estados: BORRADOR, ENVIADA, APROBADA, CON_OBSERVACIONES
- Retroalimentación de instructores
"""

from app.modules.bitacoras.router import router

__all__ = ["router"]