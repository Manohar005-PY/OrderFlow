from abc import ABC, abstractmethod


class ProviderWebhookVerifier(ABC):
    @abstractmethod
    def verify(self, payload: bytes, signature: str) -> dict:
        raise NotImplementedError
