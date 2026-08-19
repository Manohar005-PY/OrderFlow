import hashlib
import hmac
import json
import time

from app.core.exception import WebhookVerificationException
from app.webhook.verifier import ProviderWebhookVerifier


class StripeStyleWebhookVerifier(ProviderWebhookVerifier):
    def __init__(self, secret: str, tolerance_seconds: int = 300):
        self.secret = secret
        self.tolerance_seconds = tolerance_seconds

    def verify(self, payload: bytes, signature: str) -> dict:
        timestamp, signatures = self._parse_signature(signature)
        if abs(time.time() - timestamp) > self.tolerance_seconds:
            raise WebhookVerificationException()

        signed_payload = f"{timestamp}.".encode() + payload
        expected = hmac.new(
            self.secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        if not any(hmac.compare_digest(expected, value) for value in signatures):
            raise WebhookVerificationException()

        try:
            event = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WebhookVerificationException() from error

        if not isinstance(event, dict) or not event.get("id"):
            raise WebhookVerificationException()
        return event

    @staticmethod
    def _parse_signature(signature: str) -> tuple[int, list[str]]:
        values: dict[str, list[str]] = {}
        for item in signature.split(","):
            key, separator, value = item.partition("=")
            if not separator or not key or not value:
                raise WebhookVerificationException()
            values.setdefault(key, []).append(value)

        try:
            timestamp = int(values["t"][0])
            signatures = values["v1"]
        except (KeyError, ValueError):
            raise WebhookVerificationException()
        return timestamp, signatures
