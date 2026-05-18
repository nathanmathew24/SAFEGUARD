import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.dependencies.auth import get_current_user
from app.routers import auth, clients, financial, health, library, monitoring, projects, workspace
from app.routers import settings_router, telegram

logger = structlog.get_logger()

app = FastAPI(
    title="Funoon CRM",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes
app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Protected routes — all require a valid JWT cookie
_auth = [Depends(get_current_user)]

app.include_router(clients.router,    prefix="/api/clients",    tags=["clients"],    dependencies=_auth)
app.include_router(projects.router,   prefix="/api/projects",   tags=["projects"],   dependencies=_auth)
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"], dependencies=_auth)
app.include_router(financial.router,  prefix="/api/financial",  tags=["financial"],  dependencies=_auth)
app.include_router(library.router,    prefix="/api/library",    tags=["library"],    dependencies=_auth)
app.include_router(workspace.router,      prefix="/api/workspace",  tags=["workspace"],  dependencies=_auth)
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"],  dependencies=_auth)
# Telegram webhook is public (Telegram calls it, not the browser)
app.include_router(telegram.router, prefix="/telegram", tags=["telegram"])


@app.on_event("startup")
async def startup():
    from app.database import create_tables
    await create_tables()
    logger.info("funoon_crm_started", environment=settings.environment)
