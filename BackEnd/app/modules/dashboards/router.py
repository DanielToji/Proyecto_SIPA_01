from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.core.constants import Roles
from app.models import Usuario
from app.modules.dashboards import crud, schemas

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("/admin", response_model=schemas.DashboardAdmin)
def dashboard_admin(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN))
):
    """Dashboard del administrador con métricas globales ampliadas."""
    return crud.get_dashboard_admin(db)


@router.get("/coordinador", response_model=schemas.DashboardCoordinador)
def dashboard_coordinador(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.COORDINADOR))
):
    """Dashboard del coordinador con seguimiento operativo y alertas."""
    return crud.get_dashboard_coordinador(db)


@router.get("/instructor", response_model=schemas.DashboardInstructor)
def dashboard_instructor(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.INSTRUCTOR))
):
    """Dashboard del instructor con sus asignaciones, pendientes y grilla de seguimientos."""
    return crud.get_dashboard_instructor(db, current_user.id)

# ================== Dashboard Instructor ==================
@router.get("/instructor", response_model=schemas.DashboardInstructor)
def dashboard_instructor(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.INSTRUCTOR))
):
    """
    Dashboard del instructor con métricas de sus aprendices asignados.
    """
    return crud.get_dashboard_instructor(db, current_user.id)