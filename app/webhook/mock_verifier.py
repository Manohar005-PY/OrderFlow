import json

from app.core.exception import WebhookVerificationException
from app.webhook.verifier import ProviderWebhookVerifier


class MockWebhookVerifier(ProviderWebhookVerifier):
    def verify(self, payload: bytes, signature: str) -> dict:
        try:
            event = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WebhookVerificationException() from error
        if not isinstance(event, dict) or not event.get("id"):
            raise WebhookVerificationException()
        return event
