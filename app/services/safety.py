from app.services.model_registry import get_text_model_provider


class SafetyService:
    def classify_sensitive_content(self, text: str) -> dict:
        provider = get_text_model_provider()
        return provider.classify_json(
            "Classify sensitive educational content and return JSON only:\n" + text
        )

    def classify_copyright_risk(self, text: str) -> dict:
        provider = get_text_model_provider()
        return provider.classify_json(
            "Classify copyright risk for educational content and return JSON only:\n" + text
        )

