class TestCreateProject:
    def test_create(self, client, auth_header):
        resp = client.post("/projects/", json={
            "title": "My Project",
            "description": "desc",
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Project"
        assert data["description"] == "desc"

    def test_create_unauthenticated(self, client):
        resp = client.post("/projects/", json={"title": "X"})
        assert resp.status_code == 401


class TestListProjects:
    def test_list_empty(self, client, auth_header):
        resp = client.get("/projects/", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_own(self, client, auth_header, project):
        resp = client.get("/projects/", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["id"] == project["id"]


class TestUpdateProject:
    def test_update(self, client, auth_header, project):
        resp = client.patch(f"/projects/{project['id']}", json={
            "title": "Updated",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    def test_update_not_found(self, client, auth_header):
        resp = client.patch("/projects/999", json={"title": "X"}, headers=auth_header)
        assert resp.status_code == 404


class TestDeleteProject:
    def test_delete(self, client, auth_header, project):
        resp = client.delete(f"/projects/{project['id']}", headers=auth_header)
        assert resp.status_code == 204

        resp = client.get("/projects/", headers=auth_header)
        assert resp.json() == []

    def test_delete_not_found(self, client, auth_header):
        resp = client.delete("/projects/999", headers=auth_header)
        assert resp.status_code == 404
