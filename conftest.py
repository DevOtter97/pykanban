import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

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
def registered_user(client):
    resp = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "secret123",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def auth_header(client, registered_user):
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "secret123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def project(client, auth_header):
    resp = client.post("/projects/", json={"title": "Test Project"}, headers=auth_header)
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
def task(client, auth_header, column):
    resp = client.post("/tasks/", json={
        "title": "Test Task",
        "column_id": column["id"],
    }, headers=auth_header)
    assert resp.status_code == 201
    return resp.json()
