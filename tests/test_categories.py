class TestCreateCategory:
    def test_create(self, client, auth_header):
        resp = client.post("/categories/", json={
            "name": "Bug",
            "description": "Bug report",
        }, headers=auth_header)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Bug"

    def test_create_duplicate(self, client, auth_header, category):
        resp = client.post("/categories/", json={"name": "Bug"}, headers=auth_header)
        assert resp.status_code == 400


class TestListCategories:
    def test_list(self, client, auth_header, category):
        resp = client.get("/categories/", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestUpdateCategory:
    def test_update(self, client, auth_header, category):
        resp = client.patch(f"/categories/{category['id']}", json={
            "name": "Feature",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Feature"

    def test_update_not_found(self, client, auth_header):
        resp = client.patch("/categories/999", json={"name": "X"}, headers=auth_header)
        assert resp.status_code == 404


class TestDeleteCategory:
    def test_delete(self, client, auth_header, category):
        resp = client.delete(f"/categories/{category['id']}", headers=auth_header)
        assert resp.status_code == 204

    def test_delete_not_found(self, client, auth_header):
        resp = client.delete("/categories/999", headers=auth_header)
        assert resp.status_code == 404
