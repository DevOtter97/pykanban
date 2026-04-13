from datetime import datetime, timezone, timedelta


class TestCreateCard:
    def test_create(self, client, auth_header, column):
        resp = client.post("/cards/", json={
            "title": "New Card",
            "column_id": column["id"],
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Card"
        assert data["column_id"] == column["id"]

    def test_create_with_due_date(self, client, auth_header, column):
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        resp = client.post("/cards/", json={
            "title": "Due Card",
            "column_id": column["id"],
            "due_date": due,
        }, headers=auth_header)
        assert resp.status_code == 201
        assert resp.json()["due_date"] is not None

    def test_create_with_assignment(self, client, auth_header, column, registered_user):
        resp = client.post("/cards/", json={
            "title": "Assigned Card",
            "column_id": column["id"],
            "assigned_to": registered_user["id"],
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["assigned_to"] == registered_user["id"]
        assert data["assignee"]["username"] == registered_user["username"]

    def test_create_invalid_column(self, client, auth_header):
        resp = client.post("/cards/", json={
            "title": "X",
            "column_id": 999,
        }, headers=auth_header)
        assert resp.status_code == 404

    def test_create_invalid_assignee(self, client, auth_header, column):
        resp = client.post("/cards/", json={
            "title": "X",
            "column_id": column["id"],
            "assigned_to": 999,
        }, headers=auth_header)
        assert resp.status_code == 404


class TestUpdateCard:
    def test_update_title(self, client, auth_header, card):
        resp = client.patch(f"/cards/{card['id']}", json={
            "title": "Updated",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    def test_update_not_found(self, client, auth_header):
        resp = client.patch("/cards/999", json={"title": "X"}, headers=auth_header)
        assert resp.status_code == 404


class TestDeleteCard:
    def test_delete(self, client, auth_header, card):
        resp = client.delete(f"/cards/{card['id']}", headers=auth_header)
        assert resp.status_code == 204

    def test_delete_not_found(self, client, auth_header):
        resp = client.delete("/cards/999", headers=auth_header)
        assert resp.status_code == 404


class TestGetMyCards:
    def test_my_cards(self, client, auth_header, column, registered_user):
        client.post("/cards/", json={
            "title": "Mine",
            "column_id": column["id"],
            "assigned_to": registered_user["id"],
        }, headers=auth_header)
        resp = client.get("/cards/mine", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Mine"

    def test_my_cards_empty(self, client, auth_header):
        resp = client.get("/cards/mine", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetCardsByDueDate:
    def test_due_cards(self, client, auth_header, column):
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        client.post("/cards/", json={
            "title": "Due",
            "column_id": column["id"],
            "due_date": due,
        }, headers=auth_header)
        resp = client.get("/cards/due", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_overdue_filter(self, client, auth_header, column):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        client.post("/cards/", json={
            "title": "Overdue",
            "column_id": column["id"],
            "due_date": past,
        }, headers=auth_header)
        client.post("/cards/", json={
            "title": "Future",
            "column_id": column["id"],
            "due_date": future,
        }, headers=auth_header)
        resp = client.get("/cards/due?overdue=true", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Overdue"
