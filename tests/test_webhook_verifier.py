import hashlib
import hmac
import json
import time

import pytest

from app.core.exception import WebhookVerificationException
from app.webhook.stripe_verifier import StripeStyleWebhookVerifier


SECRET = "webhook-test-secret-with-at-least-32-characters"


def signed(payload: bytes, timestamp: int | None = None) -> str:
    timestamp = timestamp or int(time.time())
    digest = hmac.new(
        SECRET.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def payload():
    return json.dumps(
        {"id": "evt_test_1", "data": {"object": {"provider_payment_id": "pay_1"}}},
        separators=(",", ":"),
    ).encode()


def test_valid_signature_is_accepted():
    event = StripeStyleWebhookVerifier(SECRET).verify(payload(), signed(payload()))
    assert event["id"] == "evt_test_1"


def test_invalid_signature_is_rejected():
    with pytest.raises(WebhookVerificationException):
        StripeStyleWebhookVerifier(SECRET).verify(payload(), "t=1,v1=invalid")


def test_modified_payload_is_rejected():
    original = payload()
    with pytest.raises(WebhookVerificationException):
        StripeStyleWebhookVerifier(SECRET).verify(
            original.replace(b"pay_1", b"pay_2"),
            signed(original),
        )


def test_missing_signature_is_rejected():
    with pytest.raises(WebhookVerificationException):
        StripeStyleWebhookVerifier(SECRET).verify(payload(), "")


def test_expired_timestamp_is_rejected():
    with pytest.raises(WebhookVerificationException):
        StripeStyleWebhookVerifier(SECRET, tolerance_seconds=300).verify(
            payload(),
            signed(payload(), int(time.time()) - 301),
        )


def test_malformed_event_is_rejected():
    body = b'{"data": {}}'
    with pytest.raises(WebhookVerificationException):
        StripeStyleWebhookVerifier(SECRET).verify(body, signed(body))
