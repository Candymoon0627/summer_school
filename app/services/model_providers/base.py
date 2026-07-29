from abc import ABC, abstractmethod

from app.schemas.lesson import LessonGenerationResult


class ModelProvider(ABC):
    @abstractmethod
    def generate_lesson(self, prompt: str) -> LessonGenerationResult:
        raise NotImplementedError

    @abstractmethod
    def classify_json(self, prompt: str) -> dict:
        raise NotImplementedError


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

