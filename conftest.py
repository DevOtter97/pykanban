import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from repositories.sqlalchemy.db_models import UserRow

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client, db):
    resp = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "secret123",
    })
    assert resp.status_code == 201
    # Promote to superadmin so test user can create teams/projects
    user = db.query(UserRow).filter(UserRow.username == "testuser").first()
    user.role = "superadmin"
    db.commit()
    data = resp.json()
    data["role"] = "superadmin"
    return data


@pytest.fixture()
def auth_header(client, registered_user):
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "secret123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def team(client, auth_header):
    resp = client.post("/teams/", json={
        "name": "Test Team",
        "description": "A test team",
    }, headers=auth_header)
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def project(client, auth_header, team):
    resp = client.post("/projects/", json={
        "title": "Test Project",
        "team_id": team["id"],
    }, headers=auth_header)
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def column(client, auth_header, project):
    resp = client.post("/columns/", json={
        "title": "Test Column",
        "project_id": project["id"],
    }, headers=auth_header)
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def category(client, auth_header):
    resp = client.post("/categories/", json={
        "name": "Bug",
        "description": "Bug report",
    }, headers=auth_header)
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def typology(client, auth_header):
    resp = client.post("/typologies/", json={
        "name": "Desarrollo",
        "description": "Development work",
    }, headers=auth_header)
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def enabled_combo(client, auth_header, category, typology):
    resp = client.put("/category-typology/", json={
        "category_id": category["id"],
        "typology_id": typology["id"],
        "enabled": True,
    }, headers=auth_header)
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture()
def card(client, auth_header, column):
    resp = client.post("/cards/", json={
        "title": "Test Card",
        "column_id": column["id"],
    }, headers=auth_header)
    assert resp.status_code == 201
    return resp.json()


# ── Helper fixtures for second user (member role) ───────────────────────────

@pytest.fixture()
def member_user(client, db):
    resp = client.post("/auth/register", json={
        "email": "member@example.com",
        "username": "memberuser",
        "password": "secret123",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def member_header(client, member_user):
    resp = client.post("/auth/login", data={
        "username": "memberuser",
        "password": "secret123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
