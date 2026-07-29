from app.services.model_providers.mock import MockModelProvider


def test_mock_model_generates_structured_lesson() -> None:
    result = MockModelProvider().generate_lesson("Grade 4 math fractions")
    assert result.structured_content.title
    assert result.rendered_markdown.startswith("#")
    assert result.token_output > 0

