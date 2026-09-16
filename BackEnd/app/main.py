import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

# Importacion de routers de todos los modulos
from app.modules.auth.router import router as auth_router
from app.modules.usuarios.router import router as usuarios_router
from app.modules.empresas.router import router as empresas_router
from app.modules.modalidades.router import router as modalidades_router
from app.modules.programas_fichas.router import router as programas_fichas_router
from app.modules.procesos.router import router as procesos_router
from app.modules.charlas.router import router as charlas_router
from app.modules.seguimientos.router import router as seguimientos_router
from app.modules.bitacoras.router import router as bitacoras_router
from app.modules.notificaciones.router import router as notificaciones_router
from app.modules.dashboards.router import router as dashboards_router
from app.modules.reportes.router import router as reportes_router
from app.modules.importacion.router import router as importacion_router
from app.modules.busqueda.router import router as busqueda_router
from app.modules.auditoria.router import router as auditoria_router


@asynccontextmanager
async def lifespan(app: FastAPI):  
    """
    Contexto de vida de la aplicacion.
    """
    yield


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de Vigilancia y Seguimiento de Etapa Productiva",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Registro global de rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS con lista blanca desde configuracion
allow_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    """
    Middleware para agregar cabeceras basicas de seguridad.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Registro de routers
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(empresas_router)
app.include_router(modalidades_router)
app.include_router(programas_fichas_router)
app.include_router(procesos_router)
app.include_router(charlas_router)
app.include_router(seguimientos_router)
app.include_router(bitacoras_router)
app.include_router(notificaciones_router)
app.include_router(dashboards_router)
app.include_router(reportes_router)
app.include_router(importacion_router)
app.include_router(busqueda_router)
app.include_router(auditoria_router)


@app.get("/health", tags=["health"])
def health_check():
    """
    Endpoint de salud para verificar que la aplicacion esta corriendo.
    """
    return {"status": "ok", "message": f"{settings.APP_NAME} running"}


@app.get("/", tags=["root"])
def root():
    """
    Endpoint raiz informativo.
    """
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }