# MVP Architecture: AI Localized Lesson Plan Assistant

更新时间：2026-07-25

本文是 `Edu.md` 的 MVP 执行版架构文档。`Edu.md` 保留为项目背景、调研和原始方案；本文记录已经确认的 MVP 范围、架构决策、实现分层、外部资源准备清单和开发里程碑。

## 1. MVP 目标

MVP 目标不是只做演示聊天机器人，而是做一个真实可用的最小知识闭环：

```text
教师通过 LINE 输入教案需求或投稿知识
  -> 系统生成结构化教案并返回 DOCX
  -> 教师投稿本地案例 / 术语解释 / 课堂活动
  -> 管理员审核
  -> 学校私有知识进入本校 RAG
  -> 地区/全局共享知识发布到 GitHub
  -> embedding 写入 pgvector
  -> 后续教案生成可检索使用
```

第一阶段定位为封闭试用 MVP，优先服务少量真实教师，不追求完整平台化。

## 2. 已确认 MVP 范围

### 2.1 真实实现

- LINE Official Account 教师入口。
- 学校邀请码绑定教师。
- 首次使用隐私/AI 使用同意。
- 自然语言教案需求输入，缺字段时追问。
- 异步教案生成。
- 内部保存 `structured_content JSONB + rendered_markdown`。
- 返回 LINE 文本预览 + DOCX 下载链接。
- 教师查看最近 5 条历史教案，并可重新获取 DOCX 链接。
- 教师轻量反馈：有用 / 需要修改 / 不适合。
- 教师投稿：
  - `local_example`
  - `term_explanation`
  - `teaching_activity`
- Streamlit 管理后台。
- 学校私有单审，地区/全局共享双审。
- 敏感内容、版权风险、重复内容自动初筛，最终由人工确认。
- 知识版本记录和历史版本恢复。
- 知识软删除和恢复。
- RAG：metadata hard filter + pgvector similarity + 简单 rerank。
- RAG 引用记录和低置信度提示。
- 地区/全局共享知识发布到 GitHub private repo。
- 后端直接 commit GitHub main，并由后端完成 embedding 同步。
- Redis Queue / RQ 异步任务。
- Supabase Postgres + pgvector。
- Supabase Storage 或 S3-compatible Storage，用于 DOCX。
- Sentry 错误追踪。
- 结构化日志、健康检查、后台状态页。
- Docker 化，本地 `docker compose`。
- 基础 CI/CD。

### 2.2 只预留接口或状态

- 图片识别/OCR。
- 教材/PDF/试卷/电子书上传。
- 完整教案投稿。
- GitHub PR 发布流程。
- GitHub Actions embedding 主流程。
- 独立学校数据库。
- PostgreSQL RLS。
- 正式 React/Next.js 后台。
- 自动随机 A/B 分流。
- PDF 导出。

## 3. 非目标 Non-goals

MVP 第一版明确不做：

- 图片识别/OCR 真实实现。
- PDF 导出。
- 教材/PDF/试卷/电子书上传真实实现。
- 完整教案投稿真实实现。
- GitHub PR 工作流作为主发布流程。
- GitHub Actions 作为 embedding 主流程。
- 完整 hybrid search / BM25 / 多语言分词。
- 正式 React/Next.js 后台。
- 自动随机 A/B 分流。
- 多仓库拆分。
- 每个学校独立数据库。
- 完整 PostgreSQL RLS。
- 教师端复杂编辑已审核投稿。
- 教师自助删除已审核共享内容。
- 复杂客服系统。
- 批量 LINE 主动推送公告。
- 积分、排行榜、贡献者认证。
- 本地部署 Qwen。

## 4. 技术总架构

```text
LINE Official Account
  -> FastAPI Webhook/API
  -> PostgreSQL: Supabase Postgres + pgvector
  -> Redis Queue: RQ Worker
  -> Model Providers: Gemini / DeepSeek / Qwen configurable
  -> DOCX Export
  -> Object Storage
  -> LINE Push Message

Streamlit Admin
  -> FastAPI Admin API / service layer
  -> PostgreSQL
  -> GitHub Publisher
  -> Embedding Sync
  -> Audit Logs
  -> Sentry

GitHub private repo
  -> stores shared_region / shared_global Markdown only
```

核心原则：

- PostgreSQL 是业务真相来源。
- Redis 只负责队列、短期会话、限流和临时缓存。
- GitHub 只保存地区/全局共享的审核后 Markdown 知识库。
- 学校私有知识不写 GitHub。
- 文件本体放对象存储，数据库只保存 `object_key` 和元数据。
- Streamlit 只做后台 UI，业务逻辑放 service 层。

## 5. 部署形态

生产/试点环境拆三个独立服务：

```text
api-service       FastAPI
worker-service    RQ Worker
admin-service     Streamlit
```

本地开发用 `docker compose` 一键启动。

推荐托管组合：

```text
PostgreSQL + pgvector: Supabase
Object Storage: Supabase Storage, later swappable to R2/S3
Redis: Upstash Redis
API/Worker/Admin: Render / Railway / Fly.io
Error tracking: Sentry
GitHub: private repo + fine-grained token
```

环境分层：

```text
development
staging
production
```

建议测试 LINE channel 和正式 LINE channel 分离。

## 6. 代码仓库结构

MVP 使用单仓库 monorepo。后期可按目录边界拆分多仓库。

```text
edu-ai-assistant/
  app/
    api/
      main.py
      routes/
      dependencies.py

    admin/
      main.py
      pages/

    worker/
      main.py
      jobs/

    core/
      config.py
      security.py
      logging.py

    db/
      session.py
      models/
      migrations/

    services/
      lesson_generation.py
      rag.py
      knowledge.py
      review.py
      publishing.py
      storage.py
      model_providers/
      docx_export.py
      sensitivity.py
      copyright.py
      usage.py
      audit.py

    repositories/
      teachers.py
      schools.py
      knowledge.py
      lessons.py
      submissions.py

    schemas/
      lesson.py
      knowledge.py
      review.py

    prompts/
      lesson_generation_v1.md
      parse_lesson_request_v1.md
      sensitive_check_v1.md
      copyright_check_v1.md
      knowledge_structuring_v1.md

    templates/
      lesson_docx/
      markdown/

  data/
    seed_knowledge/

  tests/
  scripts/
  docker-compose.yml
  Dockerfile
  pyproject.toml
  .env.example
```

约束：

- API routes 不写核心业务流程，只调用 services。
- Worker jobs 只取 ID，业务处理调用 services。
- Streamlit 不直接写复杂业务逻辑。
- 数据库访问集中在 repositories。
- Prompt 文件版本化。
- Model provider 可替换。

## 7. 数据隔离与多租户

MVP 采用共享 PostgreSQL + 逻辑隔离。

含义：

```text
所有地区和学校共用一个 PostgreSQL。
每条业务数据带 region_id / school_id / visibility_scope。
所有查询通过权限过滤返回允许访问的数据。
```

MVP 不做独立学校数据库，但预留 `tenant_id`。

核心表：

```text
regions
districts
schools
teachers
admin_users
teacher_consents
consent_versions
lesson_requests
lesson_feedback
support_tickets
submissions
knowledge_items
knowledge_item_versions
knowledge_chunks
lesson_knowledge_refs
media_assets
audit_logs
model_call_logs
usage_counters
feature_flags
line_events
line_message_deliveries
```

### 7.1 地区和学校

```text
regions
- id
- country_code
- name
- code
- active

districts
- id
- region_id
- name
- code
- active

schools
- id
- region_id
- district_id
- name
- school_code_hash
- school_code_rotated_at
- school_type
- resource_level
- active
```

`region` 不写死成枚举。Pattani / Yala / Narathiwat 只是初始数据。

### 7.2 学校邀请码

- 每所学校一个当前有效邀请码。
- 6-8 位随机大写字母数字，避免易混字符。
- 数据库存 hash，不存明文。
- 创建/重置时只显示一次明文。
- 重置后旧 code 失效，已绑定教师不受影响。
- 教师不能自助换学校，只能管理员换绑。
- 换绑只影响未来请求，不迁移旧投稿和知识。

## 8. 权限模型

权限由 `role + scope` 组成。

角色：

```text
reviewer
senior_reviewer
admin
super_admin
```

作用范围：

```text
region_scope
school_scope
```

权限摘要：

```text
reviewer:
- 审核学校私有知识
- 编辑 pending_review 内容
- 标记敏感/版权风险
- 退回/拒绝投稿

senior_reviewer:
- reviewer 所有权限
- 二审地区共享
- 处理 sensitive_hold
- 发布 shared_region
- 恢复版本

admin:
- senior_reviewer 所有权限
- 管理本地区学校和教师
- 调整本地区用量
- 重置本地区 school_code

super_admin:
- 全局所有权限
- 创建地区
- 管理所有 admin_users
- 发布 shared_global
- 系统配置
```

MVP 先使用应用层统一权限过滤，暂不启用完整 RLS。后续真实试点前可考虑 PostgreSQL RLS。

## 9. 知识可见范围

知识范围：

```text
private_school
shared_region
shared_global
```

规则：

- 教师投稿默认进入 `private_school` 待审核。
- 任何知识进入 RAG 前必须至少人工审核一次。
- 学校私有知识单审。
- 地区/全局共享知识双审。
- 学校私有知识不写 GitHub，只存在 PostgreSQL + pgvector。
- 地区/全局共享知识写 GitHub Markdown + pgvector。

可见性：

```text
教师可检索：
- 本校 approved private_school
- 本地区 approved shared_region
- shared_global

教师不可检索：
- 其他学校 private_school
- 其他地区 shared_region
- pending_review / rejected / sensitive_hold / deleted
```

## 10. 知识类型与字段

MVP 真实支持：

```text
local_example
term_explanation
teaching_activity
```

预留：

```text
full_lesson
image_extracted_note
textbook_reference
exam_paper_reference
```

推荐通用字段：

```text
id
owner_type: project / school / teacher
owner_school_id
owner_region_id
visibility_scope
review_status
knowledge_type
subject
topic
title
target_grade
grade_min
grade_max
grade_mode
curriculum_codes
curriculum_notes
adaptation_notes
content_th
content_ms
content_en
type_specific JSONB
local_context
classroom_use
materials_needed
safety_notes
sensitive_tags
copyright_status
quality_score
source_type
source_confidence
source_note
vector_status
github_path
github_commit_sha
is_deleted
deleted_at
created_at
updated_at
published_at
```

年级策略：

- `target_grade` 表示主要适用年级。
- `grade_min / grade_max` 表示可迁移范围。
- `grade_mode` 支持 `exact / range / band / remedial / extension`。
- 完整教案未来必须绑定单一 `target_grade`。
- 本地案例、术语、活动可以跨年级，但必须说明如何调整。

课程指标策略：

- MVP 预留 `curriculum_codes / curriculum_notes`。
- 不强制填写。
- 只有人工确认的课程指标可以进入 prompt。
- AI 不允许自行编造官方课程代码。

## 11. 审核流程

审核状态建议：

```text
draft
pending_review
approved_school_private
first_approved_region
approved_region_shared
first_approved_global
approved_global_shared
needs_revision
rejected
sensitive_hold
publish_failed
embedding_failed
pending_republish
archived
merged
withdrawn
```

学校私有：

```text
pending_review -> approved_school_private
```

地区共享：

```text
approved_school_private -> first_approved_region -> approved_region_shared
```

全局共享：

```text
approved_region_shared -> first_approved_global -> approved_global_shared
```

教师投稿审核结果通过 LINE 通知：

- 审核通过。
- 需要修改。
- 拒绝。
- 升级为地区/全局共享。

`needs_revision` 第一版允许教师重新提交，不做复杂原投稿编辑。

教师可撤回未审核投稿；已审核通过的投稿只能由管理员删除/归档。

## 12. 质量评分

MVP 使用轻量 `quality_score`。

建议：

```text
1: 勉强可用
2: 可用于学校私有
3: 标准可用
4: 适合地区共享
5: 优秀示范
```

RAG rerank 时优先使用高质量知识。

共享建议：

```text
private_school: quality_score >= 2
shared_region: quality_score >= 3
shared_global: quality_score >= 4
```

## 13. 敏感与版权处理

### 13.1 敏感内容

自动初筛采用规则 + 模型，最终由人工审核员确认。

敏感标签：

```text
student_identity
school_identity
personal_data
religion
ethnic_identity
language_identity
royal_family
political_content
ethnic_conflict
violence
copyright_risk
```

风险等级：

```text
low
medium
high
blocked
```

处理：

- `low`: 普通审核。
- `medium`: 审核员注意。
- `high`: `sensitive_hold`，需要 senior_reviewer。
- `blocked`: 不进入 RAG，除非 admin 手动解除。

### 13.2 版权

教材、试卷、电子书内容可以未来进入系统，但必须经过版权状态审核。

版权状态：

```text
unchecked
likely_original
needs_review
needs_rewrite
licensed
approved_private_reference
approved_shared_adapted
rejected
```

规则：

- 教材/试卷/电子书上传 MVP 只占位，不保存文件。
- 未来开启后，可以作为 `private_reference`。
- 未授权原文不得直接进入 `shared_region / shared_global`。
- 未授权原文不得直接写 GitHub。
- 可改写为原创教学说明、本地案例或课堂活动后共享。
- `licensed` 或 `approved_shared_adapted` 才能共享。

## 14. 版本、恢复、删除和合并

### 14.1 版本记录

表：

```text
knowledge_item_versions
- id
- knowledge_item_id
- version_number
- snapshot JSONB
- change_summary
- change_type
- changed_by_admin_id
- created_at
```

每次明确保存/审核/恢复/可见范围变更/发布时创建版本。

RAG 引用记录 `knowledge_item_version_id`。

### 14.2 恢复

恢复采用完整 snapshot 覆盖当前内容，并创建新版本：

```text
change_type = restored
```

规则：

- `private_school` 恢复后直接 `needs_reembed`。
- `shared_region/shared_global` 恢复后进入 `pending_republish`，需要重新发布。

### 14.3 软删除

知识默认软删除。

删除后：

- 不参与 RAG。
- `knowledge_chunks.active = false`。
- 保留版本历史。
- 保留 audit log。
- admin 可恢复。
- 已发布 GitHub 文件默认不物理删除，严重敏感泄露单独处理。

### 14.4 重复检测和合并

MVP 做轻量相似检测。

流程：

```text
新知识创建/投稿
  -> 生成 embedding
  -> 检索相似 knowledge_items
  -> 后台提示可能重复
  -> 管理员确认是否合并
```

合并规则：

- 保留主知识 item。
- 重复 item 标记 `merged / archived`。
- 记录 `merged_into_knowledge_item_id`。
- 创建 version 和 audit log。
- 主知识重新 embedding。
- 重复 item 不参与 RAG。

## 15. RAG 设计

### 15.1 检索策略

MVP 采用：

```text
metadata hard filter
  + pgvector similarity
  + 简单关键词/质量/年级/scope rerank
```

不做完整 BM25、多语言分词和复杂 hybrid rank fusion。

过滤条件：

```text
visibility_scope allowed
review_status approved
is_deleted = false
subject match
grade compatible
region/school/global allowed
sensitive/copyright status allowed
```

rerank 因子：

- vector similarity。
- topic exact match。
- title/topic keyword match。
- exact `target_grade` boost。
- `quality_score` boost。
- scope priority boost。

每次返回：

```text
5-8 chunks
同一个 knowledge_item 最多 1-2 chunks
```

### 15.2 Chunk 策略

- 短知识默认一条 `knowledge_item` 生成一个 chunk。
- 超过阈值再按章节或字段切片。
- 建议阈值：`800 tokens`。
- embedding 文本包含 metadata 前缀。
- prompt 上下文使用干净模板，不直接塞原始 embedding 文本。

### 15.3 低置信度

记录：

```text
rag_confidence: high / medium / low
retrieved_count
local_retrieved_count
top_similarity
fallback_reason
```

低置信度时仍生成通用教案，但提示：

```text
当前知识库中该主题的本地案例较少，本教案包含通用教学建议。
```

### 15.4 引用记录

表：

```text
lesson_knowledge_refs
- id
- lesson_request_id
- knowledge_item_id
- knowledge_item_version_id
- chunk_id
- relevance_score
- rank
- used_in_section
- created_at
```

教师端只显示脱敏简短引用，不显示学校/教师姓名。

## 16. 模型策略

模型 provider 不写死。

按任务配置：

```text
TEXT_GENERATION_MODEL
REQUEST_PARSE_MODEL
SENSITIVITY_MODEL
COPYRIGHT_MODEL
EMBEDDING_MODEL
VISION_MODEL
```

MVP 可先用 Gemini 免费层验证，也可后续接入 DeepSeek/Qwen 做文本生成对比。

记录每次模型调用：

```text
model_provider
model_name
task_type
prompt_version
rag_strategy_version
input_tokens
output_tokens
latency_ms
cost_estimated
status
error_message
```

Prompt 文件版本化，暂不做后台在线编辑 prompt。

模型输出必须：

- JSON 输出。
- Pydantic schema 校验。
- 最多 2 次修复/重试。
- 失败后标记任务失败并通知教师。

返回教师前做输出安全二次检查：

- 低风险：返回。
- 中风险：自动改写一次。
- 高风险：不返回，标记需人工查看。

## 17. Embedding 策略

MVP 固定一个 embedding 模型。

表里记录：

```text
embedding_provider
embedding_model
embedding_dimensions
```

后续换模型时全量重建索引。MVP 数据量小，重建成本低。

支持：

- embedding 状态追踪。
- 单条 retry。
- 批量 retry failed。
- 脚本全量重建 embedding。

状态：

```text
not_embedded
embedding_queued
embedded
embedding_failed
needs_reembed
```

## 18. 教案生成

### 18.1 输入

采用自然语言输入 + 缺字段追问。

硬要求：

```text
subject
grade
topic
```

默认补齐：

```text
region = 教师学校所属地区
school_id = 教师绑定学校
language_mode = Thai + local Malay helper + English helper
duration_minutes = 45
resource_level = low_resource
```

### 18.2 输出保存

内部保存：

```text
structured_content JSONB
rendered_markdown TEXT
```

教师端：

```text
LINE 文本预览
Flex 操作卡片
DOCX 下载链接
```

暂不做 PDF。

### 18.3 DOCX

DOCX 主内容泰语，本地马来语和英语作为辅助表达。

模板包含：

```text
Title
Subject / Grade / Topic / Duration
Language Mode
Local Context
Teaching Objectives
Materials
Lesson Flow
Local Examples
Key Terms
Practice Questions
Board Plan
Low-resource Alternative
Safety / Sensitivity Notes
AI Notice
Local Knowledge Used
```

文件命名：

```text
lesson_{grade}_{subject}_{topic}_{date}_{short_id}.docx
```

保存策略：

- 生成历史保存 12 个月。
- DOCX 文件保存 90 天。
- DOCX 过期后可从 structured_content 重新生成。

## 19. LINE 端设计

### 19.1 首次使用

```text
教师关注 LINE
  -> 输入 school_code
  -> 系统显示学校名称确认
  -> 显示隐私/AI 使用说明
  -> 教师同意
  -> 绑定完成
```

同意版本记录：

```text
consent_versions
teacher_consents
```

同意文本升级后，教师下次使用前必须重新同意。

### 19.2 Rich Menu

MVP 做简单 Rich Menu：

```text
生成教案
投稿知识
查看历史
我的学校
帮助
反馈
```

### 19.3 消息策略

收到请求：

```text
reply message: 正在生成，请稍等
```

任务完成：

```text
push message: 教案预览 + DOCX 下载链接
```

失败：

```text
push message: 生成失败，请稍后重试
```

记录发送状态：

```text
line_message_deliveries
```

### 19.4 Webhook 幂等

保存 LINE 事件：

```text
line_events
- event_key
- line_user_id
- message_id
- event_type
- processed_status
- created_at
```

重复 event 直接返回 200，不重复处理。

### 19.5 会话状态

短期会话状态放 Redis，带 TTL。

最终业务结果写 PostgreSQL。

## 20. 投稿和反馈

### 20.1 投稿入口

采用菜单引导投稿 + 自然语言投稿兼容。

默认：

```text
visibility_scope = private_school
review_status = pending_review
source_type = teacher_submission
```

### 20.2 历史

教师可查看最近 5 条历史教案。

如果 DOCX 还在，返回新 signed URL。

如果 DOCX 过期但结构化内容仍在，重新生成 DOCX。

### 20.3 反馈

教案结果卡片提供：

```text
有用
需要修改
不适合
```

Rich Menu 提供系统问题反馈入口。

后台有简单支持反馈列表，管理员可标记处理并可选 LINE 回复教师。

## 21. GitHub 发布

MVP 使用：

```text
后端直接 commit GitHub main
后端同步 embedding 到 pgvector
不依赖 GitHub Actions 作为主流程
```

流程：

```text
senior_reviewer/admin 点击发布
  -> 检查审核状态和可见范围
  -> 生成 Markdown
  -> 校验 Markdown
  -> commit 到 GitHub
  -> 保存 github_path / github_commit_sha
  -> chunk + embedding + upsert pgvector
  -> 状态更新为 embedded
```

失败处理：

- GitHub commit 失败：`publish_failed`，不进入 embedding。
- Embedding 失败：`embedding_failed`，管理员可 retry。

### 21.1 GitHub 目录

```text
knowledge/
  global/
    math/
      grade-3-5/
        low-resource-group-activity-ki000001.md

  countries/
    th/
      regions/
        pattani/
          math/
            grade-4/
              fractions-fish-sharing-ki000123.md
            grade-3-5/
              market-measurement-ki000124.md
```

### 21.2 Markdown front matter

```yaml
---
id: ki_000123
knowledge_type: local_example
country: th
region: pattani
visibility_scope: shared_region
subject: math
topic: fractions
target_grade: 4
grade_min: 3
grade_max: 5
quality_score: 4
sensitive_tags: []
copyright_status: approved_shared_adapted
published_at: 2026-07-25
---
```

发布前做 Markdown front matter 和正文结构校验。

### 21.3 Commit

- 使用专门 GitHub token，后续可换 machine user 或 GitHub App。
- commit message 格式：

```text
publish knowledge: ki_000123 fractions-fish-sharing
update knowledge: ki_000123 fractions-fish-sharing
archive knowledge: ki_000123 fractions-fish-sharing
```

数据库记录：

```text
github_path
github_commit_sha
github_commit_message
published_by_admin_id
published_at
```

支持批量发布：

- 单批最多 20 条。
- 允许部分成功。
- 后台显示失败原因。

## 22. 异步任务

使用 Redis Queue / Python RQ。

任务 payload 只传实体 ID，不传大正文。

任务类型：

```text
generate_lesson
generate_docx
send_line_message
embed_knowledge_item
publish_knowledge_item
batch_publish_knowledge
sensitivity_check
copyright_check
duplicate_check
```

最终状态写 PostgreSQL。

Redis 负责：

- 队列。
- retry/backoff。
- 短期会话。
- 限流计数。
- 去重锁。

PostgreSQL 负责：

- 业务最终状态。
- 生成历史。
- 审核记录。
- 发布状态。
- 错误摘要。
- 用量统计。

## 23. 存储

MVP 做统一 `media_assets` 表和 StorageService。

真实用于：

```text
lesson_docx
```

预留：

```text
submission_attachment
textbook_upload
exam_paper_upload
ocr_source
generated_export
```

表字段：

```text
media_assets
- id
- owner_type
- owner_id
- uploaded_by_teacher_id
- uploaded_by_admin_id
- media_type
- purpose
- object_key
- original_filename
- mime_type
- file_size
- storage_provider
- checksum
- retention_policy
- expires_at
- created_at
- deleted_at
```

下载使用 signed URL，不保存永久 public URL。

## 24. 用量、限流和预算

默认额度：

```text
teacher_daily_lesson_limit = 10
teacher_hourly_lesson_limit = 5
school_daily_lesson_limit = 200
max_generation_retries = 2
max_docx_regeneration_per_day = 10 / teacher
```

早期测试可降低：

```text
teacher_daily_lesson_limit = 5
school_daily_lesson_limit = 50
```

记录：

```text
usage_counters
model_call_logs
```

预算：

- 系统级月预算，例如 500 USD。
- 后台显示 50%、80%、100% 阈值提醒。
- 免费模型也记录 token 和请求量。

## 25. 日志、监控和审计

### 25.1 结构化日志

所有服务输出 JSON log：

```text
request_id
teacher_id
school_id
lesson_request_id
job_id
action
status
latency_ms
error_code
```

### 25.2 Sentry

MVP 必须接入 Sentry。

### 25.3 健康检查

FastAPI：

```text
/health
/ready
```

检查：

- 数据库连接。
- Redis 连接。
- 基础配置。

### 25.4 后台状态页

显示：

- 今日生成次数。
- 失败任务数。
- 队列长度。
- 模型调用失败数。
- GitHub 发布失败数。
- embedding_failed 数。
- 预算使用情况。

### 25.5 审计日志

表：

```text
audit_logs
- id
- actor_admin_id
- action
- target_type
- target_id
- before_snapshot JSONB
- after_snapshot JSONB
- ip_address
- user_agent
- created_at
```

必须记录：

- 学校创建/停用。
- school_code 重置。
- 教师禁用/启用。
- 审核动作。
- 知识编辑。
- 可见范围变更。
- 敏感/版权标签变更。
- 版本恢复。
- GitHub 发布。
- 用量限制变更。

## 26. 后台页面

Streamlit 页面建议：

```text
Login
Dashboard
Schools
Teachers
Lesson Requests
Submissions
Knowledge Items
Knowledge Detail/Edit
Review Queue
Version History
Duplicate Review
Coverage Dashboard
Usage
Support Tickets
Audit Logs
Settings
```

知识审核表单按 `knowledge_type` 动态显示字段。

数据库使用 common columns + `type_specific JSONB` 保存类型专属字段。

## 27. 覆盖度看板

后台显示：

- region。
- school。
- subject。
- target_grade。
- topic。
- knowledge_type。
- visibility_scope。
- quality_score。

统计：

- 知识条数。
- 高质量知识条数。
- 最近 7/30 天被检索次数。
- low confidence 请求次数。
- 教师反馈 `not_local_enough` 次数。
- 最常用知识。
- 最缺主题。

## 28. 初始知识库

MVP 目标：先准备约 150 条高质量知识单元，用于验证 RAG 效果。

不是理论最优值，而是 MVP 工程折中：

- 少于 100 条难以验证 RAG 价值。
- 150 条可覆盖核心组合并支持 A/B 或人工评估。
- 300-500 条适合更严肃封闭试用。

初始覆盖建议：

```text
Pattani 优先
Math + Science
Grade 3-5
Thai + local Malay helper + English helper
```

来源：

```text
project_manual
ai_draft_reviewed
teacher_submission
local_consultant
public_source_adapted
textbook_adapted
```

初始知识用 YAML 文件人工维护，导入时 Pydantic 严格校验。

目录：

```text
data/seed_knowledge/
```

默认导入状态：

```text
pending_review
```

只有明确标记 verified 的种子数据可直接导入为 approved。

## 29. 测试策略

MVP 测试重点：

- 权限隔离。
- 审核状态流。
- RAG 检索过滤。
- 版本恢复。
- Redis job 幂等。
- 模型 provider mock。
- GitHub publish mock。
- Storage mock。

工具：

```text
pytest
pytest-asyncio
httpx
factory fixtures
```

外部服务测试默认 mock，不真实调用 Gemini/DeepSeek/LINE/GitHub。

手动端到端验收覆盖：

- LINE 绑定。
- 教案生成。
- DOCX 下载。
- 教师投稿。
- 后台审核。
- RAG 命中新知识。
- GitHub 发布。
- embedding retry。
- Sentry 测试错误。

## 30. CI/CD

GitHub Actions 基础 CI：

```text
on pull_request / push:
- install dependencies
- run lint
- run tests
- validate migrations
```

部署：

- `main` 自动部署 staging。
- production 手动触发。
- staging 可自动 migrate。
- production migration 手动确认。

## 31. 上线验收标准

MVP 完成必须通过以下路径：

1. 教师首次绑定：

```text
关注测试 LINE -> 输入 school_code -> 确认学校 -> 同意隐私/AI 说明 -> 绑定成功
```

2. 教案生成：

```text
输入“四年级数学分数”
  -> 缺字段追问或自动补齐
  -> 立即回复正在生成
  -> worker 生成
  -> 返回文本预览 + DOCX 链接
```

3. RAG 命中：

```text
已有 approved knowledge
  -> 教师生成相关主题
  -> lesson_knowledge_refs 记录引用
  -> 内容体现本地知识
```

4. 教师投稿：

```text
LINE 投稿本地案例
  -> pending_review
  -> 后台可查看
  -> 自动敏感/版权/重复初筛
```

5. 审核入库：

```text
reviewer 审核为 approved_school_private
  -> embedding 成功
  -> 本校下一次生成可检索
```

6. 共享发布：

```text
senior_reviewer 升级 shared_region
  -> 生成 Markdown
  -> commit GitHub
  -> embedding 更新
  -> DB 记录 commit_sha
```

7. 权限隔离：

```text
School A 私有知识不会被 School B 检索
Pattani 共享知识不会被其他 region 默认检索
```

8. 失败恢复：

```text
模型失败重试
embedding_failed 可后台重试
publish_failed 可后台重试
```

9. 监控：

```text
Sentry 收到测试错误
后台状态页显示队列/失败/用量
```

## 32. 开发里程碑

### Milestone 1: 基础骨架

- Repo / Docker / FastAPI / Worker / Streamlit。
- PostgreSQL models + Alembic。
- Redis/RQ。
- 配置和 Sentry。
- admin dev login。

验收：

```text
三个服务能启动
数据库迁移成功
worker 能跑测试 job
```

### Milestone 2: LINE 绑定和教案生成

- LINE webhook。
- signature 校验。
- school_code 绑定。
- consent。
- 自然语言教案请求。
- 缺字段追问。
- 异步生成。
- DOCX 导出。
- 历史查看。
- 反馈。

验收：

```text
教师能在 LINE 生成一份 DOCX 教案
```

### Milestone 3: 知识库和 RAG

- `knowledge_items`。
- YAML seed import。
- embedding。
- filtered vector search + rerank。
- `lesson_knowledge_refs`。
- RAG confidence。

验收：

```text
教案能引用已审核知识
low confidence 能提示
```

### Milestone 4: 投稿和审核后台

- 教师投稿。
- Streamlit review queue。
- 敏感/版权/重复检测。
- 质量评分。
- 版本记录/恢复。
- 软删除。
- 学校私有审核入 RAG。

验收：

```text
教师投稿可审核后进入本校 RAG
```

### Milestone 5: 共享发布

- visibility upgrade。
- 双审核。
- Markdown render/validate。
- GitHub direct commit。
- batch publish。
- embedding sync。
- publish retry。

验收：

```text
地区共享知识写入 GitHub，并能被 RAG 使用
```

### Milestone 6: 运营和验收

- 权限范围。
- 用量限制。
- 覆盖度看板。
- 状态页。
- audit logs。
- CI/CD。
- staging/prod。
- 端到端验收。

验收：

```text
可以给封闭测试教师使用
```

## 33. 你需要准备的账号、密钥和资源

所有外部资源建议由你或项目组织账号创建和持有。开发只使用最小权限 token/环境变量接入。

### 33.1 LINE

- LINE Official Account。
- Messaging API channel。
- 测试 channel。
- 正式 channel。
- `LINE_CHANNEL_SECRET`。
- `LINE_CHANNEL_ACCESS_TOKEN`。
- Webhook URL。
- Rich Menu 素材或文案。

### 33.2 数据库和存储

- Supabase project for staging。
- Supabase project for production。
- Postgres connection string。
- pgvector extension。
- Supabase Storage bucket。
- Service role key 仅后端使用。

### 33.3 Redis

- Upstash Redis staging。
- Upstash Redis production。
- `REDIS_URL`。

### 33.4 模型 API

至少准备：

- Gemini API key。

可选准备：

- DeepSeek API key。
- Qwen API key。

需要后续用相同测试集比较：

- 泰语质量。
- 本地马来语辅助表达。
- 教育场景输出。
- 成本。
- 延迟。

### 33.5 GitHub

- GitHub private repo for shared knowledge。
- Fine-grained PAT 或 machine user token。
- 权限最小化：

```text
contents read/write on target repo
metadata read
```

不要给全账号所有 repo 权限。

### 33.6 Google OAuth

- Google OAuth app。
- Client ID。
- Client Secret。
- Staging callback URL。
- Production callback URL。

### 33.7 Sentry

- Sentry project。
- `SENTRY_DSN`。
- staging / production environment 区分。

### 33.8 部署平台

选择 Render / Railway / Fly.io 之一。

需要部署：

- FastAPI service。
- RQ worker service。
- Streamlit admin service。

### 33.9 域名和 HTTPS

- API 域名。
- Admin 域名。
- Staging 域名。
- Production 域名。
- HTTPS 必须启用，LINE webhook 需要公网 HTTPS。

### 33.10 初始业务数据

需要准备：

- 初始地区：至少 Pattani，可加 Yala / Narathiwat。
- 初始 district 可选。
- 测试学校名称。
- 测试学校邀请码由系统生成。
- 测试教师名单或内部测试 LINE 用户。
- 初始 admin users。
- 初始 consent 文案。
- 初始 feature flags。
- 初始 150 条左右 seed knowledge 草稿或主题清单。

## 34. 环境变量策略

仓库提交：

```text
.env.example
```

不提交：

```text
.env
```

本地开发用 `.env`，加入 `.gitignore`。

生产/试点环境在部署平台配置真实环境变量。

配置统一使用 Pydantic Settings：

```text
app/core/config.py
```

按启用 provider 校验必填 key。

## 35. 后续升级路径

### 35.1 GitHub 发布

MVP:

```text
Direct commit main + 后端 embedding
```

升级:

```text
Branch -> PR -> GitHub Actions -> merge -> webhook/callback -> embedding
```

建议升级触发：

- 500+ 教师。
- 10+ 学校。
- 每日 20+ 条共享知识发布。
- 3+ 审核员协作。
- 全局共享内容频繁发布。
- 外部专家参与内容审查。

### 35.2 后台

MVP:

```text
Streamlit
```

升级:

```text
React / Vue / Next.js Admin Portal + FastAPI Admin API
```

### 35.3 数据隔离

MVP:

```text
共享 PostgreSQL + 应用层逻辑隔离
```

升级:

```text
PostgreSQL RLS
dedicated schema
dedicated database
```

触发条件：

- 合同要求物理隔离。
- 数据驻留要求。
- 学校/机构付费要求专属实例。
- 跨机构运营边界变复杂。

### 35.4 检索

MVP:

```text
filtered vector search + lightweight reranking
```

升级:

```text
full hybrid search
BM25/full-text
Thai tokenizer
reranker
Qdrant / Milvus / Weaviate
```

触发条件：

- 500-1000+ 条知识。
- 多语言术语表稳定。
- 出现大量检索失败案例。
- 教师反馈显示本地知识命中不足。

### 35.5 仓库

MVP:

```text
single monorepo
```

升级:

```text
backend repo
admin portal repo
worker repo
infra repo
shared SDK
```

前提是 MVP 内部目录边界保持清楚。

