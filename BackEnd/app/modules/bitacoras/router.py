from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, require_aprendiz
from app.models import Usuario, Bitacora, ProcesoEtapaProductiva

router = APIRouter(prefix="/bitacoras", tags=["Bitácoras"])


# ============================================================
# ENDPOINTS BÁSICOS DE BITÁCORAS
# ============================================================

@router.get("/")
def get_bitacoras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene lista de bitácoras (versión simple)"""
    query = db.query(Bitacora).filter(Bitacora.is_active == True)
    
    # Si es aprendiz, solo ver sus bitácoras
    if current_user.rol_id == 4:  # Aprendiz
        procesos = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.aprendiz_id == current_user.id
        ).all()
        proceso_ids = [p.id for p in procesos]
        query = query.filter(Bitacora.proceso_id.in_(proceso_ids))
    
    bitacoras = query.offset(skip).limit(limit).order_by(
        Bitacora.created_at.desc()
    ).all()
    
    return bitacoras


@router.get("/{bitacora_id}")
def get_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una bitácora por su ID"""
    bitacora = db.query(Bitacora).filter(Bitacora.id == bitacora_id).first()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    return bitacora


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_bitacora(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz)
):
    """Crea una bitácora de prueba"""
    # Buscar un proceso activo del aprendiz
    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.aprendiz_id == current_user.id,
        ProcesoEtapaProductiva.estado == "ACTIVO"
    ).first()
    
    if not proceso:
        # Crear un proceso de prueba si no existe
        from datetime import date
        proceso = ProcesoEtapaProductiva(
            aprendiz_id=current_user.id,
            ficha_id=1,
            modalidad_id=1,
            instructor_id=1,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            estado="ACTIVO"
        )
        db.add(proceso)
        db.commit()
        db.refresh(proceso)
    
    # Crear bitácora de prueba
    bitacora = Bitacora(
        proceso_id=proceso.id,
        numero_bitacora=1,
        periodo_reportado="2024-01",
        titulo="Bitácora de prueba",
        contenido="Contenido de prueba para la bitácora",
        estado="BORRADOR"
    )
    
    db.add(bitacora)
    db.commit()
    db.refresh(bitacora)
    
    return bitacora


@router.put("/{bitacora_id}")
def update_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una bitácora (versión simple)"""
    bitacora = db.query(Bitacora).filter(Bitacora.id == bitacora_id).first()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    
    bitacora.titulo = "Bitácora actualizada"
    db.commit()
    db.refresh(bitacora)
    
    return bitacora


@router.delete("/{bitacora_id}")
def delete_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz)
):
    """Elimina una bitácora (soft delete)"""
    bitacora = db.query(Bitacora).filter(Bitacora.id == bitacora_id).first()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    
    bitacora.is_active = False
    db.commit()
    
    return {"message": "Bitácora eliminada exitosamente"}


@router.get("/aprendiz/{aprendiz_id}")
def get_bitacoras_by_aprendiz(
    aprendiz_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene bitácoras de un aprendiz"""
    procesos = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.aprendiz_id == aprendiz_id,
        ProcesoEtapaProductiva.is_active == True
    ).all()
    
    proceso_ids = [p.id for p in procesos]
    
    if not proceso_ids:
        return []
    
    bitacoras = db.query(Bitacora).filter(
        Bitacora.proceso_id.in_(proceso_ids),
        Bitacora.is_active == True
    ).order_by(Bitacora.created_at.desc()).all()
    
    return bitacoras