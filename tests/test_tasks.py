from datetime import datetime, timezone, timedelta


class TestCreateTask:
    def test_create(self, client, auth_header, column):
        resp = client.post("/tasks/", json={
            "title": "New Task",
            "column_id": column["id"],
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Task"
        assert data["column_id"] == column["id"]

    def test_create_with_due_date(self, client, auth_header, column):
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        resp = client.post("/tasks/", json={
            "title": "Due Task",
            "column_id": column["id"],
            "due_date": due,
        }, headers=auth_header)
        assert resp.status_code == 201
        assert resp.json()["due_date"] is not None

    def test_create_with_assignment(self, client, auth_header, column, registered_user):
        resp = client.post("/tasks/", json={
            "title": "Assigned Task",
            "column_id": column["id"],
            "assigned_to": registered_user["id"],
        }, headers=auth_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["assigned_to"] == registered_user["id"]
        assert data["assignee"]["username"] == registered_user["username"]

    def test_create_invalid_column(self, client, auth_header):
        resp = client.post("/tasks/", json={
            "title": "X",
            "column_id": 999,
        }, headers=auth_header)
        assert resp.status_code == 404

    def test_create_invalid_assignee(self, client, auth_header, column):
        resp = client.post("/tasks/", json={
            "title": "X",
            "column_id": column["id"],
            "assigned_to": 999,
        }, headers=auth_header)
        assert resp.status_code == 404


class TestUpdateTask:
    def test_update_title(self, client, auth_header, task):
        resp = client.patch(f"/tasks/{task['id']}", json={
            "title": "Updated",
        }, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    def test_update_not_found(self, client, auth_header):
        resp = client.patch("/tasks/999", json={"title": "X"}, headers=auth_header)
        assert resp.status_code == 404


class TestDeleteTask:
    def test_delete(self, client, auth_header, task):
        resp = client.delete(f"/tasks/{task['id']}", headers=auth_header)
        assert resp.status_code == 204

    def test_delete_not_found(self, client, auth_header):
        resp = client.delete("/tasks/999", headers=auth_header)
        assert resp.status_code == 404


class TestGetMyTasks:
    def test_my_tasks(self, client, auth_header, column, registered_user):
        client.post("/tasks/", json={
            "title": "Mine",
            "column_id": column["id"],
            "assigned_to": registered_user["id"],
        }, headers=auth_header)
        resp = client.get("/tasks/mine", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Mine"

    def test_my_tasks_empty(self, client, auth_header):
        resp = client.get("/tasks/mine", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetTasksByDueDate:
    def test_due_tasks(self, client, auth_header, column):
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        client.post("/tasks/", json={
            "title": "Due",
            "column_id": column["id"],
            "due_date": due,
        }, headers=auth_header)
        resp = client.get("/tasks/due", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_overdue_filter(self, client, auth_header, column):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        client.post("/tasks/", json={
            "title": "Overdue",
            "column_id": column["id"],
            "due_date": past,
        }, headers=auth_header)
        client.post("/tasks/", json={
            "title": "Future",
            "column_id": column["id"],
            "due_date": future,
        }, headers=auth_header)
        resp = client.get("/tasks/due?overdue=true", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Overdue"
