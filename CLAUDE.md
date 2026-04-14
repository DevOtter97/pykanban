# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run dev server
uvicorn main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_cards.py

# Run a specific test
pytest tests/test_cards.py::test_create_card -v
```

## Architecture

Kanban board REST API built with FastAPI + SQLAlchemy + SQLite (`todo.db`). JWT auth via python-jose + bcrypt. Structured logging via structlog.

Uses a **repository pattern** with clean separation between domain models (Pydantic), data access (repositories), and HTTP layer (routers).

### Domain model hierarchy

User → Project → BoardColumn → Card. Cards also reference Category, Typology, and an assigned User. Categories and Typologies are linked via a many-to-many `CategoryTypology` table that controls which combinations are allowed (validated on card create/update).

### Key modules

- **`models/`** — Pydantic v2 domain models (one module per entity). These are the canonical data shapes used across the app. Enums live in `models/enums.py`, shared validators in `models/validators.py`.
- **`repositories/protocols.py`** — abstract repository interfaces using `typing.Protocol`. Defines the contract for data access without any SQLAlchemy dependency.
- **`repositories/sqlalchemy/`** — concrete repository implementations. `db_models.py` contains all SQLAlchemy ORM models (suffixed `*Row`). Each `*_repo.py` converts between ORM rows and Pydantic models internally. The `__init__.py` exports FastAPI `Depends()` providers (e.g. `get_card_repo`).
- **`auth.py`** — JWT creation/verification, `get_current_user` dependency (returns `UserOut` Pydantic model)
- **`permissions.py`** — centralized permission helpers, receives repositories as arguments (no direct DB access)
- **`database.py`** — engine, `SessionLocal`, `Base`, `get_db` dependency
- **`migrations.py`** — idempotent startup migrations (runs before `create_all` in `main.py`)
- **`routers/`** — one file per resource, each exports a `router`; all endpoints require auth via `Depends(get_current_user)` except register/login. Routers inject repositories via `Depends()` and never touch SQLAlchemy directly.

### Patterns

- **Repository injection**: routers declare repository dependencies via `Depends(get_*_repo)`. The providers in `repositories/sqlalchemy/__init__.py` create repo instances with the current DB session.
- **ORM stays in repos**: SQLAlchemy ORM models (`*Row` classes) are internal to `repositories/sqlalchemy/`. They never leak into routers or permissions. Repos return Pydantic models.
- **Permission checks**: `permissions.py` functions receive `UserOut` + repository instances (not `Session`). Example: `require_project_access(user, project_id, project_repo, team_repo)`.
- Partial updates use `PATCH` with `model_dump(exclude_unset=True)`.
- Category+typology validation: `_assert_category_typology_allowed()` in `routers/cards.py` checks via `CategoryRepository`, `TypologyRepository`, and `CategoryTypologyRepository`.

### Testing

Tests use a separate `test.db` SQLite database. The `conftest.py` provides `autouse` fixture `setup_db` that creates/drops all tables per test. Key fixtures chain: `client` → `auth_header` → `project` → `column` → `card`. Tests hit the API via `TestClient` (not unit-testing models directly). The `get_db` dependency override ensures repos get the test session.
