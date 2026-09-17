from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, require_role, require_aprendiz
from app.core.constants import Roles
from app.models import (
    Usuario, Bitacora, ProcesoEtapaProductiva, Ficha,
    BitacoraEvidencia, EvidenciaArchivo,
)

router = APIRouter(prefix="/bitacoras", tags=["Bitácoras"])


# ============================================================
# HELPER: Serializar bitácora para el frontend
# ============================================================

def _serializar_bitacora(b: Bitacora, db: Session) -> dict:
    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == b.proceso_id
    ).first()

    # Archivos adjuntos
    archivos = []
    relaciones = (
        db.query(BitacoraEvidencia)
        .filter(
            BitacoraEvidencia.bitacora_id == b.id,
            BitacoraEvidencia.is_active == True,
        )
        .all()
    )
    for rel in relaciones:
        archivo = db.query(EvidenciaArchivo).filter(
            EvidenciaArchivo.id == rel.evidencia_archivo_id
        ).first()
        if archivo:
            archivos.append({
                "id": archivo.id,
                "nombre": archivo.nombre_archivo,
                "ruta_objeto": archivo.ruta_objeto,
                "mime_type": archivo.mime_type,
                "tamano_bytes": archivo.tamano_bytes,
                "tipo": archivo.mime_type or "application/pdf",
            })

    # Bimestre (1, 2, 3) según el mes del periodo_reportado
    periodo = b.periodo_reportado or ""
    try:
        mes = int(periodo.split("-")[1]) if "-" in periodo else 1
    except Exception:
        mes = 1
    bimestre = 1 if mes <= 4 else (2 if mes <= 8 else 3)

    estado_val = b.estado.value if hasattr(b.estado, "value") else str(b.estado)

    return {
        "id": b.id,
        "proceso_id": b.proceso_id,
        "numero_bitacora": b.numero_bitacora,
        "periodo_reportado": b.periodo_reportado,
        "titulo": b.titulo,
        "contenido": b.contenido,
        "estado": estado_val,
        "fecha_envio": b.fecha_envio.isoformat() if b.fecha_envio else None,
        "fecha_revision": b.fecha_revision.isoformat() if b.fecha_revision else None,
        "instructor_retroalimentacion": b.instructor_retroalimentacion,
        "archivo_f147_url": b.archivo_f147_url,
        "bimestre": bimestre,
        "archivos": archivos,
        "aprendiz_id": proceso.aprendiz_id if proceso else None,
        "aprendiz_nombre": proceso.aprendiz_nombre if proceso else None,
        "aprendiz_email": proceso.aprendiz_email if proceso else None,
        "aprendiz_documento": proceso.aprendiz_documento if proceso else None,
        "ficha_id": proceso.ficha_id if proceso else None,
        "ficha_numero": proceso.ficha_numero if proceso else None,
        "is_active": b.is_active,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
    }


# ============================================================
# LISTADO CON FILTROS
# ============================================================

@router.get("/")
def get_bitacoras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    proceso_id: Optional[int] = None,
    ficha_id: Optional[int] = None,
    aprendiz_id: Optional[int] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(Bitacora).filter(Bitacora.is_active == True)

    if current_user.rol_id == Roles.APRENDIZ:
        procesos = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.aprendiz_id == current_user.id,
            ProcesoEtapaProductiva.is_active == True,
        ).all()
        proceso_ids = [p.id for p in procesos]
        query = query.filter(Bitacora.proceso_id.in_(proceso_ids))

    if proceso_id:
        query = query.filter(Bitacora.proceso_id == proceso_id)

    if ficha_id or aprendiz_id:
        procs_q = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.is_active == True
        )
        if ficha_id:
            procs_q = procs_q.filter(ProcesoEtapaProductiva.ficha_id == ficha_id)
        if aprendiz_id:
            procs_q = procs_q.filter(ProcesoEtapaProductiva.aprendiz_id == aprendiz_id)
        proc_ids = [p.id for p in procs_q.all()]
        query = query.filter(Bitacora.proceso_id.in_(proc_ids))

    if estado:
        query = query.filter(Bitacora.estado == estado)

    bitacoras = query.order_by(Bitacora.created_at.desc()).offset(skip).limit(limit).all()
    return [_serializar_bitacora(b, db) for b in bitacoras]


# ============================================================
# BITÁCORAS POR FICHA (agrupadas por aprendiz)
# ============================================================

@router.get("/ficha/{ficha_id}")
def get_bitacoras_by_ficha(
    ficha_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve las bitácoras agrupadas por aprendiz para una ficha."""
    ficha = db.query(Ficha).filter(Ficha.id == ficha_id).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")

    # Programa
    from app.models import ProgramaFormacion
    programa = db.query(ProgramaFormacion).filter(
        ProgramaFormacion.id == ficha.programa_id
    ).first()

    procesos = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.ficha_id == ficha_id,
        ProcesoEtapaProductiva.is_active == True,
    ).all()

    aprendices_data = []
    for p in procesos:
        bitacoras = (
            db.query(Bitacora)
            .filter(Bitacora.proceso_id == p.id, Bitacora.is_active == True)
            .order_by(Bitacora.numero_bitacora.asc())
            .all()
        )

        aprendices_data.append({
            "aprendiz_id": p.aprendiz_id,
            "proceso_id": p.id,
            "nombre": p.aprendiz_nombre or "Sin nombre",
            "email": p.aprendiz_email or "—",
            "documento": p.aprendiz_documento or "—",
            "bitacoras": [_serializar_bitacora(b, db) for b in bitacoras],
            "total_bitacoras": len(bitacoras),
        })

    return {
        "ficha_id": ficha.id,
        "numero_ficha": ficha.numero_ficha,
        "programa": programa.nombre if programa else "",
        "aprendices": aprendices_data,
    }


# ============================================================
# BITÁCORAS POR APRENDIZ
# ============================================================

@router.get("/aprendiz/{aprendiz_id}")
def get_bitacoras_by_aprendiz(
    aprendiz_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    procesos = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.aprendiz_id == aprendiz_id,
        ProcesoEtapaProductiva.is_active == True,
    ).all()

    proceso_ids = [p.id for p in procesos]
    if not proceso_ids:
        return []

    bitacoras = (
        db.query(Bitacora)
        .filter(Bitacora.proceso_id.in_(proceso_ids), Bitacora.is_active == True)
        .order_by(Bitacora.numero_bitacora.asc())
        .all()
    )

    return [_serializar_bitacora(b, db) for b in bitacoras]


# ============================================================
# DETALLE
# ============================================================

@router.get("/{bitacora_id}")
def get_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    bitacora = db.query(Bitacora).filter(Bitacora.id == bitacora_id).first()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    return _serializar_bitacora(bitacora, db)


# ============================================================
# EVIDENCIAS
# ============================================================

@router.get("/{bitacora_id}/evidencias")
def get_evidencias_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    bitacora = db.query(Bitacora).filter(Bitacora.id == bitacora_id).first()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    relaciones = (
        db.query(BitacoraEvidencia)
        .filter(
            BitacoraEvidencia.bitacora_id == bitacora_id,
            BitacoraEvidencia.is_active == True,
        )
        .all()
    )

    resultado = []
    for rel in relaciones:
        archivo = db.query(EvidenciaArchivo).filter(
            EvidenciaArchivo.id == rel.evidencia_archivo_id
        ).first()
        if archivo:
            resultado.append({
                "id": archivo.id,
                "nombre": archivo.nombre_archivo,
                "ruta_objeto": archivo.ruta_objeto,
                "tipo_documento": archivo.tipo_documento,
                "mime_type": archivo.mime_type,
                "tamano_bytes": archivo.tamano_bytes,
            })
    return resultado


# ============================================================
# CRUD
# ============================================================

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_bitacora(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.aprendiz_id == current_user.id,
        ProcesoEtapaProductiva.estado == "ACTIVO",
    ).first()
    if not proceso:
        raise HTTPException(status_code=400, detail="No tienes un proceso activo")

    bitacora = Bitacora(
        proceso_id=proceso.id,
        numero_bitacora=1,
        periodo_reportado="2024-01",
        titulo="Bitácora de prueba",
        contenido="Contenido de prueba",
        estado="BORRADOR",
    )
    db.add(bitacora)
    db.commit()
    db.refresh(bitacora)
    return bitacora


@router.put("/{bitacora_id}")
def update_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
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
    current_user: Usuario = Depends(require_aprendiz),
):
    bitacora = db.query(Bitacora).filter(Bitacora.id == bitacora_id).first()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    bitacora.is_active = False
    db.commit()
    return {"message": "Bitácora eliminada exitosamente"}