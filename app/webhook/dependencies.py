from fastapi import Depends

from app.core.config import settings
from app.webhook.stripe_verifier import StripeStyleWebhookVerifier
from app.webhook.verifier import ProviderWebhookVerifier


def get_webhook_verifier() -> ProviderWebhookVerifier:
    return StripeStyleWebhookVerifier(settings.WEBHOOK_SECRET)


def webhook_verifier_dependency(
    verifier: ProviderWebhookVerifier = Depends(get_webhook_verifier),
) -> ProviderWebhookVerifier:
    return verifier
