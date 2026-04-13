"""
Run lightweight migrations on startup without dropping existing data.
Safe to run multiple times (idempotent).
"""
import structlog
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = structlog.get_logger()


def run(engine: Engine):
    with engine.connect() as conn:
        logger.info("migrations_started")

        # 1. Create projects table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT,
                position    INTEGER DEFAULT 0,
                owner_id    INTEGER NOT NULL REFERENCES users(id),
                created_at  DATETIME DEFAULT (datetime('now'))
            )
        """))

        # 2. Add project_id column to columns table if missing
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(columns)"))]
        if "project_id" not in cols:
            conn.execute(text("ALTER TABLE columns ADD COLUMN project_id INTEGER"))

        # 3. Add due_date and assigned_to columns to tasks table if missing
        task_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(tasks)"))]
        if "due_date" not in task_cols:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN due_date DATETIME"))
        if "assigned_to" not in task_cols:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN assigned_to INTEGER REFERENCES users(id)"))

        conn.commit()
        logger.info("schema_migrations_complete")

        # 4. For each user who has columns without a project, create a default project
        orphan_users = conn.execute(text("""
            SELECT DISTINCT owner_id FROM columns WHERE project_id IS NULL
        """)).fetchall()

        for (user_id,) in orphan_users:
            logger.info("creating_default_project", user_id=user_id, reason="orphan_columns")
            # Create default project for this user
            result = conn.execute(text("""
                INSERT INTO projects (title, description, position, owner_id)
                VALUES ('Mi proyecto', NULL, 0, :uid)
            """), {"uid": user_id})
            project_id = result.lastrowid

            # Assign all their orphan columns to this project
            conn.execute(text("""
                UPDATE columns SET project_id = :pid
                WHERE owner_id = :uid AND project_id IS NULL
            """), {"pid": project_id, "uid": user_id})

        conn.commit()
