import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import engine, Base
from app.seed import seed_database
from app.logging_config import logger
from app.routes import health, medicines, batches, stock, reports, dashboard

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if not exist and seed synthetic data
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        seed_database()
    except Exception as e:
        logger.error(f"Error during startup database initialization: {e}")
    yield
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Domain-Specific Inventory, Batch Rules & Auditable Movements API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()

    # Log incoming request
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # Log completed request
        logger.info(
            f"Completed request: {request.method} {request.url.path} "
            f"Status: {response.status_code} in {duration_ms}ms",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            f"Unhandled server error on {request.method} {request.url.path}: {exc}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )


# Include Routers
app.include_router(health.router)
app.include_router(medicines.router)
app.include_router(batches.router)
app.include_router(stock.router)
app.include_router(reports.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "dashboard": "/dashboard",
        "documentation": "/docs",
        "health_check": "/health",
        "readiness_check": "/ready",
    }
