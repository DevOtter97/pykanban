class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "pass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data

    def test_register_duplicate_email(self, client, registered_user):
        resp = client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "other",
            "password": "pass123",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_register_duplicate_username(self, client, registered_user):
        resp = client.post("/auth/register", json={
            "email": "other@example.com",
            "username": "testuser",
            "password": "pass123",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Username already taken"


class TestLogin:
    def test_login_success(self, client, registered_user):
        resp = client.post("/auth/login", data={
            "username": "testuser",
            "password": "secret123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post("/auth/login", data={
            "username": "testuser",
            "password": "wrong",
        })
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post("/auth/login", data={
            "username": "noexiste",
            "password": "pass",
        })
        assert resp.status_code == 401


class TestMe:
    def test_get_me(self, client, auth_header, registered_user):
        resp = client.get("/auth/me", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401
