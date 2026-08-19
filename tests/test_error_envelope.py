def test_validation_error_has_consistent_envelope(client):
    response = client.get(
        "/products/not-an-integer",
        headers={"X-Request-ID": "validation-request"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["message"] == "Request validation failed"
    assert body["request_id"] == "validation-request"
    assert body["details"]
    assert "Traceback" not in response.text


def test_missing_authentication_has_consistent_envelope(client):
    response = client.get(
        "/users/me",
        headers={"X-Request-ID": "auth-request"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": "http_unauthorized",
        "message": "Not authenticated",
        "request_id": "auth-request",
    }


def test_uncaught_domain_exception_has_domain_error_code(client):
    response = client.patch(
        "/order/999999999/status",
        json={"status": "PAID"},
        headers={"X-Request-ID": "domain-request"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "order_not_found",
        "message": "Order not found",
        "request_id": "domain-request",
    }
    assert "Traceback" not in response.text
