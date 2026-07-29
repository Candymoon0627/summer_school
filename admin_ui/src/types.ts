export type AdminMe = {
  admin_id: string | null;
  username: string;
  role: string;
  school_ids: string[];
  region_ids: string[];
  is_scoped: boolean;
};

export type AdminUser = {
  id: string;
  email: string;
  role: string;
  school_ids: string[];
  region_ids: string[];
  active: boolean;
  created_at: string | null;
};

export type Overview = {
  counts: Record<string, number>;
  lesson_status: Record<string, number>;
  knowledge_review_status: Record<string, number>;
  knowledge_vector_status: Record<string, number>;
  submission_status: Record<string, number>;
};

export type School = {
  id: string;
  name: string;
  region_id: string;
  active: boolean;
  resource_level: string;
  created_at: string | null;
};

export type Teacher = {
  id: string;
  line_user_id: string;
  school_id: string;
  region_id: string;
  status: string;
  last_active_at: string | null;
  created_at: string | null;
};

export type Lesson = {
  id: string;
  teacher_id: string;
  school_id: string;
  region_id: string;
  subject: string | null;
  grade: number | null;
  topic: string | null;
  status: string;
  rag_confidence: string | null;
  model: string | null;
  token_input: number | null;
  token_output: number | null;
  error_message: string | null;
  created_at: string | null;
  completed_at: string | null;
};

export type LessonDetail = {
  id: string;
  raw_user_input: string;
  subject: string | null;
  grade: number | null;
  topic: string | null;
  status: string;
  rag_confidence: string | null;
  error_message: string | null;
  structured_content: Record<string, unknown> | null;
  docx_assets: Array<{
    id: string;
    purpose: string;
    object_key: string;
    file_size: number | null;
    storage_provider: string;
    signed_url?: string;
  }>;
  knowledge_refs: Array<{
    knowledge_item_id: string;
    knowledge_item_version_id: string | null;
    chunk_id: string | null;
    rank: number;
    relevance_score: number | null;
  }>;
};

export type SubmissionSummary = {
  id: string;
  status: string;
  stage: number;
  source_type: string;
  teacher_id: string | null;
  school_id: string | null;
  region_id: string | null;
  knowledge_item_id: string | null;
  title: string | null;
  knowledge_type: string | null;
  subject: string | null;
  topic: string | null;
  grade: string | number | null;
  visibility_scope: string | null;
  created_at: string | null;
  submitted_at: string | null;
  published_at: string | null;
};

export type SubmissionReview = {
  id: string;
  stage: number;
  action: string;
  reviewer_username: string;
  reviewer_role: string;
  note: string | null;
  before_status: string | null;
  after_status: string | null;
  created_at: string | null;
};

export type SubmissionDetail = SubmissionSummary & {
  target_grade: number | null;
  grade_min: number | null;
  grade_max: number | null;
  content_th: string | null;
  content_ms: string | null;
  content_en: string | null;
  local_context: string | null;
  classroom_use: string | null;
  safety_notes: string | null;
  source_note: string | null;
  sensitive_status: string | null;
  copyright_status: string | null;
  duplicate_status: string | null;
  first_reviewed_at: string | null;
  second_reviewed_at: string | null;
  embedded_at: string | null;
  reviews: SubmissionReview[];
};

export type KnowledgeItem = {
  id: string;
  owner_school_id: string | null;
  owner_region_id: string | null;
  title: string;
  knowledge_type: string;
  subject: string | null;
  topic: string | null;
  target_grade: number | null;
  grade_min: number | null;
  grade_max: number | null;
  visibility_scope: string;
  review_status: string;
  vector_status: string;
  github_path: string | null;
  github_commit_sha: string | null;
};

export type KnowledgeVersion = {
  id: string;
  version_number: number;
  change_type: string;
  change_summary: string | null;
  created_at: string | null;
};

export type AuditLog = {
  id: string;
  action: string;
  target_type: string;
  target_id: string | null;
  created_at: string | null;
};

export type CoverageItem = Record<string, string | number | boolean | null>;

export type PublishingCandidate = {
  id: string;
  title: string;
  subject: string | null;
  region_code: string | null;
  github_path: string | null;
  warnings: string[];
  blocked: boolean;
};

export type RagSearchResult = {
  confidence?: string;
  status?: string;
  items: Array<{
    knowledge_item_id: string;
    title: string;
    score: number;
  }>;
};
