# Edu AI Assistant

Edu AI Assistant is a LINE-based lesson planning and local knowledge system for teachers.
It helps teachers request localized lesson plans, receive DOCX outputs, contribute classroom
knowledge, and reuse approved knowledge through retrieval-augmented generation.

The current implementation is a working monorepo with a FastAPI backend, RQ worker, React/Refine
admin console, PostgreSQL/pgvector data model, LINE webhook integration, DOCX export, model-provider
abstractions, local/Supabase storage support, and GitHub publishing for reviewed shared knowledge.

## What It Does

- Accepts teacher lesson requests through LINE or admin debug tools.
- Generates structured lesson plans with Thai-first content plus Local Malay and English helper text.
- Exports separate Thai, Local Malay, and English DOCX lesson files.
- Stores lesson requests, generated content, media assets, teacher feedback, and RAG references.
- Lets teachers submit local examples, term explanations, and classroom activities as text.
- Supports two-stage admin review before approved submissions become knowledge items.
- Embeds approved knowledge into pgvector and retrieves it with metadata-aware RAG filters.
- Publishes approved `shared_region` and `shared_global` Markdown knowledge to a GitHub repository.
- Keeps `private_school` knowledge in the database and vector store without publishing it to GitHub.
- Provides a React/Refine admin console for schools, teachers, lessons, submissions, knowledge,
  publishing operations, coverage checks, audit logs, and admin users.

## Architecture

```text
LINE Official Account
  -> FastAPI webhook and admin API
  -> PostgreSQL with pgvector
  -> Redis / RQ worker
  -> model providers: mock, Gemini, DeepSeek, Qwen
  -> DOCX export
  -> local or Supabase object storage
  -> LINE reply / push messages

React / Refine admin console
  -> FastAPI admin endpoints
  -> review, publishing, RAG, coverage, audit, and user-management workflows

GitHub knowledge repository
  -> reviewed shared_region / shared_global Markdown knowledge only
```

## Repository Layout

```text
app/
  api/                 FastAPI app and route modules
  core/                configuration, logging, security, Sentry, admin auth
  db/                  SQLAlchemy models and Alembic migrations
  prompts/             versioned prompts
  repositories/        database access layer
  schemas/             Pydantic request/response schemas
  services/            lesson generation, RAG, review, publishing, storage, LINE services
  worker/              RQ worker entrypoint and jobs

admin_ui/              React + Refine + MUI admin console
data/seed_knowledge/   seed knowledge YAML batches
data/line/             LINE Rich Menu image assets
knowledge/             exported Markdown knowledge files for GitHub publishing
scripts/               setup, smoke, seed, cleanup, publishing, and LINE helper scripts
tests/                 backend test suite
```

## Local Setup

Prerequisites:

- Python 3.11+
- Docker Desktop
- Node.js 20+ for the admin console

Create local environment settings:

```powershell
Copy-Item .env.example .env
```

For local development, keep the mock providers:

```env
ACTIVE_TEXT_MODEL_PROVIDER=mock
ACTIVE_TEXT_MODEL_NAME=mock-lesson-v1
ACTIVE_EMBEDDING_PROVIDER=mock
ACTIVE_EMBEDDING_MODEL=mock-embedding-v1
ACTIVE_EMBEDDING_DIMENSIONS=8
```

For Gemini-backed text generation and embeddings:

```env
ACTIVE_TEXT_MODEL_PROVIDER=gemini
ACTIVE_TEXT_MODEL_NAME=gemini-3.6-flash
ACTIVE_EMBEDDING_PROVIDER=gemini
ACTIVE_EMBEDDING_MODEL=gemini-embedding-2
ACTIVE_EMBEDDING_DIMENSIONS=3072
GEMINI_API_KEY=your-key
```

Install backend dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Start Postgres, Redis, API, and worker:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_docker_images.ps1
docker compose -p edu_ai up -d --no-build api worker
```

Use the explicit `-p edu_ai` project name on Windows because non-ASCII workspace paths can break
Docker Compose's automatic project-name detection.

Services:

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

Create or update the database schema:

```powershell
python -m alembic upgrade head
```

Seed initial system data:

```powershell
python scripts\seed_system.py
```

## Admin Console

Run the React admin console:

```powershell
cd admin_ui
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The admin UI calls `http://127.0.0.1:8000` by default. Override it with:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Authentication uses database-backed admin users when available, with the `.env` bootstrap admin as
the local fallback:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-before-use
ADMIN_ROLE=super_admin
```

Supported roles include `viewer`, `operator`, `reviewer`, `school_admin`, and `super_admin`.
Scoped school admins can only see and mutate records for assigned schools, and cannot run global
publishing or other unscoped operations.

## LINE Integration

Configure LINE credentials in `.env`:

```env
LINE_CHANNEL_ID=
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_RICH_MENU_ID_TH=
LINE_RICH_MENU_ID_MS=
LINE_RICH_MENU_ID_EN=
```

Rich Menu buttons should send these stable commands:

```text
/menu_lesson
/menu_submit_text
/menu_submit_image
/menu_ai_experience
/menu_history
/menu_help
```

Generate Rich Menu image assets:

```powershell
python scripts\generate_line_rich_menu_assets.py
```

Create and upload the three Rich Menus:

```powershell
python scripts\setup_line_rich_menu.py `
  --th-image data\line\rich_menu_th.png `
  --ms-image data\line\rich_menu_ms.png `
  --en-image data\line\rich_menu_en.png `
  --set-default th
```

Teachers bind to a school by sending an invitation code. After binding, they can request a lesson,
change language, view recent lesson history, or submit local knowledge text. Image/OCR submission
and AI classroom scenarios are intentionally represented as under-development flows in this version.

## Knowledge and RAG

Seed knowledge files live in `data/seed_knowledge/*.yaml`. Import all seed YAML files:

```powershell
python scripts\import_seed_knowledge.py
```

Import only the Pattani 80-item test batch:

```powershell
python scripts\import_seed_knowledge.py --file data\seed_knowledge\pattani_test_80.yaml
```

Run a remote end-to-end check against the imported seed batch:

```powershell
python scripts\smoke_remote_seed_lesson.py --batch-id pattani-test-v1-80 --subject science --grade 4 --topic "water cycle"
```

The check verifies imported knowledge, RAG retrieval, lesson generation, stored
`lesson_knowledge_refs`, object-storage upload, and signed DOCX download.

## GitHub Knowledge Publishing

GitHub publishing is only for reviewed shared knowledge. School-private knowledge remains in the
application database and vector store.

Configure:

```env
GITHUB_REPO=owner/repo
GITHUB_TOKEN=your-fine-grained-token
GITHUB_BRANCH=main
```

Check readiness:

```powershell
python scripts\check_github_readiness.py
```

Dry-run publish candidates:

```powershell
python scripts\publish_knowledge_batch.py --region pattani --limit 20
```

Inspect synthetic test candidates:

```powershell
python scripts\publish_knowledge_batch.py --region pattani --allow-test-data --limit 20
```

Real publishing requires `--execute`. Use `--allow-warnings` only after manually reviewing the
candidate warnings.

Published Markdown is written under paths like:

```text
knowledge/countries/th/regions/<region-id>/<subject>/<grade>/<slug>.md
```

## Useful Local Commands

Run tests:

```powershell
pytest
```

Run lint:

```powershell
ruff check .
```

Clean automatically generated smoke data:

```powershell
python scripts\cleanup_smoke_data.py --execute
```

Clean the Pattani seed batch:

```powershell
python scripts\cleanup_seed_knowledge.py --batch-id pattani-test-v1-80
```

Build the admin UI:

```powershell
cd admin_ui
npm run build
```

## Runtime Integrations

- Database: PostgreSQL with pgvector, local Docker or Supabase Postgres.
- Queue: Redis with RQ worker.
- Storage: local filesystem for development, Supabase Storage for real DOCX assets.
- Models: mock provider for local tests, Gemini/DeepSeek/Qwen provider hooks for real generation.
- LINE: official account webhook and messaging API.
- Observability: optional Sentry integration.
- GitHub: optional publishing target for reviewed shared Markdown knowledge.

## Documentation Notes

The files intended for a public or team-facing repository are source code, tests, scripts,
configuration examples, `README.md`, `LICENSE`, prompt templates, seed data, LINE assets, and
published shared knowledge under `knowledge/`.

Internal handoff notes, early planning documents, working PDFs, generated local data, smoke outputs,
cache directories, and secret-bearing environment files should stay out of GitHub unless the team
explicitly decides to publish them.
