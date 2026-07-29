# 面向泰国南部代课教师的 AI 本土化教案生成助手

更新时间：2026-07-24

## 1. 项目定位

本项目面向泰国南部边境府，尤其是也拉府（Yala）、北大年府（Pattani）和陶公府（Narathiwat）的乡村合同制教师、代课教师和多科教学教师，提供一个嵌入 LINE 的 AI 教案生成与本土知识共创助手。

核心目标不是做一个通用 AI 聊天机器人，而是帮助教师在备课时间不足、多语言教学压力大、缺少本地化教学材料的情况下，快速生成符合当地学生语言和生活经验的教案。

系统第一阶段按 50 名教师真实试点设计，预算控制在每月 500 美元以内；架构尽量简单，但保留后续扩展能力。

## 2. 问题背景与调研依据

### 2.1 泰国小型学校教师行政负担过重

泰国公平教育基金（EEF/EEFI）相关调查和报道显示，小型学校教师承担了大量非教学工作，导致备课时间被严重挤压。

关键数据：

| 指标 | 数据 |
|---|---:|
| 小型学校教师平均每周授课时长 | 27.3 小时 |
| 超出泰国教育部标准比例 | 37.6% |
| 认为超负荷工作影响课堂教学的教师 | 47.7% |
| 认为自己有足够时间备课的教师 | 29.7% |
| 反映工作与生活难以平衡的教师 | 63% |
| 教师平均每年离开教室处理其他事务 | 84 天 |
| 其中用于教师/学校绩效评估 | 43 天 |

非教学任务耗时包括：

| 非教学任务 | 每学期耗时 |
|---|---:|
| 年级/班级主任工作 | 874 小时 |
| 学术行政 | 777 小时 |
| 公关工作 | 468 小时 |
| 质量保证 | 438 小时 |
| 人力资源 | 414 小时 |

相关来源：

- Bangkok Post, "Marathon teaching: the strained tasks of small-school teachers": https://www.bangkokpost.com/thailand/special-reports/3176959/marathon-teaching-the-strained-tasks-of-small-schoolteachers
- EEF English article, "The Small-School Teacher Crisis": https://en.eef.or.th/2026/07/13/the-small-school-teacher-crisis/
- Tai Thai Times: https://taithaitimes.com/article/detail/9034
- The Free Library mirror: https://www.thefreelibrary.com/Teachers+at+small+schools+struggling+to+cope%2c+survey+shows.-a0871268728

极端案例方面，Bangkok Post 报道称，2025 年 6 月武里南府一名英语教师因承担财务、采购等额外行政压力而自杀，反映教师行政负担已经成为严重的系统性问题。

- Bangkok Post, "Teacher commits suicide over extra work": https://www.bangkokpost.com/learning/easy/3052286/teacher-commits-suicide-over-extra-work

政策回应方面，泰国教育部已经推进教师减负政策，将需向基础教育委员会报告的项目从 114 项削减至 62 项，ITA 评估指标从 28 项削减至 17 项，惠及全国 50 多万名教师。

- Thailand News Gazette: https://www.thailandnewsgazette.com/minister-narumon-implements-obec-reporting-reduction-policy/

### 2.2 泰南多语言教学困境

泰国南部边境府大量学生的家庭语言是 Patani Malay / Pattani Malay，即当地马来语变体，常被称为 Jawi/Yawi 语境下的本地语言表达。但学校教材、考试和行政教学体系主要使用泰语。许多学生在低年级阶段需要同时理解学科知识和非母语教学语言，学习难度显著增加。

Prince of Songkla University 相关论文指出，泰国南部冲突地区的教育政策长期与国家身份建构、语言政策和安全治理交织在一起。该研究建议，教育若要发挥和平建设作用，需要承认文化多样性、地方历史和本地语言，并推动更包容的多语言教育。

- Prince of Songkla University / Conflict and Peace Studies Journal: https://so07.tci-thaijo.org/index.php/cpsj_psu/article/view/4-1_1

UNESCO 也支持以第一语言为基础的多语言教育。2023 年在曼谷形成的 Bangkok Priorities for Action 呼吁亚太地区政府推进 first language-based multilingual education，以提升学习效果和教育包容性。

- UNESCO, Bangkok Priorities for Action: https://www.unesco.org/en/articles/bangkok-priorities-action-first-language-based-multilingual-education
- UNESCO document record: https://unesdoc.unesco.org/ark:/48223/pf0000387958

Patani Malay-Thai 双语/多语教育已有案例研究，强调将 Patani Malay 语言和文化身份纳入教学能改善社区对学校教育的信任。

- UNESCO Institute for Lifelong Learning case study: https://www.uil.unesco.org/en/litbase/patani-malay-thai-bilingual/multilingual-education-thailand
- Mahidol University Patani Malay-Thai MTB-MLE project: https://op.mahidol.ac.th/ra/2017/10/25/lc-04/
- Planning and Implementing Patani Malay in Bilingual Education in Southern Thailand: https://openresearch-repository.anu.edu.au/bitstreams/ca86475b-3b44-4080-8e3e-c1a9cf57ef3a/download

### 2.3 乡村教师短缺与多科教学

基于 PISA Thailand 学校层面数据的实证研究显示，教师短缺会显著影响学生教育表现，农村地区更明显。教师短缺还会导致教师被迫教授非专业科目，甚至混合不同年级教学。

- ERIC record: https://eric.ed.gov/?id=EJ1405423
- DOAJ record: https://doaj.org/article/134da8daebe24ae09cc434ac0fa7659c

世界银行关于泰国小型学校的研究指出，约 64% 的泰国小学存在严重教师短缺，定义为平均每个班级不足一名教师。小型学校教师往往需要覆盖更多科目和年级。

- World Bank blog, "Thailand's small school challenge and options for quality education": https://blogs.worldbank.org/en/eastasiapacific/thailand-s-small-school-challenge-and-options-quality-education
- World Bank Open Knowledge Repository: https://openknowledge.worldbank.org/entities/publication/80825e30-7a4d-4aea-b855-c48b4568b6fa

### 2.4 LINE 是泰国最合适的产品入口

LINE 在泰国是国民级通信应用。2025 年初相关数字报告显示，泰国 LINE 月活跃用户约 5,600 万，占总人口 78.2%，占互联网用户 85.7%。2026 年市场报道仍显示 LINE 是泰国使用率最高的平台之一。

这意味着本项目不应优先做独立 App，而应直接嵌入 LINE Official Account，降低教师学习成本。

- Meltwater, 2025 Thailand social media statistics: https://www.meltwater.com/en/blog/social-media-statistics-thailand
- Thai Headlines / DataReportal summary: https://www.thaiheadlines.com/169393/
- LINE Developers Messaging API: https://developers.line.biz/en/reference/messaging-api/

### 2.5 AI 模型与技术环境

短期模型选择：

- Gemini：适合原型和试点，支持文本与图片输入，泰语能力较好，Google 账号/API 获取门槛低。
- OpenAI GPT 系列：能力强，但在本项目中可作为备选供应商。
- Typhoon：泰语大模型生态，适合后续本地化研究。
- OpenThaiGPT：泰语开源模型，可作为远期自主部署方向。
- SEA-LION：面向东南亚语言和文化的开源多语言模型，可作为区域化扩展参考。
- Qwen：可本地部署，适合远期离线化和成本控制。

相关来源：

- Gemini API models: https://ai.google.dev/gemini-api/docs/models
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Typhoon official: https://opentyphoon.ai/
- Typhoon technical report: https://arxiv.org/html/2312.13951v1
- Typhoon 2 paper: https://arxiv.org/html/2412.13702v1
- OpenThaiGPT 1.5: https://openthai.aieat.or.th/en/previous-versions-and-resources/openthaigpt-1.5
- SEA-LION: https://sea-lion.ai/

## 3. 用户画像

目标用户不是“技术能力弱的教师”，而是被结构性问题压缩备课时间的乡村教师。

推荐用户画像表述：

> 仅达到最低学历或岗位要求的乡村合同制/代课教师，因师资短缺和行政负担被迫承担多科教学，缺乏备课时间、本地化教学材料和方言教学支持。

核心需求：

- 快速生成一节可直接使用或稍作修改的教案。
- 能把抽象知识点转换成当地学生熟悉的生活例子。
- 能获得泰语、马来语、英语三语言辅助表达。
- 能通过图片上传教材页、板书或手写笔记，自动转成投稿草稿。
- 不需要学习复杂后台或额外 App。

## 4. 产品定义

### 4.1 产品形态

产品形态为 LINE Official Account 聊天机器人，并配套一个轻量管理员审核后台。

教师端只使用 LINE：

- 发送文本需求。
- 上传教材页、板书或课堂材料图片。
- 接收教案卡片。
- 确认投稿草稿。
- 查询历史生成记录。

管理员端使用 Streamlit 后台：

- 查看投稿。
- 查看图片和 AI 识别结果。
- 编辑三语言内容。
- 初审。
- 复核。
- 标记敏感内容。
- 发布到 GitHub private repo。
- 触发向量库同步。

### 4.2 核心功能

1. 教案生成

教师输入学科、年级、知识点、地区和语言需求，系统检索本土知识库，调用 Gemini 生成结构化教案。

输出内容包括：

- 教学目标。
- 课堂导入。
- 本地化例子。
- 关键术语解释。
- 泰语、马来语、英语辅助表达。
- 课堂活动。
- 练习题。
- 板书建议。
- 低资源环境替代方案。

2. 图片识别与投稿草稿

教师上传图片后，系统调用 LINE Content API 下载图片，再调用 Gemini Vision/OCR 能力识别图片内容，转成结构化投稿草稿。

3. 内容投稿

教师可通过 LINE 发送投稿，或确认 AI 从图片中抽取的投稿草稿。

投稿不会直接进入知识库，而是先进入 PostgreSQL，状态为 pending_review。

4. 双审核入库

管理员完成初审和复核后，内容才会被发布到 GitHub private repo 和向量库。

5. 本土知识检索

系统根据地区、学科、年级、语言、敏感等级等过滤条件检索知识库，避免生成脱离当地情境的教案。

6. 数据隔离与脱敏共享

原始投稿、原始图片、教师 userId 和生成记录按学校/地区隔离；审核通过并脱敏后的知识可进入共享知识库。

## 5. 当前推荐系统架构

本项目采用：

```text
LINE Bot + FastAPI + PostgreSQL + pgvector + Redis Queue + Worker Pool
+ Object Storage + Gemini + Private GitHub + Streamlit Admin Dashboard
```

### 5.1 架构总览

```text
教师 LINE App
  ↓
LINE Messaging API Webhook
  ↓
FastAPI 后端
  ├── LINE signature 校验
  ├── 用户身份识别：LINE userId
  ├── 意图识别：教案生成 / 投稿 / 图片识别 / 查询
  ├── PostgreSQL：业务主数据库
  ├── pgvector：向量检索
  ├── Redis Queue：异步任务队列
  ├── Worker Pool：并行执行耗时任务
  ├── Object Storage：图片和附件
  ├── Gemini API：文本生成与图片识别
  └── GitHub API：发布已审核知识库

管理员
  ↓
Streamlit Admin Dashboard
  ├── Google Login 或 LINE Login
  ├── admin_users 白名单
  ├── 投稿列表
  ├── 初审
  ├── 复核
  ├── 内容编辑
  ├── 敏感内容标记
  └── 发布到 GitHub private repo

GitHub private repo
  ↓
GitHub Actions
  ↓
Markdown 校验 → 切片 → Embedding → 写入 pgvector
```

### 5.2 各组件职责

| 层级 | 技术选型 | 职责 |
|---|---|---|
| 用户交互层 | LINE Official Account | 教师唯一入口 |
| Webhook/API 层 | FastAPI | 接收 LINE 事件、鉴权、路由、任务入队 |
| 主数据库 | PostgreSQL | 用户、会话、投稿、审核、生成记录、用量统计 |
| 向量检索 | pgvector | 存储 embedding，支持 RAG 检索 |
| 异步队列 | Redis / Upstash Redis | 教案生成、图片识别、GitHub 同步、embedding 任务 |
| 后台任务 | Worker Pool | 并行处理 AI 调用、图片识别、敏感检测、向量同步 |
| 图片存储 | Object Storage | 保存教材页、板书、投稿图片 |
| AI 引擎 | Gemini | 泰语/多语言生成、图片识别、结构化抽取 |
| 知识库版本管理 | GitHub private repo | 保存审核通过后的 Markdown 内容和版本历史 |
| 自动同步 | GitHub Actions | 内容校验、切片、embedding、同步向量库 |
| 管理后台 | Streamlit | 快速实现审核、复核、编辑、发布 |

### 5.3 GitHub 的正确定位

GitHub 不作为系统数据库。

GitHub 只负责：

- 保存审核通过后的 Markdown 知识库。
- 记录内容版本历史。
- 支持管理员追踪变更。
- 通过 GitHub Actions 触发知识库同步。

GitHub 不适合保存：

- 教师 userId。
- 会话状态。
- 投稿草稿。
- 原始图片。
- 审核流程状态。
- 任务队列。
- 用量统计。
- 错误日志。

这些运行时数据应保存在 PostgreSQL、Redis、Object Storage 和日志系统中。

GitHub API 限制参考：

- Authenticated REST API 通常为 5,000 requests/hour。
- 内容创建还存在 secondary limits，通常不超过 500 content-generating requests/hour。
- 官方文档：https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

## 6. 数据存储设计

### 6.1 数据存储位置

真实部署时数据库应位于云端，但数据库和服务器不是同一个概念。

```text
服务器 = 运行 FastAPI、Worker、Streamlit 的地方
数据库 = 保存业务数据的地方
对象存储 = 保存图片/附件的地方
向量库 = 保存 embedding 的地方
GitHub = 保存已审核知识库源文件的地方
```

推荐使用托管云服务，而不是把所有数据装在同一台服务器上。

原因：

- 应用服务器可以重启、扩容、重新部署。
- 数据库需要稳定、备份、权限控制和故障恢复。
- 图片文件适合对象存储，不适合塞进数据库或 GitHub。
- 向量索引可以从 Markdown 知识库重建，但也需要稳定查询。

### 6.2 推荐数据表

核心表：

```text
teachers
- id
- line_user_id
- display_name
- school_id
- region
- language_preference
- created_at
- last_active_at

schools
- id
- name
- region
- district
- visibility_scope

admin_users
- id
- provider
- provider_user_id
- email
- role
- region_scope
- active
- created_at

lesson_requests
- id
- teacher_id
- subject
- grade
- topic
- region
- language_mode
- status
- prompt
- generated_content
- token_input
- token_output
- created_at
- completed_at

submissions
- id
- teacher_id
- school_id
- source_type
- title
- subject
- grade
- region
- content_th
- content_ms
- content_en
- local_context
- sensitive_level
- status
- created_at
- updated_at

submission_reviews
- id
- submission_id
- reviewer_id
- review_stage
- decision
- comment
- created_at

media_assets
- id
- teacher_id
- submission_id
- object_key
- media_type
- original_filename
- storage_url
- pii_detected
- retention_policy
- created_at

knowledge_items
- id
- submission_id
- github_path
- github_commit_sha
- subject
- grade
- region
- language_primary
- title_th
- title_ms
- title_en
- content_th
- content_ms
- content_en
- published_at

knowledge_chunks
- id
- knowledge_item_id
- chunk_text
- language
- region
- subject
- grade
- embedding
- created_at

jobs
- id
- job_type
- payload
- status
- retry_count
- error_message
- created_at
- updated_at
```

### 6.3 数据保存策略

| 数据 | 保存策略 |
|---|---|
| 教师 LINE userId | 长期保存 |
| 会话上下文 | 6-12 个月 |
| 教案生成历史 | 6-24 个月 |
| 投稿草稿 | 长期保存 |
| 审核通过知识 | 长期保存 |
| 原始图片 | 默认长期保存，可压缩，可按政策删除 |
| 失败任务日志 | 30-90 天 |
| 敏感原文日志 | 不建议长期保存 |

### 6.4 数据隔离与共享

系统采用“原始数据隔离，脱敏知识共享”的策略。

```text
原始投稿、图片、教师身份、学校信息：按学校/地区隔离。
审核通过且脱敏后的知识：可进入共享知识库。
```

示例：

```text
不可共享：Pattani 某学校三年级学生 Ahmed 在课堂上...
可共享：泰南马来语母语学生学习泰语分数概念时，可使用分鱼案例辅助解释。
```

## 7. 并行处理与响应速度设计

### 7.1 为什么需要异步任务

LINE Webhook 不应该同步等待 Gemini 完整生成。正确流程是：

```text
教师发送需求
  ↓
FastAPI 立即回复：正在生成
  ↓
任务进入 Redis Queue
  ↓
Worker 后台处理
  ↓
完成后通过 LINE push message 返回结果
```

这样可以避免：

- Webhook 超时。
- Gemini 响应慢导致用户等待。
- 图片识别阻塞后端。
- 高峰期请求互相拖慢。

### 7.2 响应时间目标

| 场景 | 目标响应时间 | 实现方式 |
|---|---:|---|
| 简短文本教案 | 20-40 秒 | FastAPI 入队，Worker 调 Gemini |
| 复杂教案生成 | 40-90 秒 | RAG 检索 + 多语言生成 + 后台回传 |
| 图片识别投稿 | 1-2 分钟 | 图片下载 + Gemini 识别 + 草稿结构化 |
| 审核入库 | 人工流程 | 初审 + 复核 + 发布 |

### 7.3 可并行处理的任务

| 业务流程 | 可并行内容 |
|---|---|
| 文本教案生成 | 用户信息读取、语言识别、敏感检测、RAG 检索、本地案例检索 |
| 图片投稿 | 图片下载、图片识别、OCR/结构化抽取、敏感信息检测 |
| 投稿流程 | 先写 PostgreSQL，再异步创建 GitHub 文件或 PR |
| 审核后同步 | Markdown 校验、切片、embedding、向量库 upsert、管理员通知 |
| 高并发请求 | Webhook 快速入队，Worker Pool 横向扩展 |

## 8. 审核后台设计

第一版使用 Streamlit，不做复杂前端。核心原则是：

```text
Streamlit 只做界面
审核状态和发布逻辑放在 FastAPI/service 层
```

这样未来迁移到 React/Vue/Next.js 后台时，只需要替换前端，不需要重写核心业务。

### 8.1 登录与权限

管理员可以使用 Google Login 或 LINE Login。关键不是登录方式，而是后台必须有授权白名单。

```text
管理员登录
  ↓
系统获取 provider_user_id / email
  ↓
查询 admin_users 表
  ↓
判断 active、role、region_scope
  ↓
允许或拒绝访问
```

角色建议：

| 角色 | 权限 |
|---|---|
| reviewer | 初审 |
| senior_reviewer | 复核、发布 |
| admin | 用户管理、权限管理、系统配置 |

### 8.2 双审核流程

投稿状态流：

```text
draft
  ↓
pending_review
  ↓
first_approved
  ↓
second_approved
  ↓
published
  ↓
synced_to_github
  ↓
embedded
```

异常状态：

```text
needs_revision
rejected
sensitive_hold
sync_failed
embedding_failed
```

### 8.3 后台页面

第一版后台页面：

- 登录页。
- 投稿列表。
- 投稿详情。
- 图片/OCR 结果查看。
- 三语言内容编辑。
- 敏感标签管理。
- 初审通过。
- 复核通过。
- 退回修改。
- 发布到 GitHub。
- 向量同步状态查看。
- 基础用量统计。

## 9. 知识库与 RAG 设计

### 9.1 知识库格式

审核通过后的内容保存为 Markdown，并存入 GitHub private repo。

推荐目录结构：

```text
knowledge/
  yala/
    math/
      grade-4/
        fractions-rubber-latex.md
  pattani/
    science/
      grade-5/
        water-cycle-fishing-village.md
  narathiwat/
    language/
      grade-3/
        thai-vocabulary-market-context.md
```

推荐 Markdown front matter：

```yaml
---
id: knowledge_000001
region: pattani
subject: math
grade: 4
topic: fractions
languages: [th, ms, en]
sensitive_level: low
source: teacher_submission
review:
  first_reviewer: reviewer_001
  second_reviewer: reviewer_002
published_at: 2026-07-24
---
```

正文包含：

```text
# Title

## Thai

## Malay

## English

## Local Context

## Classroom Use

## Safety / Sensitivity Notes
```

### 9.2 RAG 检索流程

```text
教师请求
  ↓
解析 subject / grade / topic / region / language
  ↓
生成 query embedding
  ↓
pgvector 检索相似 chunk
  ↓
按地区、学科、年级、敏感等级过滤
  ↓
拼接 Prompt
  ↓
Gemini 生成教案
  ↓
返回 LINE Flex Message / 文本
```

### 9.3 为什么第一版用 pgvector

第一版使用 PostgreSQL + pgvector，而不是单独部署 Chroma/Milvus。

理由：

- 50 人试点数据量很小。
- 少部署一个服务。
- 业务数据和向量索引统一备份。
- pgvector 足够支撑几万到几十万 chunk 的早期检索。
- 后续可通过 retriever 抽象迁移到 Qdrant/Milvus。

检索接口应封装为：

```text
retriever.search(query, filters)
retriever.upsert(chunks)
retriever.delete(item_id)
```

避免业务代码和 pgvector 强绑定。

## 10. 安全、隐私与合规

### 10.1 隐私风险

系统可能处理：

- 教师 LINE userId。
- 学校名称。
- 学生姓名。
- 课堂照片。
- 教材图片。
- 宗教、民族、语言身份相关内容。
- 地区冲突相关敏感表达。

### 10.2 合规原则

系统应遵循泰国 PDPA 个人数据保护要求，并采取最小化收集原则。

建议：

- 不主动收集学生真实姓名。
- 图片上传前提示教师避免拍摄学生脸部和个人信息。
- 图片进入审核前进行 PII/敏感信息检测。
- 管理员分地区授权。
- 审核后台记录所有操作日志。
- 敏感内容必须初审 + 复核。
- 对外共享前必须脱敏。

### 10.3 敏感内容处理

敏感标签：

```text
student_identity
school_identity
religion
royal_family
ethnic_conflict
political_content
violence
personal_data
copyright_risk
```

敏感内容状态：

```text
sensitive_hold
needs_redaction
approved_private_only
approved_shared
rejected
```

## 11. 容量与性能估算

### 11.1 50 人试点

假设：

- 50 名教师。
- 30 名日活。
- 每人每天生成 2 次教案。
- 每天 60 次教案生成。
- 每天 10-20 次图片识别。
- 每月约 1,800 次文本生成，300-600 次图片识别。

该规模下：

- FastAPI 单个小实例足够。
- 1 个 Worker 足够，必要时加到 2 个。
- PostgreSQL 免费/低价套餐足够。
- pgvector 足够。
- GitHub private repo 足够。
- 人工审核能力比技术容量更容易成为瓶颈。

### 11.2 可扩展容量

| 阶段 | 建议架构 | 可承载规模 |
|---|---|---:|
| DEMO | FastAPI + PostgreSQL + pgvector + Streamlit | 10-50 教师 |
| 50 人试点 | 加 Redis Queue + Worker + Object Storage | 50-500 教师 |
| 区域试点 | 多 Worker + 托管 Postgres + 独立对象存储 + 监控 | 500-5,000 教师 |
| 大规模部署 | 专用向量库 + 正式 Web 后台 + SSO + 多实例部署 | 5,000-50,000+ 教师 |

### 11.3 第三方限制

LINE Messaging API 的多数接口有较高请求限制，例如官方文档显示部分端点示例为 2,000 requests/second，通常不是本项目早期瓶颈。

- LINE Messaging API reference: https://developers.line.biz/en/reference/messaging-api/

GitHub API 普通认证请求为小时级限额，内容创建还有 secondary limit。因此 GitHub 不应用在高频运行时状态写入，只用于审核通过后的知识库版本管理。

- GitHub REST API rate limits: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

Gemini 限额和价格随模型、项目、免费/付费层变化，真实试点前需要在 Google AI Studio 或 Cloud 项目中确认当前 quota。

- Gemini rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing

## 12. 成本估计

### 12.1 DEMO 成本

| 模块 | 服务选择 | 月成本估计 |
|---|---|---:|
| FastAPI | Render/Railway 免费或低价服务 | 0-10 美元 |
| PostgreSQL + pgvector | Supabase/Neon 免费层 | 0 美元 |
| Redis Queue | Upstash 免费/低用量 | 0 美元 |
| Object Storage | Supabase Storage / Cloudflare R2 / S3 低用量 | 0-5 美元 |
| GitHub private repo | GitHub Free | 0 美元 |
| Gemini | 免费额度或低用量 | 0-20 美元 |
| 合计 |  | 0-35 美元/月 |

### 12.2 50 人真实试点成本

| 模块 | 月成本估计 |
|---|---:|
| FastAPI Web Service | 7-25 美元 |
| Worker Service | 7-25 美元 |
| PostgreSQL + pgvector | 0-25 美元 |
| Redis Queue | 0-10 美元 |
| Object Storage | 0-10 美元 |
| Gemini API | 10-100 美元 |
| GitHub | 0-10 美元 |
| 监控/日志 | 0-20 美元 |
| 合计 | 50-200 美元/月 |

### 12.3 稳妥试点预算

如果希望提高稳定性，建议预算：

```text
150-300 美元/月：比较舒服的 50 人试点
300-500 美元/月：可加入更完整监控、备份、更多 AI 调用额度
```

### 12.4 费用来源与计算逻辑

参考价格来源：

- Supabase pricing: Free plan 包含基础资源，Pro 当前为 25 美元/月，含 8GB disk 和 7 天备份。https://supabase.com/pricing
- Upstash Redis pricing: Pay as You Go 计费，命令数、存储和带宽分开计费。https://upstash.com/pricing/redis
- Render pricing/free docs: Web 服务和 PostgreSQL 有免费/低价配置，免费服务存在休眠和资源限制。https://render.com/pricing 和 https://render.com/docs/free
- Neon pricing: 提供免费 Postgres 和按量升级选项。https://neon.com/pricing
- Gemini pricing: 按输入/输出 token 计费，不同 Flash/Pro 模型价格不同。https://ai.google.dev/gemini-api/docs/pricing

AI 成本粗算：

```text
一次普通教案：
输入约 3,000 tokens
输出约 1,500 tokens

如果使用低价 Flash/Lite 类模型：
单次可能低于 0.01 美元。

每月 2,000 次文本生成：
通常约 10-50 美元量级，具体取决于模型、输出长度、是否包含图片、是否使用搜索 grounding。
```

图片识别成本会高于纯文本，因为图片会计入输入 token，并且响应时间更长。

## 13. 最小 DEMO 范围

为了快速产出可演示代码，最小 DEMO 不需要一次性实现全部生产能力。

### 13.1 DEMO 必须实现

- LINE Webhook 接收文本。
- LINE signature 校验。
- 使用 LINE userId 识别教师。
- 文本教案生成。
- PostgreSQL 保存用户、请求和生成结果。
- pgvector 保存少量本地知识 chunk。
- RAG 检索后调用 Gemini。
- 返回 LINE 文本或简单 Flex Message。
- 图片上传后调用 Gemini 识别。
- 生成投稿草稿。
- Streamlit 后台查看投稿。
- 初审/复核状态切换。
- 审核通过后生成 Markdown。
- 写入 GitHub private repo。

### 13.2 DEMO 可暂缓

- 复杂 Rich Menu。
- 完整多租户权限。
- 正式 SSO。
- 高级监控。
- 自动脱敏模型。
- 多 Worker 横向扩展。
- 排行榜和积分。
- 正式 Web 后台。
- Qwen 本地部署。

## 14. 未来系统架构升级方向

### 14.1 从轻量审核后台升级为正式管理系统

当前：

```text
Streamlit Admin Dashboard
```

未来：

```text
React / Vue / Next.js Admin Portal
  ↓
FastAPI Admin API
  ↓
PostgreSQL
```

升级内容：

- 更完整的角色权限。
- 批量审核。
- 审核任务分配。
- 审核质量统计。
- 多地区管理员。
- 操作审计。
- 内容版本对比。

### 14.2 从 pgvector 升级为专用向量数据库

当前：

```text
PostgreSQL + pgvector
```

未来：

```text
Qdrant / Milvus / Weaviate
```

升级触发条件：

- 知识 chunk 超过几十万到百万级。
- 需要更高并发检索。
- 需要 hybrid search。
- 需要复杂 metadata filter。
- PostgreSQL 查询性能开始影响主业务。

### 14.3 从单后端升级为多服务架构

当前：

```text
FastAPI monolith + Worker
```

未来：

```text
API Service
AI Generation Service
Ingestion Service
Review Service
Notification Service
```

升级触发条件：

- 多团队协作。
- 需要独立扩展 AI worker。
- 需要更强任务隔离。
- 地区级部署增加。

### 14.4 从单模型升级为多模型路由

当前：

```text
Gemini
```

未来：

```text
Model Router
  ├── Gemini：多模态、泰语、快速试点
  ├── OpenAI：高质量生成备选
  ├── Typhoon / OpenThaiGPT：泰语本地化
  ├── SEA-LION：东南亚多语言
  └── Qwen：离线/私有部署
```

升级目标：

- 降低成本。
- 提高可用性。
- 支持离线部署。
- 提升泰语和马来语质量。
- 为南部马来语方言积累社区标注数据。

### 14.5 从 LINE Bot 扩展到多渠道

当前：

```text
LINE Official Account
```

未来：

```text
Channel Adapter
  ├── LINE：泰国
  ├── WhatsApp：印尼、非洲等地区
  ├── Zalo：越南
  └── Web / PWA：学校管理端
```

核心业务逻辑保持不变，只替换渠道适配层。

### 14.6 从知识共创升级为教师贡献生态

未来可加入：

- 投稿积分。
- 优秀贡献者认证。
- 地区知识库共建。
- 教师培训任务。
- 教学案例质量评分。
- 本地语言术语库维护。

需要注意：激励系统不能过早上线，否则可能引入低质量投稿。应先建立审核标准和质量评价机制。

## 15. 相似 GitHub 项目参考

目前没有发现完全相同的项目，即“LINE + 泰国南部教师 + 本土知识 RAG + 双审核 + GitHub 知识库”的完整开源实现。但有若干模块级项目可以借鉴。

### 15.1 LINE + Gemini

- kkdai/linebot-gemini-python  
  https://github.com/kkdai/linebot-gemini-python  
  可借鉴：LINE Bot、FastAPI、Gemini 文本/图片输入。

- jirawatee/LINE-Chatbot-x-Gemini-API  
  https://github.com/jirawatee/LINE-Chatbot-x-Gemini-API  
  可借鉴：LINE Messaging API 与 Gemini API 的基础集成。

- line/line-bot-sdk-python  
  https://github.com/line/line-bot-sdk-python  
  可借鉴：官方 Python SDK、Webhook、消息回复、push message。

### 15.2 FastAPI + RAG + Streamlit

- Zlash65/rag-bot-fastapi  
  https://github.com/Zlash65/rag-bot-fastapi  
  可借鉴：FastAPI、RAG、ChromaDB、Streamlit 的端到端结构。

- jodog0412/rag-chatbot-app-with-fastapi  
  https://github.com/jodog0412/rag-chatbot-app-with-fastapi  
  可借鉴：FastAPI + RAG API 结构。

- vitorccmanso/Rag-ChatBot  
  https://github.com/vitorccmanso/Rag-ChatBot  
  可借鉴：Gemini + RAG 的文档问答流程。

### 15.3 AI 教案生成

- DivanshiJain2005/AI-lesson-planner  
  https://github.com/DivanshiJain2005/AI-lesson-planner  
  可借鉴：Streamlit 教案生成界面和 prompt 结构。

- asiln/Lesson-Plan-Generator  
  https://github.com/asiln/Lesson-Plan-Generator  
  可借鉴：教师输入到结构化教案输出的基本流程。

### 15.4 学术参考

- LessonPlanner: Assisting Novice Teachers to Prepare Pedagogy-Driven Lesson Plans with Large Language Models  
  https://arxiv.org/abs/2408.01102  
  可借鉴：面向教师的交互式教案生成设计。

- LessonBench-V1: A Benchmark Dataset for Evaluating AI Lesson Generation Agents  
  https://arxiv.org/abs/2607.13041  
  可借鉴：未来评估教案生成质量的方法。

## 16. 项目结论

本项目的问题定义成立：泰国乡村教师存在行政负担重、备课时间不足、师资短缺和多语言教学困难等真实痛点；泰国 LINE 使用率高，使 LINE Bot 成为合理入口；Gemini 等多模态模型可以降低教案生成和图片投稿门槛；GitHub private repo 适合作为审核通过知识库的版本管理工具。

推荐最终架构为：

```text
LINE Bot
+ FastAPI
+ PostgreSQL
+ pgvector
+ Redis Queue
+ Worker Pool
+ Object Storage
+ Gemini
+ Private GitHub
+ Streamlit Admin Dashboard
```

第一阶段不追求复杂平台化，而是完成 50 名教师可真实试用的闭环：

```text
教师输入需求
  ↓
AI 生成本土化三语言教案
  ↓
教师投稿本地案例/图片
  ↓
管理员初审 + 复核
  ↓
发布到私有 GitHub 知识库
  ↓
同步到 pgvector
  ↓
反哺下一次教案生成
```

该架构可以用较低成本完成 DEMO，也可以在获得投资或政府/NGO 试点资源后，平滑升级为更完整的教育内容管理与 AI 辅助教学平台。
