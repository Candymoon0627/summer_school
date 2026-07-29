from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.schemas.knowledge import KnowledgeSeedItem
from app.services.content_review import ContentReviewService
from app.services.duplicate import DuplicateDetectionService
from app.services.knowledge import KnowledgeService
from app.services.publishing import GitHubPublishingService
from app.services.publishing_batch import KnowledgeBatchPublishingService


def test_sensitive_copyright_and_mock_publish_flow() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        item = KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Fish sharing for fractions",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_en="Use fish sharing to teach fractions.",
                verified=True,
            )
        )

        sensitive = ContentReviewService(db).run_sensitive_check(item.id)
        assert sensitive["risk_level"] == "low"
        copyright_result = ContentReviewService(db).run_copyright_check(item.id)
        assert copyright_result["copyright_status"] == "likely_original"

        publish = GitHubPublishingService(db).publish_knowledge_item(str(item.id))
        assert publish.github_path.endswith(".md")
        assert publish.commit_sha.startswith("mock-")


def test_duplicate_detection_and_merge() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        first = KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Fish sharing for fractions A",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_en="Use fish sharing to teach fractions.",
                verified=True,
            )
        )
        second = KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Fish sharing for fractions B",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_en="Use fish sharing to teach fractions.",
                verified=True,
            )
        )

        candidates = DuplicateDetectionService(db).detect_for_item(second.id, threshold=-1)
        assert candidates
        result = DuplicateDetectionService(db).merge_duplicate(
            duplicate_item_id=second.id,
            main_item_id=first.id,
        )
        assert result["status"] == "merged"


def test_github_publish_updates_existing_file(monkeypatch) -> None:
    from app.core.config import get_settings
    from app.services.publishing import GitHubPublishingService

    captured_payloads = []

    class FakeResponse:
        def __init__(self, status_code: int, data: dict) -> None:
            self.status_code = status_code
            self._data = data

        def json(self) -> dict:
            return self._data

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise AssertionError(f"unexpected status {self.status_code}")

    class FakeClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url, headers, params):
            return FakeResponse(200, {"sha": "existing-file-sha"})

        def put(self, url, json, headers):
            captured_payloads.append(json)
            return FakeResponse(200, {"commit": {"sha": "new-commit-sha"}})

    monkeypatch.setenv("GITHUB_REPO", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_BRANCH", "main")
    get_settings.cache_clear()
    monkeypatch.setattr("app.services.publishing.httpx.Client", FakeClient)

    result = GitHubPublishingService.__new__(GitHubPublishingService)._commit_or_mock(
        "knowledge/test.md",
        "# Test",
    )

    assert result.commit_sha == "new-commit-sha"
    assert captured_payloads[0]["sha"] == "existing-file-sha"

    get_settings.cache_clear()


def test_batch_publish_dry_run_excludes_test_data_by_default() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Synthetic test item",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_th="เศษส่วน",
                content_ms="Pecahan",
                content_en="Fractions",
                source_type="oer_synthetic_test",
                source_note="batch=test",
                verified=True,
            )
        )

        result = KnowledgeBatchPublishingService(db).publish(region_code="pattani", dry_run=True)

    assert result.candidates == []
    assert result.published == []


def test_batch_publish_dry_run_can_include_test_data() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        item = KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Synthetic test item",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_th="เศษส่วน",
                content_ms="Pecahan",
                content_en="Fractions",
                source_type="oer_synthetic_test",
                source_note="batch=test",
                verified=True,
            )
        )

        result = KnowledgeBatchPublishingService(db).publish(
            region_code="pattani",
            allow_test_data=True,
            dry_run=True,
        )

    assert len(result.candidates) == 1
    assert result.candidates[0].id == str(item.id)
    assert "test_data" in result.candidates[0].warnings


def test_batch_publish_execute_blocks_candidates_with_warnings() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title="Incomplete source item",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_en="Fractions",
                source_type="project_manual",
                verified=True,
            )
        )

        try:
            KnowledgeBatchPublishingService(db).publish(
                region_code="pattani",
                dry_run=False,
            )
        except ValueError as exc:
            assert "Refusing to publish candidates with warnings" in str(exc)
        else:
            raise AssertionError("Expected warning candidates to block execute.")
