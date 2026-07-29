# Edu AI Assistant MVP Handoff

Last updated: 2026-07-29

## Current State

The repository now contains a Python MVP with LINE, Supabase, Gemini, Sentry, RQ worker,
teacher-submission review, and Supabase Storage end-to-end smoke paths.

## Current Checkpoint

Saved on 2026-07-29 after Refine migration, LINE real-client validation, school-admin isolation,
GitHub publish smoke, submission classification, smoke-data cleanup, and test/lint validation.

Current working state:

- Docker Desktop/WSL is available, but no app containers are required for the latest local
  validation.
- Docker Compose project name for normal runs: `edu_ai`.
- API is expected at `http://localhost:8000` when started.
- Admin UI is expected at `http://localhost:5173` when the Refine dev server is started.
- Sentry code is wired for FastAPI, SQLAlchemy, and RQ, with a development-only test event endpoint
  and host-side smoke script.
- Host-side Redis/RQ smoke passed.
- Docker container API + worker async smoke passed.
- Latest local tests: `51 passed, 1 warning`.
- Latest full lint: `ruff check app scripts tests` passed.
- Latest migration check: `alembic upgrade head` passed against a fresh project-local SQLite file
  and the configured Supabase/Postgres database. The remote Alembic version is
  `0003_admin_password_hash`, and `admin_users.password_hash` exists.

Latest progress saved in this handoff:

- LINE conversation-side language switching is implemented.
- Default teacher output language is Thai through `teachers.language_preference`.
- Bound teachers can trigger language selection through `/change language`, Thai aliases, or Malay
  aliases; selection is handled through LINE Quick Reply.
- LINE menu commands are implemented with Flex Message cards and Quick Reply shortcuts for lesson
  generation, text submission, image/OCR placeholder, AI experience placeholder, and help; recent
  lesson history returns a text list.
- Guided LINE lesson generation now asks for grade and subject through Quick Reply before asking
  for the topic; the short-lived selection state is stored in `teachers.note` with the
  `line_lesson_flow:` prefix.
- Text-submission Format/Example buttons now display instructions only and do not send `submit:`
  payloads that would create a submission.
- React/Refine Admin UI scaffold is implemented under `admin_ui/` with login, overview,
  submissions create/edit/review flow, lessons, knowledge management, a school directory with
  teachers grouped by school, operations, and audit logs.
- Refine Schools view now uses server-side school search/pagination and fetches teachers only for
  the selected school. The backend `/admin/schools` endpoint supports `limit`, `offset`, and `q`;
  `/admin/teachers` supports `limit`, `offset`, and `school_id`.
- Refine Operations page now covers school creation, teacher binding, debug lesson
  creation/generation, RAG search, knowledge coverage, and GitHub publishing candidate/dry-run/
  execute flows. Execute publish is gated by typing `PUBLISH`.
- Refine Knowledge page now covers import, sensitive/copyright/duplicate checks, approve-school,
  approve-region, reject, soft-delete, version restore, re-embed, and single-item publish actions.
- Fixed Refine login state when opening `/` unauthenticated: successful login now refreshes auth
  state even if the route path does not change.
- Added scoped `school_admin` support through `ADMIN_SCHOOL_IDS`/`ADMIN_REGION_IDS`. Scoped admins
  only see assigned schools, teachers, lessons, submissions, and accessible knowledge; cross-school
  detail access returns 403. Region/global publish operations, Sentry test, school creation, and
  region-shared approval are blocked for scoped admins.
- Added database-backed multi-account admin login through `admin_users.password_hash`. `.env`
  credentials remain as the bootstrap fallback; super admins can create school-scoped admin users
  from the Refine `Admin Users` page.
- School-admin frontend adaptation hides `Operations` and `Admin Users`; direct route access is
  redirected. Backend APIs also enforce assigned-school scope.
- School admins can manage school-private submissions/knowledge. School-admin knowledge imports are
  forced to `private_school`; region/global approval and GitHub publishing remain super-admin only.
- Super admins can see all schools and submissions, publish submissions into shared knowledge, and
  publish shared-region/shared-global knowledge items to GitHub.
- FastAPI CORS now allows the local Vite dev origins configured by `CORS_ALLOW_ORIGINS`.
- User-entered menu/action aliases can be detected across Thai, Local Malay, and English; internal
  Rich Menu commands remain stable as `/menu_*`.
- Lesson generation still exports Thai, Local Malay, and English DOCX files, but LINE completion
  messages now send only the teacher's selected language link.
- Per-language Rich Menu linking is supported when `LINE_RICH_MENU_ID_TH`,
  `LINE_RICH_MENU_ID_MS`, and `LINE_RICH_MENU_ID_EN` are configured.
- `scripts/generate_line_rich_menu_assets.py` generated three 2x3 Rich Menu PNG assets under
  `data/line/`.
- `scripts/setup_line_rich_menu.py` created/uploaded three LINE Rich Menus and the created IDs are
  configured in local `.env`.
- Fixed per-user Rich Menu linking to use `https://api.line.me/v2/bot/user/{userId}/richmenu/{id}`;
  the upload API still uses `api-data.line.me`.
- Verified direct English Rich Menu linking for the active test LINE user after the fix.
- Verified after this work: backend `51 passed, 1 warning`; backend `ruff check app scripts tests`
  passed; frontend `npm run lint`, `npm run build`, and `npm audit --omit=dev` passed; Playwright
  full button smoke passed for Refine login, Operations school/teacher/lesson/RAG/GitHub/Sentry,
  School Directory, lesson detail, submissions create/edit/revision/reject/publish, Knowledge
  import/check/approve/restore/reembed/publish/reject/soft-delete, and Audit Logs refresh.
- Real LINE client flow was exercised for binding, language switching, Rich Menu lesson generation,
  queue/worker processing, DOCX upload, and LINE push. Redis must be running and host-side Windows
  workers now use RQ `SimpleWorker`.
- A real GitHub publish smoke wrote a small shared-region knowledge Markdown file to
  `Candymoon0627/summer_school`, verified it through the GitHub API, and later cleaned it up.
- The retained Pattani MVP seed batch has now been published to GitHub: 80 embedded knowledge items,
  split `math:40` and `science:40`, with `pending_github=0`. A GitHub API sample read returned 200
  for
  `knowledge/countries/th/regions/8616f9ac-dc61-4b23-b5c9-6507b3ad2e6c/science/grade-3-5/weather-weather-observation-test-item-4-96238704.md`.
- Smoke/UI/Isolation test schools, teachers, lessons, submissions, knowledge, admin users, DOCX
  media rows/files, and GitHub smoke Markdown files were cleaned. A dry-run after cleanup matched
  zero rows/files in that test-data scope.

Resume from here:

1. Keep LINE image/OCR submission and `Edu_addition.pdf` AI classroom scenarios marked as in
   development unless they become part of the next scope.
2. For a real pilot, replace/review the synthetic Pattani seed knowledge before treating the GitHub
   corpus as production content.
3. Add durable production hosting/tunnel; current Cloudflare quick tunnel is temporary.
4. Before a public pilot, rotate any credentials that were exposed during setup and keep `.env`
   private.

If Docker images need to be rebuilt on this Windows workspace, use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_docker_images.ps1
docker compose -p edu_ai up -d --no-build api worker
```

Runtime environment:

- Workspace: `C:\Users\Lenovo\Desktop\新建文件夹`
- Python venv: `D:\venvs\edu-ai-assistant`
- Main command prefix: `D:\venvs\edu-ai-assistant\Scripts\python.exe`
- `.env` exists locally and contains real credentials. It is ignored by git.

## Implemented

- FastAPI app shell and admin/debug API routes.
- SQLAlchemy models for organizations, teachers, LINE bindings, lessons, media, knowledge, feedback,
  audits, consent, duplicates, and usage.
- Alembic initial schema plus `0002_submissions` for teacher submissions and reviews.
- Supabase Postgres connection through Supabase pooler.
- School creation and invitation-code teacher binding.
- Mock and Gemini lesson request parsing/generation.
- DOCX export for generated lesson plans.
- Supabase Storage upload, signed URL generation, and delete.
- Knowledge seed import, version snapshot, review status changes, soft delete, restore, and re-embed.
- Mock embedding provider and filtered RAG retrieval.
- Gemini text model provider using `google-genai`.
- Gemini embedding provider using `gemini-embedding-2`.
- Lightweight sensitive/copyright checks.
- Duplicate detection and admin merge.
- GitHub Markdown rendering, validation, first publish, and existing-file update.
- GitHub real write smoke test with cleanup.
- RQ async smoke script for Redis-backed lesson generation (`scripts/smoke_rq_async.py`).
- Docker Compose Redis URL override for container-to-container queue access.
- Docker build context cleanup through `.dockerignore`.
- Clean Docker image build helper for Windows (`scripts/build_docker_images.ps1`).
- Sentry SDK initialization for API and worker, plus a dev smoke endpoint/script.
- LINE webhook, invitation-code binding, queued lesson generation, and completion push.
- LINE language preference with Thai default, `/change language` Quick Reply selection, Thai/Local
  Malay/English command aliases, and optional per-language Rich Menu linking.
- LINE menu command handling for lesson generation, text submission, image/OCR placeholder,
  AI experience placeholder, recent lesson history, and help.
- LINE text submission detection through `投稿:` / `投稿：` / `submit:` / `submission:` prefixes.
- LINE image/file submission currently returns an "under development" message.
- Pattani seed knowledge YAML with 80 Thai-first math/science MVP test items.
- Remote seed RAG lesson smoke script with knowledge-reference verification.
- Trilingual lesson schema, Gemini prompt, separate Thai/Malay/English DOCX exports, and LINE
  completion summary/link selection based on teacher language preference.
- GitHub readiness and batch publish dry-run tooling.
- Dry-run-first automatic smoke data cleanup tooling.
- Lesson generation failure handling: failed jobs update lesson status/error; LINE notification
  failures do not flip completed jobs to failed.
- Refine admin dashboard for overview metrics, school/teacher management, lesson inspection,
  submission review, knowledge review, publishing dry-runs/guarded execute, RAG checks, coverage,
  audit logs, and admin user management.
- Admin API endpoints for overview, lesson list/detail, knowledge versions, and batch publishing.
- Admin API endpoints for submission list/detail/create/edit, submit, first approve, second approve,
  request revision, reject, and publish-to-knowledge.
- Admin authentication/authorization through database-backed admin users plus `.env` bootstrap
  credentials. FastAPI `/admin/*` routes require HTTP Basic auth; Refine Admin requires login
  before rendering dashboard content. Write operations are role-gated and scoped by school where
  applicable.
- Two-stage teacher submission state machine:
  `draft -> pending_review -> first_approved -> second_approved -> embedded`, with
  `needs_revision` and `rejected` exception paths.
- Approved submissions create `KnowledgeItem` records and active RAG chunks through the existing
  knowledge/embedding services.
- Local tests for the core non-LINE flows.

## Important Files

- Architecture notes: `MVP_Architecture.md`
- App entrypoint: `app/api/main.py`
- Admin routes: `app/api/routes/admin.py`
- Settings: `app/core/config.py`
- Database session: `app/db/session.py`
- Initial migration: `app/db/migrations/versions/0001_initial_schema.py`
- Submission migration: `app/db/migrations/versions/0002_submissions.py`
- Storage service: `app/services/storage.py`
- GitHub publishing service: `app/services/publishing.py`
- Lesson generation: `app/services/lesson_generation.py`
- LINE language/menu text: `app/services/language.py`
- LINE webhook command handling: `app/services/line_webhook.py`
- LINE messaging and Rich Menu linking: `app/services/line_messaging.py`
- Knowledge service: `app/services/knowledge.py`
- Submission service: `app/services/submissions.py`
- Submission repository: `app/repositories/submission.py`
- Submission models: `app/db/models/submission.py`
- RAG service: `app/services/rag.py`
- Real integration smoke script: `scripts/smoke_existing_apis.py`
- README commands: `README.md`
- Gemini provider: `app/services/model_providers/gemini.py`
- First test seed knowledge: `data/seed_knowledge/pattani_test_80.yaml`
- Remote seed lesson smoke: `scripts/smoke_remote_seed_lesson.py`
- GitHub readiness: `scripts/check_github_readiness.py`
- GitHub batch publish: `scripts/publish_knowledge_batch.py`
- Smoke data cleanup: `scripts/cleanup_smoke_data.py`
- LINE Rich Menu asset generation: `scripts/generate_line_rich_menu_assets.py`
- LINE Rich Menu setup: `scripts/setup_line_rich_menu.py`
- Refine Admin UI: `admin_ui/`

## Verified

Local tests:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe -m pytest -q
```

Latest result:

```text
51 passed, 1 warning
```

On this Windows machine, pytest may fail when it tries to use the default temp path. Use a fresh
project-local temp directory when running tests:

```powershell
$base = Join-Path (Resolve-Path .).Path ('.pytest_run_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $base | Out-Null
$env:TEMP = $base
$env:TMP = $base
D:\venvs\edu-ai-assistant\Scripts\python.exe -m pytest -q --basetemp $base -o cache_dir=$base\cache
```

Gemini text provider smoke:

```text
ACTIVE_TEXT_MODEL_PROVIDER=gemini
ACTIVE_TEXT_MODEL_NAME=gemini-3.6-flash
```

Verified real Gemini structured lesson generation. `gemini-2.5-flash` returned `404 NOT_FOUND`
for this API key because it is no longer available to new users; use `gemini-3.6-flash`.

Gemini embedding provider smoke:

```text
ACTIVE_EMBEDDING_PROVIDER=gemini
ACTIVE_EMBEDDING_MODEL=gemini-embedding-2
ACTIVE_EMBEDDING_DIMENSIONS=3072
```

Verified real Gemini embedding generation: returned a 3072-dimensional vector.

Local full non-async smoke using SQLite + local storage passed with real Gemini text and embedding:

- School code created.
- Teacher bound.
- Seed knowledge imported as `approved_region_shared`.
- Knowledge chunk embedded with provider `gemini`, model `gemini-embedding-2`, dimensions `3072`.
- RAG returned `medium` confidence with one matching item.
- Lesson generation completed with real Gemini.
- DOCX media asset record created.

Database migration:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe -m alembic upgrade head
```

Latest local result: passed against a fresh project-local SQLite file.

Latest remote result: passed against the configured Supabase/Postgres database. Read-only
verification returned Alembic version `0003_admin_password_hash` and confirmed `submissions`,
`submission_reviews`, and `admin_users.password_hash` exist.

Teacher submission/review tests verified:

- Admin-created submission can be submitted for review.
- Publishing before second review is blocked.
- First review and second review advance the state machine.
- Publish-to-knowledge creates a `KnowledgeItem` and active RAG chunk.
- Bound LINE teachers can create text submissions with `投稿:` / `submit:` prefixes.
- LINE text submissions now attempt grade/subject/topic classification before falling back to
  `general` and `grade 1-12`; for example `Grade 4 fractions...` becomes `math`, `fractions`,
  `grade 4`.
- Admin API list/detail/action endpoints are covered.

## LINE Navigation Plan

Current state:

- Use LINE Rich Menu as the persistent bottom navigation, similar to a Telegram bot command menu.
- Use Quick Reply only for temporary, contextual choices after a bot message.
- First Rich Menu layout should use 6 areas: Generate Lesson, Text Submission, Image Submission,
  AI Experience, My History, and Help.
- Rich Menu tap actions should send fixed text commands to the webhook:

```text
/menu_lesson
/menu_submit_text
/menu_submit_image
/menu_ai_experience
/menu_history
/menu_help
```

- Current webhook behavior:

- `/menu_lesson`: implemented; replies with a Flex card that starts the guided flow:
  choose grade -> choose subject -> type topic.
- `/menu_submit_text`: implemented; replies with a Flex card containing text-submission format,
  example/format instruction buttons that do not create submissions, and navigation shortcuts.
- `/menu_submit_image`: implemented; replies with a Flex card explaining image/OCR is in
  development and routes teachers to text submission/help.
- `/menu_ai_experience`: implemented; replies with a Flex card explaining AI classroom experience
  is in development and routes teachers to lesson generation/help.
- `/menu_history`: implemented; returns recent lesson-request history. Submission history can be
  added later.
- `/menu_help`: implemented; replies with a Flex card linking to common actions and language
  selection.

Language behavior:

- Teachers default to Thai output through `teachers.language_preference`.
- Bound teachers can send `/change language`, `เปลี่ยนภาษา`, or `tukar bahasa`.
- The bot replies with Quick Reply choices: Thai, Local Malay, and English.
- Exact language selections such as `ไทย`, `Bahasa Melayu`, and `English` update the teacher
  preference.
- LINE text replies and lesson completion notifications use the selected language.
- Lesson generation still creates Thai, Local Malay, and English DOCX assets, but the LINE
  completion message only sends the selected language's DOCX link.
- `LineMessagingService.link_rich_menu_for_language()` links a user to a per-language Rich Menu if
  `LINE_RICH_MENU_ID_TH`, `LINE_RICH_MENU_ID_MS`, or `LINE_RICH_MENU_ID_EN` is configured.

LINE Rich Menu implementation status:

1. Generated 2x3 template image assets for Thai, Local Malay, and English under `data/line/`.
2. Created and uploaded all three Rich Menus through the LINE Messaging API.
3. Set the Thai Rich Menu as the default.
4. Configured the created IDs in local `.env` as `LINE_RICH_MENU_ID_TH`,
   `LINE_RICH_MENU_ID_MS`, and `LINE_RICH_MENU_ID_EN`.
5. Remaining manual check: use the real LINE Official Account client to verify button taps and
   language-specific menu switching.

Real non-LINE smoke test:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_existing_apis.py
```

Verified:

- Supabase Postgres write/read.
- School creation.
- Teacher binding.
- Knowledge import and embedding.
- RAG search.
- Mock lesson generation.
- DOCX export.
- Supabase Storage upload.
- Signed URL download from private bucket.

GitHub write smoke test:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_existing_apis.py --github-write
```

Verified:

- GitHub Markdown publish.
- Temporary file deletion.

Note: GitHub repository history will still contain create/delete commits from smoke tests.

Redis/RQ async smoke:

```powershell
docker compose -p edu_ai up -d redis
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_rq_async.py
```

Verified:

- Redis reachable on `redis://localhost:6379/0`.
- Lesson request enqueued to RQ with returned `queue_job_id`.
- RQ worker executed `app.worker.jobs.generate_lesson_job`.
- Lesson request reached `completed`.
- DOCX media asset was created.

Docker Compose API + worker async smoke:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_docker_images.ps1
docker compose -p edu_ai up -d --no-build api worker
```

Verified through HTTP debug endpoints:

- `GET /admin/status` returned `{"api":"ok","worker":"configured","sentry":"configured"}`.
- `POST /admin/dev/lesson-request?...&enqueue=true` returned a queue job id.
- Worker container consumed the job from Redis and completed the lesson request.
- Worker logs showed successful Gemini embedding, Gemini text generation, and Supabase Storage upload.
- Redis queue length returned to `0`.

Remote seed RAG lesson smoke:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_remote_seed_lesson.py --batch-id pattani-test-v1-80 --subject science --grade 4 --topic "water cycle"
```

Verified:

- Seed batch `pattani-test-v1-80` available in Supabase with 80 items and 80 active chunks.
- RAG returned `high` confidence.
- Gemini generated a lesson with model metadata `gemini:gemini-3.6-flash`.
- `lesson_knowledge_refs` recorded 8 references to the seed batch.
- DOCX uploaded to Supabase Storage and signed download returned bytes.

Trilingual lesson output smoke:

- Gemini returned structured `title_trilingual`, `summary_trilingual`, and
  `lesson_flow_trilingual` fields.
- DOCX export creates three separate files with purposes `lesson_docx_th`, `lesson_docx_ms`, and
  `lesson_docx_en`.
- DOCX styles explicitly set Tahoma for `eastAsia` and `cs` font slots to reduce Thai rendering
  issues in Word/WPS.
- Docker `api` and `worker` were restarted after the trilingual prompt/schema change.

LINE request parsing:

- Does not require a fixed English phrase.
- Supports English examples like `Grade 4 science water cycle`.
- Supports Thai examples like `ขอแผนการสอน ป.4 วิทยาศาสตร์ เรื่องวัฏจักรน้ำ` and
  `ป.4 คณิตศาสตร์ เศษส่วน`.
- Supports Chinese examples like `四年级数学 分数`.

GitHub readiness and batch publish dry-run:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\check_github_readiness.py
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\publish_knowledge_batch.py --region pattani --limit 10
```

Verified:

- GitHub repo/token configured and repo accessible.
- `.env` is ignored.
- Batch publish dry-run lists candidates and warnings without writing to GitHub.
- Real publish blocks warning candidates unless explicitly overridden.
- Real batch publish was run for the retained Pattani MVP seed data with explicit
  `--allow-test-data --allow-warnings --execute`; database verification showed 80 GitHub paths and
  `pending_github=0`.

Admin dashboard/API validation:

```powershell
curl.exe -sS -i http://127.0.0.1:8000/admin/status
curl.exe -sS -u "$env:ADMIN_USERNAME`:$env:ADMIN_PASSWORD" http://127.0.0.1:8000/admin/me
curl.exe -sS -u "$env:ADMIN_USERNAME`:$env:ADMIN_PASSWORD" http://127.0.0.1:8000/admin/overview
curl.exe -sS -u "$env:ADMIN_USERNAME`:$env:ADMIN_PASSWORD" "http://127.0.0.1:8000/admin/lessons?limit=3"
curl.exe -sS -I http://127.0.0.1:5173
```

Verified:

- `/admin/status` returned `{"api":"ok","worker":"configured","sentry":"configured"}`.
- Unauthenticated `/admin/status` returned `401 Admin authentication required`.
- Authenticated `/admin/me` returned user `admin` with role `super_admin`.
- `/admin/overview` returned remote Supabase counts and status buckets.
- `/admin/lessons` returned recent lesson request rows.
- Refine Admin returned HTTP 200 on port 5173.
- Docker containers `api`, `worker`, `redis`, and `postgres` are running, with host ports
  bound to `127.0.0.1` only.
- There is one legacy lesson request still marked `running` from earlier smoke testing; the current
  worker is healthy and no new worker error was found in logs.
- LINE official webhook test still passed after admin auth and port binding changes.

Smoke data cleanup dry-run:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\cleanup_smoke_data.py
```

Latest dry-run after cleanup matched automatic smoke rows only:

- 0 schools.
- 0 teachers.
- 0 lessons.
- 0 media assets.

Remote database currently still contains manual/non-matched data:

- 3 schools.
- 3 teachers.
- 5 completed lesson requests.
- 7 lesson media assets.

## Supabase Notes

The direct database host `db.bcxoqkllogrixarahsry.supabase.co` resolved only to IPv6 on this machine.
The project was changed to use the Supabase pooler host instead:

```text
aws-0-ap-southeast-1.pooler.supabase.com:6543
```

This passed `select 1` through both raw `psycopg` and the app SQLAlchemy engine.

Storage bucket:

```text
lesson-files
```

The bucket is private. The app generates signed URLs on the server for downloads.

## Current `.env` Requirements

Already configured locally:

- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_STORAGE_BUCKET`
- `GITHUB_REPO`
- `GITHUB_TOKEN`
- `GITHUB_BRANCH`
- `LINE_CHANNEL_ID`
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `SENTRY_DSN`
- `ADMIN_AUTH_ENABLED`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_ROLE`

Optional:

- `SENTRY_TRACES_SAMPLE_RATE` defaults to `0.05`.
- `DEEPSEEK_API_KEY` and `QWEN_API_KEY` are optional alternative model keys and are not required
  for the current Gemini-backed MVP path.

Gemini is currently configured locally in `.env`:

```text
ACTIVE_TEXT_MODEL_PROVIDER=gemini
ACTIVE_TEXT_MODEL_NAME=gemini-3.6-flash
ACTIVE_EMBEDDING_PROVIDER=gemini
ACTIVE_EMBEDDING_MODEL=gemini-embedding-2
ACTIVE_EMBEDDING_DIMENSIONS=3072
GEMINI_API_KEY=<set locally>
```

## Security Notes

The GitHub token, Supabase secret key, and Gemini API key were pasted into chat during setup. Treat
them as exposed.
Before any real pilot or public deployment:

- Rotate the GitHub token.
- Rotate the Supabase secret/service key if possible.
- Rotate the Gemini API key.
- Keep `.env` out of GitHub.
- Use only server-side code for Supabase secret keys.

## Known Test Data

Smoke/UI/Isolation test data was cleaned on 2026-07-29:

- Smoke/UI/Isolation schools and teachers.
- Smoke/UI/Isolation lesson requests and generated DOCX media records.
- Smoke/UI/Isolation submissions and derived knowledge items.
- The two temporary school-admin accounts created for isolation testing.
- GitHub smoke Markdown files under `knowledge/...`.
- Matching Supabase Storage DOCX files.

A dry-run immediately after cleanup matched zero rows/files in that scope. The Pattani seed
knowledge batch is intentionally retained as baseline MVP RAG content and is published to GitHub.

## Next Recommended Steps

1. Keep LINE image/OCR submission and `Edu_addition.pdf` AI classroom scenarios marked as
   in development unless they become part of the next scope.
2. For a real pilot, replace/review the synthetic Pattani seed knowledge before treating the GitHub
   corpus as production content.
3. Add durable production tunnel/deployment; current Cloudflare quick tunnel is temporary.
4. Rotate exposed credentials before a public pilot and keep `.env` private.

## Docker Notes

Docker Desktop/WSL was fixed on 2026-07-28 after starting the Windows services from an Administrator
PowerShell and launching Docker Desktop. Confirmed service/container state:

```text
com.docker.service Running
WSLService         Running
vmcompute          Running
hns                Running
```

Use an explicit compose project name because the workspace path contains non-ASCII characters:

```powershell
docker compose -p edu_ai ps
```

The project `.env` keeps `REDIS_URL=redis://localhost:6379/0` for host-side scripts. `docker-compose.yml`
overrides `REDIS_URL=redis://redis:6379/0` for `api`, `worker`, and `admin` containers.

Latest Docker note on 2026-07-29: `.env` currently points `DATABASE_URL` to an external/remote
database, so do not start the full compose stack and assume it is local unless `DATABASE_URL` is
overridden. A local compose validation attempt also hit a host `127.0.0.1:6379` port conflict and
left containers without a normal compose network attachment; the temporary `postgres` and `redis`
containers started during that attempt were stopped. Local unit tests and a fresh SQLite Alembic
migration check passed.

Docker build from the workspace may fail if stale `.pytest_run_*` directories exist. `.dockerignore`
now excludes those directories, and `scripts\build_docker_images.ps1` builds `edu_ai-api`
and `edu_ai-worker` from a clean temporary context. Use `docker compose -p edu_ai up
-d --no-build ...` after running the script.

## Useful Commands

Run tests:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe -m pytest -q
```

Run migrations:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe -m alembic upgrade head
```

Run API locally:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe -m uvicorn app.api.main:app --reload --port 8000
```

Run Refine admin:

```powershell
cd admin_ui
npm run dev
```

Run real non-LINE smoke:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_existing_apis.py
```

Run GitHub write smoke:

```powershell
D:\venvs\edu-ai-assistant\Scripts\python.exe scripts\smoke_existing_apis.py --github-write
```
