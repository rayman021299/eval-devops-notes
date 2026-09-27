from app import app, get_redis_client


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_add_and_get_notes():
    r = get_redis_client()
    r.delete("notes")

    client = app.test_client()

    post_res = client.post("/notes", json={"text": "Premiere note"})
    assert post_res.status_code == 201
    assert post_res.get_json()["status"] == "added"

    get_res = client.get("/notes")
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert data["count"] == 1
    assert "Premiere note" in data["notes"]


def test_add_note_empty():
    client = app.test_client()
    response = client.post("/notes", json={})
    assert response.status_code == 400


def test_simulate_error_endpoint():
    client = app.test_client()
    response = client.get("/simulate-error")
    assert response.status_code == 500
    assert response.get_json()["error"] == "Erreur simulee"


def test_metrics_endpoint():
    client = app.test_client()
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.data
    assert b"app_version_info" in response.data
