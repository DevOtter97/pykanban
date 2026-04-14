class TestListColumns:
    def test_list_creates_mandatory(self, client, auth_header, project):
        resp = client.get(f"/columns/?project_id={project['id']}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        # By default DESCARTADO is hidden
        assert len(data) == 3
        titles = [c["title"] for c in data]
        assert "TO DO" in titles
        assert "IN PROGRESS" in titles
        assert "DONE" in titles

    def test_list_include_hidden(self, client, auth_header, project):
        resp = client.get(f"/columns/?project_id={project['id']}&include_hidden=true", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        titles = [c["title"] for c in data]
        assert "DESCARTADO" in titles

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
        assert data["is_mandatory"] is False

    def test_create_invalid_project(self, client, auth_header):
        resp = client.post("/columns/", json={
            "title": "X",
            "project_id": 999,
        }, headers=auth_header)
        assert resp.status_code == 404


class TestUpdateColumn:
    def test_update_custom(self, client, auth_header, column):
        resp = client.patch(f"/columns/{column['id']}", json={
            "title": "Renamed",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed"

    def test_cannot_rename_mandatory(self, client, auth_header, project):
        # List to trigger mandatory column creation
        cols = client.get(f"/columns/?project_id={project['id']}&include_hidden=true", headers=auth_header).json()
        todo_col = next(c for c in cols if c["title"] == "TO DO")
        resp = client.patch(f"/columns/{todo_col['id']}", json={"title": "Renamed"}, headers=auth_header)
        assert resp.status_code == 400
        assert "mandatory" in resp.json()["detail"].lower()

    def test_update_not_found(self, client, auth_header):
        resp = client.patch("/columns/999", json={"title": "X"}, headers=auth_header)
        assert resp.status_code == 404


class TestDeleteColumn:
    def test_delete_custom(self, client, auth_header, column):
        resp = client.delete(f"/columns/{column['id']}", headers=auth_header)
        assert resp.status_code == 204

    def test_cannot_delete_mandatory(self, client, auth_header, project):
        cols = client.get(f"/columns/?project_id={project['id']}&include_hidden=true", headers=auth_header).json()
        todo_col = next(c for c in cols if c["title"] == "TO DO")
        resp = client.delete(f"/columns/{todo_col['id']}", headers=auth_header)
        assert resp.status_code == 400
        assert "mandatory" in resp.json()["detail"].lower()

    def test_delete_not_found(self, client, auth_header):
        resp = client.delete("/columns/999", headers=auth_header)
        assert resp.status_code == 404
