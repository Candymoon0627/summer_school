import argparse
from datetime import UTC, datetime

import httpx

from app.core.config import get_settings
from app.db.models.media import MediaAsset
from app.db.session import SessionLocal
from app.schemas.admin import CreateSchoolRequest
from app.schemas.knowledge import KnowledgeSeedItem
from app.services.knowledge import KnowledgeService
from app.services.lesson_generation import LessonGenerationService
from app.services.lesson_requests import LessonRequestService
from app.services.onboarding import OnboardingService
from app.services.publishing import GitHubPublishingService
from app.services.rag import RagService
from app.services.storage import StorageService


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test configured non-LINE integrations.")
    parser.add_argument(
        "--github-write",
        action="store_true",
        help="Publish one temporary knowledge Markdown file to GitHub, then delete it.",
    )
    args = parser.parse_args()

    settings = get_settings()
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    line_user_id = f"smoke-user-{stamp}"

    with SessionLocal() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name=f"Smoke Test School {stamp}",
                region_code="pattani",
                region_name="Pattani",
                country_code="th",
                resource_level="low",
            )
        )
        print(f"PASS | database school created | school_id={school.school_id}")

        teacher = OnboardingService(db).bind_teacher_by_school_code(
            line_user_id=line_user_id,
            school_code=school.school_code,
            display_name="Smoke Test Teacher",
        )
        if teacher is None:
            raise RuntimeError("Teacher binding failed.")
        print(f"PASS | database teacher bound | teacher_id={teacher.teacher_id}")

        knowledge = KnowledgeService(db).import_seed_item(
            KnowledgeSeedItem(
                knowledge_type="local_example",
                title=f"Smoke fractions market sharing {stamp}",
                region_code="pattani",
                visibility_scope="shared_region",
                subject="math",
                topic="fractions",
                target_grade=4,
                grade_min=4,
                grade_max=4,
                content_en="Use a local market sharing example to explain fractions.",
                content_ms="Gunakan contoh perkongsian di pasar untuk pecahan.",
                local_context="Pattani market context.",
                classroom_use="Students split 12 items into equal groups.",
                verified=True,
            )
        )
        print(f"PASS | knowledge imported and embedded | knowledge_id={knowledge.id}")

        rag_items, confidence = RagService(db).retrieve_for_lesson(
            teacher_id=str(teacher.teacher_id),
            school_id=str(teacher.school_id),
            region_id=str(teacher.region_id),
            subject="math",
            grade=4,
            topic="fractions",
        )
        if not rag_items:
            raise RuntimeError("RAG retrieval returned no items.")
        print(f"PASS | RAG search | confidence={confidence} top={rag_items[0].title}")

        request = LessonRequestService(db).create_from_teacher_text(
            line_user_id=line_user_id,
            text="Grade 4 math fractions, 45 minutes, low-resource classroom",
            enqueue=False,
        )
        lesson_request_id = request["lesson_request_id"]
        lesson = LessonGenerationService(db).generate(lesson_request_id)
        if not lesson.docx_media_asset_id:
            raise RuntimeError("Lesson generation did not create a DOCX media asset.")
        print(f"PASS | lesson generated | lesson_request_id={lesson.id}")

        asset = db.get(MediaAsset, lesson.docx_media_asset_id)
        if asset is None:
            raise RuntimeError("DOCX media asset not found.")
        signed_url = StorageService().signed_url(asset.object_key, expires_in=120)
        download = httpx.get(signed_url, timeout=30)
        download.raise_for_status()
        if len(download.content) == 0:
            raise RuntimeError("Signed URL downloaded an empty file.")
        print(
            "PASS | storage upload and signed download | "
            f"provider={asset.storage_provider} bytes={len(download.content)}"
        )

        if args.github_write:
            KnowledgeService(db).approve_region_shared(knowledge.id)
            publish_result = GitHubPublishingService(db).publish_knowledge_item(str(knowledge.id))
            print(f"PASS | GitHub publish | path={publish_result.github_path}")
            _delete_github_file(
                repo=settings.github_repo,
                token=settings.github_token,
                branch=settings.github_branch,
                path=publish_result.github_path,
            )
            print("PASS | GitHub cleanup | deleted temporary published file")
        else:
            print("SKIP | GitHub write | pass --github-write to test create/delete")


def _delete_github_file(repo: str | None, token: str | None, branch: str, path: str) -> None:
    if not repo or not token:
        raise RuntimeError("GITHUB_REPO and GITHUB_TOKEN are required for GitHub cleanup.")
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with httpx.Client(timeout=30) as client:
        existing = client.get(url, headers=headers, params={"ref": branch})
        existing.raise_for_status()
        sha = existing.json()["sha"]
        response = client.request(
            "DELETE",
            url,
            headers=headers,
            json={
                "message": f"cleanup smoke publish: {path}",
                "sha": sha,
                "branch": branch,
            },
        )
        response.raise_for_status()


if __name__ == "__main__":
    main()
