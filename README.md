# Edu AI Assistant MVP

This repository contains the MVP scaffold for the LINE-based localized AI lesson plan assistant.

## Local Setup

1. Copy `.env.example` to `.env`.
2. Keep `ACTIVE_TEXT_MODEL_PROVIDER=mock` until real model keys are available, or use Gemini:

```env
ACTIVE_TEXT_MODEL_PROVIDER=gemini
ACTIVE_TEXT_MODEL_NAME=gemini-3.6-flash
ACTIVE_EMBEDDING_PROVIDER=gemini
ACTIVE_EMBEDDING_MODEL=gemini-embedding-2
ACTIVE_EMBEDDING_DIMENSIONS=3072
GEMINI_API_KEY=your-key
```
3. Install dependencies into the D drive virtual environment:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe -m pip install -e ".[dev]"
```

4. Start services:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_docker_images.ps1
docker compose -p edu_ai up -d --no-build api worker
```

Services:

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Admin: http://localhost:5173
- Postgres: localhost:5432
- Redis: localhost:6379

## Current MVP

- FastAPI webhook/admin API entrypoints.
- RQ worker entrypoint.
- Refine admin dashboard at http://localhost:5173.
- SQLAlchemy models for core MVP entities.
- Mock and Gemini model providers.
- Separate Thai, Local Malay, and English DOCX export.
- LINE language preference with Thai default and `/change language` Quick Reply selection.
- LINE menu-command handling for lesson generation, submissions, image/OCR placeholder,
  AI experience placeholder, history, and help.
- Teacher text submissions with two-stage admin review and publish-to-RAG.
- LINE text submissions are auto-classified for grade/subject/topic when the body contains
  recognizable phrases such as `Grade 4 fractions`.
- Database-backed multi-account admin login with school-scoped `school_admin` isolation.
- Storage/GitHub/LINE provider integrations.
- Windows host-side RQ workers use `SimpleWorker`; Linux/container workers use the default RQ
  worker.

Uncertain external integrations are intentionally abstracted behind services/providers.

## Local Functional Smoke Path

After setting up `.env`, create tables for the scaffold:

```powershell
python scripts/seed_system.py
```

Create a school:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/admin/schools `
  -ContentType "application/json" `
  -Body '{"name":"Test School","region_code":"pattani","region_name":"Pattani"}'
```

Bind a test LINE user id:

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/admin/dev/bind-teacher?line_user_id=test-user&school_code=CODE"
```

Create a lesson request without Redis:

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/admin/dev/lesson-request?line_user_id=test-user&text=四年级数学 分数&enqueue=false"
```

When Redis and worker are running, set `enqueue=true`.

## Redis/RQ Async Smoke

Start Redis only and run the host-side RQ smoke:

```powershell
docker compose -p edu_ai up -d redis
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_rq_async.py
```

Start the API and worker containers for container-to-container async generation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_docker_images.ps1
docker compose -p edu_ai up -d --no-build api worker
```

Use the explicit `-p edu_ai` project name on Windows because non-ASCII workspace paths can break
Docker Compose's automatic project-name detection. The build script uses a clean temporary Docker
context so stale local pytest/cache directories do not break image builds.

## Sentry Smoke

Create a Sentry Python/FastAPI project, copy the project DSN into `.env`, and keep the trace sample
rate low for MVP validation:

```env
SENTRY_DSN=https://public-key@o000000.ingest.sentry.io/000000
SENTRY_TRACES_SAMPLE_RATE=0.05
```

Restart the API/worker after changing `.env`, then verify configuration:

```powershell
Invoke-RestMethod http://localhost:8000/admin/status
Invoke-RestMethod -Method Post http://localhost:8000/admin/dev/sentry-test
```

For a host-side SDK check without the API:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_sentry.py
```

## Development Work Available Now

These flows can be developed and tested from admin/debug endpoints or LINE:

- Create regions and schools.
- Generate school invitation codes.
- Bind a mock `line_user_id` to a school.
- Create lesson requests through admin debug endpoints.
- Generate mock structured lessons and DOCX files.
- Import seed knowledge from API or YAML.
- Create teacher submissions from Admin or LINE text.
- Run first review, second review, revision, rejection, and publish-to-knowledge flows.
- Create knowledge versions.
- Generate mock embeddings for knowledge chunks.
- Search knowledge through filtered RAG.
- Soft-delete knowledge and remove it from RAG.
- Use Refine Admin to manage schools, teachers, lessons, submissions, knowledge review,
  publishing dry-runs, RAG checks, coverage, and audit logs.

## Admin Dashboard

Run the Refine Admin UI:

```powershell
cd admin_ui
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The current MVP dashboard includes:

- Login using `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`.
- Role-based controls for `viewer`, `operator`, `reviewer`, and `super_admin`.
- Overview metrics for schools, teachers, knowledge items, lesson requests, lesson statuses, and
  knowledge review/vector statuses.
- School creation, invitation-code display, teacher list, and test teacher binding.
- Lesson request list, debug lesson creation, lesson detail, DOCX asset view, RAG refs, and manual
  generate-now operation.
- Teacher submission list, manual submission creation, content editing, first review, second
  review, return-for-revision, rejection, and publish-to-knowledge.
- Knowledge import, review operations, sensitive/copyright/duplicate checks, region approval,
  rejection, and version list.
- GitHub publishing candidate dry-run and guarded execute flow.
- Coverage, RAG search, recent audit logs, and smoke-cleanup command guidance.

Install and run:

```powershell
cd admin_ui
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The Refine UI uses the FastAPI admin endpoints at `http://127.0.0.1:8000` by default. Override with:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Implemented Refine screens:

- Login with the existing `.env` bootstrap admin or database-backed admin users.
- Overview metrics and recent audit logs.
- Submission list/detail with create, edit, first approve, second approve, request revision,
  reject, and publish-to-knowledge actions. Submission list/detail displays subject, topic, grade,
  visibility scope, and linked knowledge item status.
- Lesson and Audit Log read-only tables.
- Knowledge management with import, sensitive/copyright/duplicate checks, approve-school,
  approve-region, reject, soft-delete, version restore, re-embed, and single-item publish actions.
  Selected knowledge items display owner scope, grade, GitHub path, and GitHub commit.
- Scalable School Directory view with server-side search/pagination and teachers grouped under the
  selected school.
- Operations tools for school creation, teacher binding, debug lesson creation/generation, RAG
  search, coverage, and GitHub publishing candidates/dry-runs/execute. Execute requires typing
  `PUBLISH`.
- Scoped `school_admin` mode is supported by setting `ADMIN_ROLE=school_admin` and
  `ADMIN_SCHOOL_IDS=<school_uuid>[,<school_uuid>]`. In this mode admin APIs and Refine views are
  filtered to assigned schools; GitHub publishing, Sentry test, school creation, and region/global
  knowledge approval remain unavailable.
- Multi-account admin login is supported through database-backed `admin_users`. Log in with the
  admin user's email and password. Use the `Admin Users` page as `super_admin` to create
  `school_admin` accounts and assign `school_ids`.

School-scoped admin behavior:

- `school_admin` can see only assigned schools, teachers, lessons, submissions, and accessible
  knowledge.
- `school_admin` can import/manage school-owned private knowledge; backend enforcement forces
  school-admin imports to `private_school`.
- `school_admin` can first/second approve and publish its own school's submissions to private
  school knowledge.
- `super_admin` can see all schools and submissions, approve regional/global knowledge, and publish
  shared knowledge to GitHub.

Refine smoke test used for this migration:

```powershell
cd admin_ui
npm install --no-save @playwright/test
npx playwright install chromium
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="<ADMIN_PASSWORD from .env>"
npx playwright test .tmp/refine-smoke.spec.ts --reporter=line
```

For the full Refine button test, run the API with mock providers and no GitHub credentials so
model generation and publish actions remain local/mock-only.

## Seed Knowledge

Seed knowledge files live in `data/seed_knowledge/*.yaml`. The first MVP test file is:

```text
data/seed_knowledge/pattani_test_math_science.yaml
data/seed_knowledge/pattani_test_80.yaml
```

The `pattani_test_80.yaml` file contains 80 self-authored Thai-first test items for Pattani
math/science RAG validation. These items are intended to verify import, embedding, retrieval, and
lesson-generation behavior before final curriculum review.

Import all seed YAML files:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\import_seed_knowledge.py
```

Import only the 80-item Pattani test batch:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\import_seed_knowledge.py --file data\seed_knowledge\pattani_test_80.yaml
```

Delete that remote/local test batch if needed:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\cleanup_seed_knowledge.py --batch-id pattani-test-v1-80
```

Run a remote end-to-end check against the imported seed batch:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_remote_seed_lesson.py --batch-id pattani-test-v1-80 --subject science --grade 4 --topic "water cycle"
```

This verifies the remote seed batch, RAG retrieval, Gemini lesson generation, recorded
`lesson_knowledge_refs`, Supabase Storage upload, and signed DOCX download.

## Trilingual Lesson Output

Lesson generation is Thai-first with Local Malay and English helper text. The structured lesson
schema includes trilingual fields such as `title_trilingual`, `summary_trilingual`,
`teaching_objectives_trilingual`, `lesson_flow_trilingual`, and `practice_questions_trilingual`.
DOCX export now creates separate Thai, Local Malay, and English documents. The Thai asset remains
the primary `lesson_requests.docx_media_asset_id` for backward compatibility, while all three files
are stored as media assets with purposes `lesson_docx_th`, `lesson_docx_ms`, and `lesson_docx_en`.
LINE completion messages use the teacher's selected language and include only that language's signed
DOCX download link.

## LINE Language and Navigation

Teachers default to Thai output. A bound teacher can send `/change language`, `เปลี่ยนภาษา`, or
`tukar bahasa` to choose Thai, Local Malay, or English through Quick Reply. The preference is saved
on the teacher profile and is used for LINE replies and the DOCX link selected in lesson completion
messages.

Rich Menu buttons should send stable internal commands:

```text
/menu_lesson
/menu_submit_text
/menu_submit_image
/menu_ai_experience
/menu_history
/menu_help
```

The webhook also accepts Thai, Local Malay, and English aliases for those actions. Rich Menu
commands now return Flex Message cards with action buttons and Quick Reply shortcuts for the next
step, while `/menu_history` returns the recent lesson-request list. Lesson generation uses a guided
flow: choose grade, choose subject, then type the topic. Text-submission Format/Example buttons only
show instructions; they do not create a submission. To switch a teacher's bottom Rich Menu after
language selection, configure the three optional LINE Rich Menu IDs:

```env
LINE_RICH_MENU_ID_TH=
LINE_RICH_MENU_ID_MS=
LINE_RICH_MENU_ID_EN=
```

Generate the MVP 2x3 template PNG assets:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\generate_line_rich_menu_assets.py
```

Create and upload the three Rich Menus:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\setup_line_rich_menu.py `
  --th-image data\line\rich_menu_th.png `
  --ms-image data\line\rich_menu_ms.png `
  --en-image data\line\rich_menu_en.png `
  --set-default th
```

## Teacher Submissions

Text submissions are supported now. LINE image/OCR submission is intentionally marked as
under development for this version.

From LINE, a bound teacher can create a submission by starting the message with one of these
prefixes:

```text
投稿：local knowledge text
投稿: local knowledge text
submit: local knowledge text
submission: local knowledge text
```

Messages without those prefixes continue to be treated as lesson-generation requests.

Submission review flow:

```text
draft -> pending_review -> first_approved -> second_approved -> embedded
```

Exception states:

```text
needs_revision
rejected
sensitive_hold
publish_failed
embedding_failed
```

The Admin dashboard has a `Submissions` tab for list/detail/edit/review operations. After second
approval, `Publish` creates a `KnowledgeItem`, embeds it, and makes it available to RAG. GitHub
publishing is still performed through the existing `Publishing & RAG` flow.

LINE lesson requests do not need to be a fixed English sentence. The parser currently recognizes
English, Thai, and Chinese subject/grade/topic cues, for example:

```text
Grade 4 science water cycle
ขอแผนการสอน ป.4 วิทยาศาสตร์ เรื่องวัฏจักรน้ำ
ป.4 คณิตศาสตร์ เศษส่วน
四年级数学 分数
```

## GitHub Knowledge Publishing

Check GitHub readiness:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\check_github_readiness.py
```

Dry-run publish candidates without writing to GitHub:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\publish_knowledge_batch.py --region pattani --limit 20
```

By default, synthetic test data is excluded and candidates with warnings are blocked from real
publish. To inspect test candidates:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\publish_knowledge_batch.py --region pattani --allow-test-data --limit 20
```

Real publish requires `--execute`; use `--allow-warnings` only after manually reviewing warnings.

Current delivery state on 2026-07-29:

- `pattani_test_80.yaml` has been retained as the baseline MVP RAG batch.
- 80 Pattani seed knowledge items are embedded and published to GitHub.
- Published split: `math:40`, `science:40`.
- Remaining approved shared items without GitHub path: `0`.
- Example published path:
  `knowledge/countries/th/regions/8616f9ac-dc61-4b23-b5c9-6507b3ad2e6c/science/grade-3-5/weather-weather-observation-test-item-4-96238704.md`.

The current batch is synthetic MVP test data and was published only after explicitly allowing test-data
and warning candidates.

## Smoke Data Cleanup

Inspect automatically generated smoke data:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\cleanup_smoke_data.py
```

Delete matched automatic smoke data:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\cleanup_smoke_data.py --execute
```

Delete matched rows and their Storage files:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\cleanup_smoke_data.py --execute --delete-storage-files
```

The script does not include the manually used `LINE Smoke Test School` unless
`--include-line-smoke-school` is passed.

## Planned UI and AI Work

- LINE image/OCR submission: in development.
- AI classroom scenarios from `Edu_addition.pdf`: in development.
- Admin frontend visual upgrade: continue improving the current React/Refine admin console.

Useful admin/debug endpoints:

```text
GET  /admin/overview
POST /admin/schools
GET  /admin/schools
GET  /admin/teachers
POST /admin/dev/bind-teacher
POST /admin/dev/lesson-request
POST /admin/dev/lesson-requests/{lesson_request_id}/generate-now
GET  /admin/dev/teachers/{line_user_id}/history
GET  /admin/lessons
GET  /admin/lessons/{lesson_request_id}
GET  /admin/submissions
POST /admin/submissions
GET  /admin/submissions/{submission_id}
PATCH /admin/submissions/{submission_id}
POST /admin/submissions/{submission_id}/submit
POST /admin/submissions/{submission_id}/first-approve
POST /admin/submissions/{submission_id}/second-approve
POST /admin/submissions/{submission_id}/request-revision
POST /admin/submissions/{submission_id}/reject
POST /admin/submissions/{submission_id}/publish-to-knowledge
POST /admin/knowledge/seed
GET  /admin/knowledge
GET  /admin/knowledge/{knowledge_item_id}/versions
POST /admin/knowledge/{knowledge_item_id}/reembed
POST /admin/knowledge/{knowledge_item_id}/approve-school-private
POST /admin/knowledge/{knowledge_item_id}/approve-region-shared
POST /admin/knowledge/{knowledge_item_id}/reject
POST /admin/knowledge/{knowledge_item_id}/soft-delete
POST /admin/knowledge/{knowledge_item_id}/restore/{version_number}
POST /admin/knowledge/{knowledge_item_id}/sensitive-check
POST /admin/knowledge/{knowledge_item_id}/copyright-check
POST /admin/knowledge/{knowledge_item_id}/duplicate-check
POST /admin/knowledge/{duplicate_item_id}/merge-into/{main_item_id}
POST /admin/knowledge/{knowledge_item_id}/publish
GET  /admin/publishing/candidates
POST /admin/publishing/batch
GET  /admin/coverage
GET  /admin/audit-logs
GET  /admin/dev/rag-search
POST /admin/dev/sentry-test
```

All `/admin/*` API endpoints require HTTP Basic auth using `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
Write operations also enforce role checks. `operator` can manage school/lesson operations,
`reviewer` can run knowledge review operations, and `super_admin` is required for Sentry test
events and GitHub publish execution.

## Real Integration Smoke Tests

After Supabase and GitHub credentials are configured in `.env`, create or update the database schema:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe -m alembic upgrade head
```

Run the non-LINE real integration smoke test:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_existing_apis.py
```

This verifies Supabase Postgres, RAG, lesson generation, DOCX export, Supabase Storage upload,
and private signed URL download. To also verify GitHub write permissions, run:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_existing_apis.py --github-write
```

The GitHub write smoke test publishes one temporary Markdown file and deletes it immediately
after verification.
