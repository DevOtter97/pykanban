class TestListColumns:
    def test_list_creates_defaults(self, client, auth_header, project):
        resp = client.get(f"/columns/?project_id={project['id']}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["title"] == "Pendiente"
        assert data[1]["title"] == "En progreso"
        assert data[2]["title"] == "Hecho"

    def test_list_not_own_project(self, client, auth_header):
        resp = client.get("/columns/?project_id=999", headers=auth_header)
        assert resp.status_code == 404


class TestCreateColumn:
    def test_create(self, client, auth_header, project):
        resp = client.post("/columns/", json={
            "title": "Custom",
            "project_id": project["id"],
            "color": "#ff0000",
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Custom"
        assert data["color"] == "#ff0000"

    def test_create_invalid_project(self, client, auth_header):
        resp = client.post("/columns/", json={
            "title": "X",
            "project_id": 999,
        }, headers=auth_header)
        assert resp.status_code == 404


class TestUpdateColumn:
    def test_update(self, client, auth_header, column):
        resp = client.patch(f"/columns/{column['id']}", json={
            "title": "Renamed",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed"

    def test_update_not_found(self, client, auth_header):
        resp = client.patch("/columns/999", json={"title": "X"}, headers=auth_header)
        assert resp.status_code == 404


class TestDeleteColumn:
    def test_delete(self, client, auth_header, column):
        resp = client.delete(f"/columns/{column['id']}", headers=auth_header)
        assert resp.status_code == 204

    def test_delete_not_found(self, client, auth_header):
        resp = client.delete("/columns/999", headers=auth_header)
        assert resp.status_code == 404
