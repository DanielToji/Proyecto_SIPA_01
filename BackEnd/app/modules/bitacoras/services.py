import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.file_validation import (
    validate_upload_file,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_DOC_TYPES,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_DOC_EXTENSIONS,
)
from app.models import EvidenciaArchivo


async def guardar_evidencia_archivo(
    db: Session,
    file: UploadFile,
    uploaded_by: Optional[int],
    tipo_documento: Optional[str] = None,
) -> EvidenciaArchivo:
    """
    Valida y guarda un archivo de evidencia en disco local.
    Luego crea el registro metadata en `evidencias_archivos`.
    RF-08: Gestión documental / repositorio de evidencias.
    """
    validate_upload_file(
        file,
        max_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        allowed_mime_types=ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES,
        allowed_extensions=ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOC_EXTENSIONS,
    )

    extension = os.path.splitext(file.filename)[1].lower()
    nombre_unico = f"{uuid.uuid4().hex}{extension}"
    upload_dir = Path(settings.UPLOAD_DIR) / "evidencias"
    upload_dir.mkdir(parents=True, exist_ok=True)
    ruta_absoluta = upload_dir / nombre_unico

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )

    ruta_absoluta.write_bytes(content)

    evidencia = EvidenciaArchivo(
        nombre_archivo=file.filename,
        ruta_objeto=str(ruta_absoluta),
        tipo_documento=tipo_documento,
        mime_type=file.content_type,
        tamano_bytes=len(content),
        uploaded_by=uploaded_by,
        is_active=True,
    )
    db.add(evidencia)
    db.commit()
    db.refresh(evidencia)
    return evidencia