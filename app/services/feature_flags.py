from typing import ClassVar


class FeatureFlagService:
    defaults: ClassVar[dict[str, bool]] = {
        "lesson_generation.enabled": True,
        "teacher_submission.enabled": True,
        "image_upload.enabled": False,
        "textbook_upload.enabled": False,
        "full_lesson_submission.enabled": False,
        "github_publish.enabled": True,
    }

    def is_enabled(self, key: str, *, region_id: str | None = None, school_id: str | None = None) -> bool:
        del region_id, school_id
        return self.defaults.get(key, False)
