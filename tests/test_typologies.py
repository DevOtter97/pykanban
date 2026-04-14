class TestCreateTypology:
    def test_create(self, client, auth_header):
        resp = client.post("/typologies/", json={
            "name": "Desarrollo",
            "description": "Development work",
        }, headers=auth_header)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Desarrollo"

    def test_create_duplicate(self, client, auth_header, typology):
        resp = client.post("/typologies/", json={"name": "Desarrollo"}, headers=auth_header)
        assert resp.status_code == 400


class TestListTypologies:
    def test_list(self, client, auth_header, typology):
        resp = client.get("/typologies/", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestUpdateTypology:
    def test_update(self, client, auth_header, typology):
        resp = client.patch(f"/typologies/{typology['id']}", json={
            "name": "Mantenimiento",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Mantenimiento"

    def test_update_not_found(self, client, auth_header):
        resp = client.patch("/typologies/999", json={"name": "X"}, headers=auth_header)
        assert resp.status_code == 404


class TestDeleteTypology:
    def test_delete(self, client, auth_header, typology):
        resp = client.delete(f"/typologies/{typology['id']}", headers=auth_header)
        assert resp.status_code == 204

    def test_delete_not_found(self, client, auth_header):
        resp = client.delete("/typologies/999", headers=auth_header)
        assert resp.status_code == 404
