class TestRolePermissions:
    """Test that role-based permissions are enforced correctly."""

    def test_regular_user_cannot_create_team(self, client, member_header):
        resp = client.post("/teams/", json={"name": "Forbidden"}, headers=member_header)
        assert resp.status_code == 403

    def test_member_cannot_create_project(self, client, auth_header, member_header, member_user, team):
        # Add as member (not admin)
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        resp = client.post("/projects/", json={
            "title": "Forbidden",
            "team_id": team["id"],
        }, headers=member_header)
        assert resp.status_code == 403

    def test_member_can_create_card(self, client, auth_header, member_header, member_user, team, project):
        # Add as member
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        # Get a column
        cols = client.get(f"/columns/?project_id={project['id']}", headers=auth_header).json()
        col_id = cols[0]["id"]
        resp = client.post("/cards/", json={
            "title": "Member Card",
            "column_id": col_id,
        }, headers=member_header)
        assert resp.status_code == 201

    def test_member_can_move_card(self, client, auth_header, member_header, member_user, team, project):
        # Add as member
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        cols = client.get(f"/columns/?project_id={project['id']}&include_hidden=true", headers=auth_header).json()
        todo_col = next(c for c in cols if c["title"] == "TO DO")
        done_col = next(c for c in cols if c["title"] == "DONE")
        # Create card
        card = client.post("/cards/", json={
            "title": "Move me",
            "column_id": todo_col["id"],
        }, headers=member_header).json()
        # Move card
        resp = client.post(f"/cards/{card['id']}/move", json={
            "column_id": done_col["id"],
            "notes": "Done!",
        }, headers=member_header)
        assert resp.status_code == 200
        assert resp.json()["completed_at"] is not None

    def test_member_cannot_create_column(self, client, auth_header, member_header, member_user, team, project):
        client.post(f"/teams/{team['id']}/members", json={
            "user_id": member_user["id"],
            "role": "member",
        }, headers=auth_header)
        resp = client.post("/columns/", json={
            "title": "Forbidden Column",
            "project_id": project["id"],
        }, headers=member_header)
        assert resp.status_code == 403

    def test_non_member_cannot_access_project(self, client, member_header, project):
        resp = client.get(f"/columns/?project_id={project['id']}", headers=member_header)
        assert resp.status_code == 403

    def test_admin_can_create_column(self, client, auth_header, team, project):
        resp = client.post("/columns/", json={
            "title": "Admin Column",
            "project_id": project["id"],
        }, headers=auth_header)
        assert resp.status_code == 201

    def test_admin_can_archive_project(self, client, auth_header, project):
        resp = client.post(f"/projects/{project['id']}/archive", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["archived"] is True
