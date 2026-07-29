from app.services.feature_flags import FeatureFlagService


def test_placeholder_features_are_disabled() -> None:
    flags = FeatureFlagService()
    assert flags.is_enabled("lesson_generation.enabled")
    assert not flags.is_enabled("image_upload.enabled")
    assert not flags.is_enabled("textbook_upload.enabled")

