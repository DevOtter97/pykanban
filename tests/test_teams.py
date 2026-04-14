class TestCreateTeam:
    def test_create_as_superadmin(self, client, auth_header):
        resp = client.post("/teams/", json={
            "name": "Dev Team",
            "description": "Development team",
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Dev Team"
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "admin"

    def test_create_as_regular_user_forbidden(self, client, member_header):
        resp = client.post("/teams/", json={"name": "X"}, headers=member_header)
        assert resp.status_code == 403

    def test_create_duplicate_name(self, client, auth_header, team):
        resp = client.post("/teams/", json={"name": "Test Team"}, headers=auth_header)
        assert resp.status_code == 400


class TestListTeams:
    def test_superadmin_sees_all(self, client, auth_header, team):
        resp = client.get("/teams/", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_member_sees_own_teams(self, client, auth_header, member_header, member_user, team):
        # Add member to team
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        resp = client.get("/teams/", headers=member_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_non_member_sees_nothing(self, client, member_header):
        resp = client.get("/teams/", headers=member_header)
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetTeam:
    def test_get_as_member(self, client, auth_header, team):
        resp = client.get(f"/teams/{team['id']}", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Team"

    def test_get_not_member(self, client, member_header, team):
        resp = client.get(f"/teams/{team['id']}", headers=member_header)
        assert resp.status_code == 403


class TestUpdateTeam:
    def test_update_as_admin(self, client, auth_header, team):
        resp = client.patch(f"/teams/{team['id']}", json={
            "name": "Renamed Team",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Team"

    def test_update_as_member_forbidden(self, client, auth_header, member_header, member_user, team):
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        resp = client.patch(f"/teams/{team['id']}", json={"name": "X"}, headers=member_header)
        assert resp.status_code == 403


class TestAddMember:
    def test_add_member(self, client, auth_header, team, member_user):
        resp = client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        assert resp.status_code == 201
        assert resp.json()["role"] == "member"

    def test_add_duplicate_member(self, client, auth_header, team, member_user):
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        resp = client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        assert resp.status_code == 400

    def test_add_nonexistent_user(self, client, auth_header, team):
        resp = client.post(f"/teams/{team['id']}/members", json={
            "user_id": 999,
            "role": "member",
        }, headers=auth_header)
        assert resp.status_code == 404


class TestUpdateMemberRole:
    def test_promote_to_admin(self, client, auth_header, team, member_user):
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        resp = client.patch(f"/teams/{team['id']}/members/{member_user['id']}", json={
            "role": "admin",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"


class TestRemoveMember:
    def test_remove_member(self, client, auth_header, team, member_user):
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        resp = client.delete(f"/teams/{team['id']}/members/{member_user['id']}", headers=auth_header)
        assert resp.status_code == 204

    def test_cannot_remove_last_admin(self, client, auth_header, team, registered_user):
        resp = client.delete(f"/teams/{team['id']}/members/{registered_user['id']}", headers=auth_header)
        assert resp.status_code == 400
        assert "last admin" in resp.json()["detail"].lower()
