def test_webhook_requires_signature_header(client):
    response = client.post(
        "/payments/webhook",
        content=b'{"id":"evt_missing_signature"}',
    )
    assert response.status_code == 401


def test_webhook_rejects_tampered_payload(client, signed_webhook):
    payload, headers = signed_webhook("provider-payment")
    response = client.post(
        "/payments/webhook",
        content=payload.replace(b"provider-payment", b"tampered-payment"),
        headers=headers,
    )
    assert response.status_code == 401
