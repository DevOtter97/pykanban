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

        # ── Existing migrations ──────────────────────────────────────────

        # 1. Create projects table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT,
                position    INTEGER DEFAULT 0,
                owner_id    INTEGER REFERENCES users(id),
                created_at  DATETIME DEFAULT (datetime('now'))
            )
        """))

        # 2. Add project_id column to columns table if missing
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(columns)"))]
        if "project_id" not in cols:
            conn.execute(text("ALTER TABLE columns ADD COLUMN project_id INTEGER"))

        # 3. Rename tasks table to cards if needed
        tables = [row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))]
        if "tasks" in tables and "cards" not in tables:
            conn.execute(text("ALTER TABLE tasks RENAME TO cards"))

        # 4. Add missing columns to cards table
        card_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(cards)"))]
        if "due_date" not in card_cols:
            conn.execute(text("ALTER TABLE cards ADD COLUMN due_date DATETIME"))
        if "assigned_to" not in card_cols:
            conn.execute(text("ALTER TABLE cards ADD COLUMN assigned_to INTEGER REFERENCES users(id)"))
        if "category_id" not in card_cols:
            conn.execute(text("ALTER TABLE cards ADD COLUMN category_id INTEGER REFERENCES categories(id)"))
        if "typology_id" not in card_cols:
            conn.execute(text("ALTER TABLE cards ADD COLUMN typology_id INTEGER REFERENCES typologies(id)"))
        if "content" not in card_cols:
            conn.execute(text("ALTER TABLE cards ADD COLUMN content JSON"))

        conn.commit()
        logger.info("schema_migrations_complete")

        # 5. For each user who has columns without a project, create a default project
        orphan_users = conn.execute(text("""
            SELECT DISTINCT owner_id FROM columns WHERE project_id IS NULL
        """)).fetchall()

        for (user_id,) in orphan_users:
            logger.info("creating_default_project", user_id=user_id, reason="orphan_columns")
            result = conn.execute(text("""
                INSERT INTO projects (title, description, position, owner_id)
                VALUES ('Mi proyecto', NULL, 0, :uid)
            """), {"uid": user_id})
            project_id = result.lastrowid
            conn.execute(text("""
                UPDATE columns SET project_id = :pid
                WHERE owner_id = :uid AND project_id IS NULL
            """), {"pid": project_id, "uid": user_id})

        conn.commit()

        # ── New migrations: roles & teams ────────────────────────────────

        # 6. Create teams table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teams (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL UNIQUE,
                description TEXT,
                created_at  DATETIME DEFAULT (datetime('now'))
            )
        """))

        # 7. Create team_members table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS team_members (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL REFERENCES teams(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                role    TEXT    NOT NULL DEFAULT 'member'
            )
        """))

        # 8. Add role column to users table
        user_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)"))]
        if "role" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"))

        # 9. Add team_id and archived columns to projects table
        proj_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(projects)"))]
        if "team_id" not in proj_cols:
            conn.execute(text("ALTER TABLE projects ADD COLUMN team_id INTEGER REFERENCES teams(id)"))
        if "archived" not in proj_cols:
            conn.execute(text("ALTER TABLE projects ADD COLUMN archived BOOLEAN NOT NULL DEFAULT 0"))

        # 10. Add is_mandatory and is_visible_by_default to columns table
        col_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(columns)"))]
        if "is_mandatory" not in col_cols:
            conn.execute(text("ALTER TABLE columns ADD COLUMN is_mandatory BOOLEAN NOT NULL DEFAULT 0"))
        if "is_visible_by_default" not in col_cols:
            conn.execute(text("ALTER TABLE columns ADD COLUMN is_visible_by_default BOOLEAN NOT NULL DEFAULT 1"))

        # 11. Add completed_at and completion_notes to cards table
        card_cols2 = [row[1] for row in conn.execute(text("PRAGMA table_info(cards)"))]
        if "completed_at" not in card_cols2:
            conn.execute(text("ALTER TABLE cards ADD COLUMN completed_at DATETIME"))
        if "completion_notes" not in card_cols2:
            conn.execute(text("ALTER TABLE cards ADD COLUMN completion_notes TEXT"))

        conn.commit()
        logger.info("roles_teams_migrations_complete")
