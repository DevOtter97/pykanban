from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import migrations
from database import Base, engine
from routers import tasks, users, columns, projects

# Run migrations before creating tables (adds missing columns to existing DB)
migrations.run(engine)
# Create any new tables defined in models
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban API", version="2.0.0")

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(columns.router)
app.include_router(tasks.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")
