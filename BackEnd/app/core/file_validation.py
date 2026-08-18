import os
from pathlib import Path
from typing import Optional, Set

from fastapi import HTTPException, UploadFile

# Tamaño máximo por defecto: 5 MB
DEFAULT_MAX_SIZE_MB = 5

# Tipos MIME permitidos por categoría
ALLOWED_IMAGE_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_DOC_TYPES: Set[str] = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/zip",
}

# Extensiones permitidas por categoría
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_DOC_EXTENSIONS: Set[str] = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".zip"}


def _validate_filename(filename: Optional[str]) -> str:
    """
    Valida que el nombre del archivo sea seguro y no contenga rutas.
    Retorna el nombre base limpio.
    """
    if not filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo no proporcionado")

    # Eliminar posibles rutas y obtener solo el nombre base
    base_name = Path(filename).name

    # Rechazar si el nombre contiene caracteres peligrosos o está vacío
    if not base_name or base_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    # Prevenir caracteres no deseados (tolerancia básica)
    forbidden_chars = set('<>:"/\\|?*')
    if any(c in forbidden_chars for c in base_name):
        raise HTTPException(status_code=400, detail="El nombre del archivo contiene caracteres no permitidos")

    return base_name


def validate_upload_file(
    file: UploadFile,
    max_size_mb: int = DEFAULT_MAX_SIZE_MB,
    allowed_mime_types: Optional[Set[str]] = None,
    allowed_extensions: Optional[Set[str]] = None,
) -> None:
    """
    Valida un archivo subido:
    - Nombre de archivo seguro
    - Tipo MIME permitido (si se especifica)
    - Extensión permitida (si se especifica)
    - No vacío
    - Tamaño máximo

    Lanza HTTPException 400 si no cumple.
    """
    # 1. Validar nombre
    safe_filename = _validate_filename(file.filename)

    # 2. Validar tipo MIME
    if not file.content_type:
        raise HTTPException(status_code=400, detail="No se pudo determinar el tipo de archivo")

    if allowed_mime_types and file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tipo de archivo no permitido: {file.content_type}. "
                f"Permitidos: {', '.join(sorted(allowed_mime_types))}"
            ),
        )

    # 3. Validar extensión
    extension = os.path.splitext(safe_filename)[1].lower()
    if allowed_extensions and extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Extensión de archivo no permitida: {extension}. "
                f"Permitidas: {', '.join(sorted(allowed_extensions))}"
            ),
        )

    # 4. Leer tamaño desde el final
    try:
        file.file.seek(0, 2)  # ir al final
        size_bytes = file.file.tell()
        file.file.seek(0)     # volver al inicio
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo leer el archivo")

    if size_bytes == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    max_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el tamaño máximo permitido de {max_size_mb} MB",
        )