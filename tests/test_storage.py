from pathlib import Path

from app.core.config import get_settings
from app.services.storage import StorageService


def test_local_storage_put_signed_url_and_delete(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path / "storage"))
    get_settings.cache_clear()

    source = tmp_path / "lesson.txt"
    source.write_text("lesson file", encoding="utf-8")

    service = StorageService()
    object_key = service.put_file(source, "lesson_docx/lesson.txt")
    stored_path = Path(service.signed_url(object_key))

    assert object_key == "lesson_docx/lesson.txt"
    assert stored_path.read_text(encoding="utf-8") == "lesson file"

    service.delete_file(object_key)
    assert not stored_path.exists()

    get_settings.cache_clear()
