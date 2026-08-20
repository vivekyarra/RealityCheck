def test_health_exposes_runtime_truth(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ai_configured"] is False
    assert response.json()["provider_mode"] == "sandbox"


def test_demo_happy_path_via_api(client):
    reset = client.post("/api/demo/reset", json={})
    assert reset.status_code == 200
    observed = client.post("/api/demo/advance", json={"step": "observe"})
    assert observed.json()["status"] == "mismatch"
    blocked = client.post("/api/demo/advance", json={"step": "resolve", "approve": False})
    assert blocked.json()["status"] == "needs_approval"
    monitoring = client.post("/api/demo/advance", json={"step": "resolve", "approve": True})
    assert monitoring.json()["status"] == "monitoring"
    recovered = client.post("/api/demo/advance", json={"step": "verify"})
    assert recovered.json()["status"] == "recovered"
    assert recovered.json()["recovered_amount"] == "350"


def test_contract_extraction_and_case_persistence(client):
    response = client.post(
        "/api/contracts/extract",
        json={
            "filename": "offer.txt",
            "counterparty_hint": "FiberMax",
            "text": "Welcome to FiberMax. Your plan is ₹499/month fixed for 12 months. Installation is free.",
        },
    )
    assert response.status_code == 200
    case_id = response.json()["case"]["id"]
    assert client.get(f"/api/cases/{case_id}").status_code == 200


def test_task_endpoint_rejects_missing_secret(client):
    response = client.post("/api/tasks/tick")
    assert response.status_code == 401


def test_authenticated_task_tick_completes_due_obligation(client):
    from datetime import UTC, datetime, timedelta

    client.app.state.settings.tasks_shared_secret = "test-secret"
    reset = client.post("/api/demo/reset", json={}).json()
    client.post("/api/demo/advance", json={"step": "observe"})
    client.post("/api/demo/advance", json={"step": "resolve", "approve": True})
    case = client.app.state.store.get(reset["id"])
    case.next_action_at = datetime.now(UTC) - timedelta(seconds=1)
    client.app.state.store.put(case)

    response = client.post("/api/tasks/tick", headers={"X-Tasks-Secret": "test-secret"})
    assert response.status_code == 200
    assert response.json()["recovered_cases"] == [reset["id"]]
    assert client.app.state.store.get(reset["id"]).status == "recovered"


def test_demo_sessions_are_isolated_and_cookie_is_hardened(client):
    first = client.post("/api/demo/reset", json={})
    first_id = first.json()["id"]
    assert "HttpOnly" in first.headers["set-cookie"]
    assert "SameSite=strict" in first.headers["set-cookie"]

    client.cookies.clear()
    second = client.post("/api/demo/reset", json={})
    assert second.json()["id"] != first_id


def test_out_of_order_api_calls_do_not_create_fake_recovery(client):
    reset = client.post("/api/demo/reset", json={})
    assert reset.json()["recovered_amount"] == "0"
    premature = client.post("/api/demo/advance", json={"step": "verify"})
    assert premature.json()["status"] == "captured"
    assert premature.json()["recovered_amount"] == "0"


def test_security_headers_and_validation_are_enforced(client):
    response = client.get("/")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'self'" in response.headers["content-security-policy"]
    oversized = "x" * 100_001
    assert client.post("/api/contracts/extract", json={"text": oversized}).status_code == 422

    static = client.get("/static/styles.css", headers={"Accept-Encoding": "gzip"})
    assert static.headers["cache-control"] == "public, max-age=86400"
    assert static.headers["content-encoding"] == "gzip"
