class TestCreateProject:
    def test_create(self, client, auth_header, team):
        resp = client.post("/projects/", json={
            "title": "My Project",
            "description": "desc",
            "team_id": team["id"],
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Project"
        assert data["description"] == "desc"
        assert data["team_id"] == team["id"]
        assert data["archived"] is False

    def test_create_unauthenticated(self, client):
        resp = client.post("/projects/", json={"title": "X", "team_id": 1})
        assert resp.status_code == 401

    def test_create_requires_team_id(self, client, auth_header):
        resp = client.post("/projects/", json={"title": "X"}, headers=auth_header)
        assert resp.status_code == 422


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

    def test_list_by_team(self, client, auth_header, project, team):
        resp = client.get(f"/projects/?team_id={team['id']}", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


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


class TestArchiveProject:
    def test_archive(self, client, auth_header, project):
        resp = client.post(f"/projects/{project['id']}/archive", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["archived"] is True

        # Archived projects don't appear in list
        resp = client.get("/projects/", headers=auth_header)
        assert resp.json() == []

    def test_unarchive(self, client, auth_header, project):
        client.post(f"/projects/{project['id']}/archive", headers=auth_header)
        resp = client.post(f"/projects/{project['id']}/unarchive", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["archived"] is False
