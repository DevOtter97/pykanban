import time

import structlog
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from logging_config import setup_logging

setup_logging()
logger = structlog.get_logger()

import migrations
from database import Base, engine
from routers import cards, users, columns, projects, categories, typologies, category_typology

# Run migrations before creating tables (adds missing columns to existing DB)
logger.info("running_database_migrations")
migrations.run(engine)
# Create any new tables defined in models
Base.metadata.create_all(bind=engine)
logger.info("database_ready")

app = FastAPI(title="Kanban API", version="2.0.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(elapsed_ms, 1),
    )
    return response


app.include_router(users.router)
app.include_router(projects.router)
app.include_router(columns.router)
app.include_router(categories.router)
app.include_router(typologies.router)
app.include_router(category_typology.router)
app.include_router(cards.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")

logger.info("api_started", version="2.0.0")
