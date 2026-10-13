from app import app


def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health():
    r = client().get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"


def test_items():
    r = client().get("/api/items")
    assert r.status_code == 200
    assert len(r.get_json()["items"]) == 5


def test_metrics_exposed():
    c = client()
    c.get("/")
    body = c.get("/metrics").get_data(as_text=True)
    assert "app_requests_total" in body
    assert "app_request_duration_seconds" in body
