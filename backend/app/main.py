import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import check_db
from app.routers import salons, search

settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup check
    if not check_db():
        raise RuntimeError("Cannot connect to database on startup")
    yield


app = FastAPI(
    title="Lookla API",
    description="Beauty marketplace Greece — lookla.gr",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS — allow frontend + mobile
origins = [o.strip() for o in settings.allowed_origins.split(",")]
if settings.environment == "development":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(salons.router, prefix="/api")
app.include_router(search.router, prefix="/api")


@app.get("/api/health")
def health():
    db_ok = check_db()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "version": "0.1.0",
    }
