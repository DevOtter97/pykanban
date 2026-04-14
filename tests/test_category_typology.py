class TestSetMapping:
    def test_enable(self, client, auth_header, category, typology):
        resp = client.put("/category-typology/", json={
            "category_id": category["id"],
            "typology_id": typology["id"],
            "enabled": True,
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_disable(self, client, auth_header, enabled_combo, category, typology):
        resp = client.put("/category-typology/", json={
            "category_id": category["id"],
            "typology_id": typology["id"],
            "enabled": False,
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_invalid_category(self, client, auth_header, typology):
        resp = client.put("/category-typology/", json={
            "category_id": 999,
            "typology_id": typology["id"],
            "enabled": True,
        }, headers=auth_header)
        assert resp.status_code == 404

    def test_invalid_typology(self, client, auth_header, category):
        resp = client.put("/category-typology/", json={
            "category_id": category["id"],
            "typology_id": 999,
            "enabled": True,
        }, headers=auth_header)
        assert resp.status_code == 404


class TestListMappings:
    def test_list(self, client, auth_header, enabled_combo):
        resp = client.get("/category-typology/", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
