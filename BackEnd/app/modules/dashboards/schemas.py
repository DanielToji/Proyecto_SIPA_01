from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class ProcesoRiesgo(BaseModel):
    proceso_id: int
    aprendiz_id: int
    nombre_aprendiz: Optional[str] = None
    ficha_id: int
    numero_ficha: Optional[str] = None
    fecha_fin: date
    dias_restantes: int
    estado_riesgo: str  # NORMAL, ATENCION, CRITICO, VENCIDO


class DocumentoPendiente(BaseModel):
    proceso_id: int
    tipo_documento: str
    estado: str


class SeguimientoGrilla(BaseModel):
    proceso_id: int
    momento: str
    estado: str  # REALIZADO, PENDIENTE, NO_PROGRAMADO
    fecha_programada: Optional[date] = None
    fecha_realizada: Optional[date] = None


class CumplimientoPrograma(BaseModel):
    programa_id: int
    programa_nombre: str
    total_procesos: int
    completados: int
    porcentaje: float


class CumplimientoInstructor(BaseModel):
    instructor_id: int
    instructor_nombre: str
    total_procesos: int
    completados: int
    porcentaje: float


class DashboardAdmin(BaseModel):
    total_usuarios_activos: int
    total_aprendices_etapa_productiva: int
    total_instructores: int
    total_fichas: int
    total_procesos_activos: int
    total_procesos_finalizados: int
    aprendices_pendientes_iniciar: int
    aprendices_sin_alternativa: int
    seguimientos_pendientes: int
    procesos_en_riesgo: List[ProcesoRiesgo]
    documentos_pendientes: int
    total_novedades: int
    cumplimiento_por_programa: List[CumplimientoPrograma]


class DashboardCoordinador(BaseModel):
    total_fichas_asignadas: int
    total_instructores_activos: int
    total_procesos_activos: int
    total_procesos_pendientes: int
    alertas_criticas: int
    aprendices_pendientes_iniciar: int
    aprendices_sin_alternativa: int
    seguimientos_pendientes: int
    procesos_en_riesgo: List[ProcesoRiesgo]
    documentos_pendientes: int
    medidas_formativas_pendientes: int


class DashboardInstructor(BaseModel):
    total_fichas_asignadas: int
    total_aprendices_cargo: int
    total_bitacoras_pendientes: int
    proximas_reuniones: int
    procesos_en_riesgo: List[ProcesoRiesgo]
    grilla_seguimientos: List[SeguimientoGrilla]
    documentos_pendientes: int
    seguimientos_pendientes: int
    medidas_formativas_pendientes: int
    
# ================== Dashboard Instructor ==================
class DashboardInstructor(BaseModel):
    total_aprendices: int
    bitacoras_pendientes: int
    reuniones_proximas: int
    instructor_id: int
    instructor_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True