from app.core.config import get_settings
from app.services.model_providers import (
    GeminiEmbeddingProvider,
    GeminiModelProvider,
    MockEmbeddingProvider,
    MockModelProvider,
)
from app.services.model_providers.base import EmbeddingProvider, ModelProvider


def get_text_model_provider() -> ModelProvider:
    settings = get_settings()
    if settings.active_text_model_provider == "mock":
        return MockModelProvider()
    if settings.active_text_model_provider == "gemini":
        return GeminiModelProvider()
    # Real providers are intentionally left as adapters to be filled when keys are available.
    raise NotImplementedError(
        f"Text model provider '{settings.active_text_model_provider}' is not implemented yet."
    )


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.active_embedding_provider == "mock":
        return MockEmbeddingProvider(settings.active_embedding_dimensions)
    if settings.active_embedding_provider == "gemini":
        return GeminiEmbeddingProvider()
    raise NotImplementedError(
        f"Embedding provider '{settings.active_embedding_provider}' is not implemented yet."
    )
