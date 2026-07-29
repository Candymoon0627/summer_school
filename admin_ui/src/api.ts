import type {
  AdminMe,
  AdminUser,
  AuditLog,
  CoverageItem,
  KnowledgeItem,
  KnowledgeVersion,
  Lesson,
  LessonDetail,
  Overview,
  PublishingCandidate,
  RagSearchResult,
  School,
  SubmissionDetail,
  SubmissionSummary,
  Teacher,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const AUTH_KEY = "edu_ai_admin_auth";

type ItemsResponse<T> = {
  items: T[];
  total?: number;
  limit?: number;
  offset?: number;
};

type RequestOptions = {
  method?: string;
  body?: unknown;
};

export type LoginInput = {
  username: string;
  password: string;
};

export function getAuthHeader(): string | null {
  return localStorage.getItem(AUTH_KEY);
}

export function setCredentials({ username, password }: LoginInput): void {
  localStorage.setItem(AUTH_KEY, `Basic ${btoa(`${username}:${password}`)}`);
}

export function clearCredentials(): void {
  localStorage.removeItem(AUTH_KEY);
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers();
  headers.set("Accept", "application/json");
  const auth = getAuthHeader();
  if (auth) {
    headers.set("Authorization", auth);
  }
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      // Keep HTTP status text when the API returns an empty body.
    }
    throw new Error(detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function login(input: LoginInput): Promise<AdminMe> {
  setCredentials(input);
  try {
    return await apiRequest<AdminMe>("/admin/me");
  } catch (error) {
    clearCredentials();
    throw error;
  }
}

export const adminApi = {
  me: () => apiRequest<AdminMe>("/admin/me"),
  overview: () => apiRequest<Overview>("/admin/overview"),
  adminUsers: () => apiRequest<ItemsResponse<AdminUser>>("/admin/users?limit=100"),
  createAdminUser: (body: {
    email: string;
    password: string;
    role: string;
    school_ids: string[];
    region_ids: string[];
    active: boolean;
  }) =>
    apiRequest<AdminUser>("/admin/users", {
      method: "POST",
      body,
    }),
  updateAdminUser: (id: string, body: Record<string, unknown>) =>
    apiRequest<AdminUser>(`/admin/users/${id}`, {
      method: "PATCH",
      body,
    }),
  schools: (params: { limit?: number; offset?: number; q?: string } = {}) => {
    const search = new URLSearchParams({
      limit: String(params.limit ?? 25),
      offset: String(params.offset ?? 0),
    });
    if (params.q) {
      search.set("q", params.q);
    }
    return apiRequest<ItemsResponse<School>>(`/admin/schools?${search.toString()}`);
  },
  teachers: (params: { limit?: number; offset?: number; schoolId?: string } = {}) => {
    const search = new URLSearchParams({
      limit: String(params.limit ?? 25),
      offset: String(params.offset ?? 0),
    });
    if (params.schoolId) {
      search.set("school_id", params.schoolId);
    }
    return apiRequest<ItemsResponse<Teacher>>(`/admin/teachers?${search.toString()}`);
  },
  lessons: () => apiRequest<ItemsResponse<Lesson>>("/admin/lessons?limit=100"),
  lesson: (id: string, includeSignedUrls = false) =>
    apiRequest<LessonDetail>(
      `/admin/lessons/${id}?include_signed_urls=${String(includeSignedUrls)}`,
    ),
  submissions: (status?: string) =>
    apiRequest<ItemsResponse<SubmissionSummary>>(
      `/admin/submissions?limit=100${status ? `&status=${encodeURIComponent(status)}` : ""}`,
    ),
  submission: (id: string) => apiRequest<SubmissionDetail>(`/admin/submissions/${id}`),
  submissionAction: (id: string, action: string, note?: string) =>
    apiRequest<SubmissionDetail>(`/admin/submissions/${id}/${action}`, {
      method: "POST",
      body: note ? { note } : {},
    }),
  publishSubmission: (id: string) =>
    apiRequest<SubmissionDetail>(`/admin/submissions/${id}/publish-to-knowledge`, {
      method: "POST",
    }),
  knowledge: () => apiRequest<ItemsResponse<KnowledgeItem>>("/admin/knowledge?limit=100"),
  knowledgeVersions: (id: string) =>
    apiRequest<ItemsResponse<KnowledgeVersion>>(`/admin/knowledge/${id}/versions`),
  importKnowledge: (body: Record<string, unknown>) =>
    apiRequest<Record<string, unknown>>("/admin/knowledge/seed", {
      method: "POST",
      body,
    }),
  createSubmission: (body: Record<string, unknown>) =>
    apiRequest<SubmissionSummary>("/admin/submissions", {
      method: "POST",
      body,
    }),
  updateSubmission: (id: string, body: Record<string, unknown>) =>
    apiRequest<SubmissionDetail>(`/admin/submissions/${id}`, {
      method: "PATCH",
      body,
    }),
  auditLogs: () => apiRequest<ItemsResponse<AuditLog>>("/admin/audit-logs?limit=50"),
  createSchool: (body: {
    name: string;
    region_code: string;
    region_name: string;
    country_code?: string;
    school_type?: string;
    resource_level: string;
  }) => apiRequest<{ school_id: string; school_code: string }>("/admin/schools", {
    method: "POST",
    body,
  }),
  bindTeacher: (lineUserId: string, schoolCode: string) =>
    apiRequest<Record<string, unknown>>(
      `/admin/dev/bind-teacher?line_user_id=${encodeURIComponent(
        lineUserId,
      )}&school_code=${encodeURIComponent(schoolCode)}`,
      { method: "POST" },
    ),
  createLessonRequest: (lineUserId: string, text: string, enqueue: boolean) =>
    apiRequest<Record<string, unknown>>(
      `/admin/dev/lesson-request?line_user_id=${encodeURIComponent(
        lineUserId,
      )}&text=${encodeURIComponent(text)}&enqueue=${String(enqueue)}`,
      { method: "POST" },
    ),
  generateLessonNow: (lessonRequestId: string) =>
    apiRequest<Record<string, unknown>>(
      `/admin/dev/lesson-requests/${lessonRequestId}/generate-now`,
      { method: "POST" },
    ),
  coverage: () => apiRequest<ItemsResponse<CoverageItem>>("/admin/coverage?limit=1000"),
  ragSearch: (params: { lineUserId: string; subject: string; grade: number; topic: string }) =>
    apiRequest<RagSearchResult>(
      `/admin/dev/rag-search?line_user_id=${encodeURIComponent(
        params.lineUserId,
      )}&subject=${encodeURIComponent(params.subject)}&grade=${params.grade}&topic=${encodeURIComponent(
        params.topic,
      )}`,
    ),
  publishingCandidates: (params: {
    region?: string;
    subject?: string;
    allowTestData?: boolean;
    limit?: number;
  }) => {
    const search = new URLSearchParams({
      limit: String(params.limit ?? 50),
      allow_test_data: String(Boolean(params.allowTestData)),
    });
    if (params.region) search.set("region", params.region);
    if (params.subject) search.set("subject", params.subject);
    return apiRequest<ItemsResponse<PublishingCandidate>>(
      `/admin/publishing/candidates?${search.toString()}`,
    );
  },
  publishBatch: (params: {
    region?: string;
    subject?: string;
    allowTestData?: boolean;
    allowWarnings?: boolean;
    execute?: boolean;
    limit?: number;
  }) => {
    const search = new URLSearchParams({
      limit: String(params.limit ?? 50),
      allow_test_data: String(Boolean(params.allowTestData)),
      allow_warnings: String(Boolean(params.allowWarnings)),
      execute: String(Boolean(params.execute)),
    });
    if (params.region) search.set("region", params.region);
    if (params.subject) search.set("subject", params.subject);
    return apiRequest<Record<string, unknown>>(`/admin/publishing/batch?${search.toString()}`, {
      method: "POST",
    });
  },
  knowledgeAction: (id: string, action: string) =>
    apiRequest<Record<string, unknown>>(`/admin/knowledge/${id}/${action}`, { method: "POST" }),
  knowledgeCheck: (id: string, check: "sensitive-check" | "copyright-check" | "duplicate-check") =>
    apiRequest<Record<string, unknown>>(`/admin/knowledge/${id}/${check}`, { method: "POST" }),
  softDeleteKnowledge: (id: string, reason?: string) => {
    const search = new URLSearchParams();
    if (reason) search.set("reason", reason);
    const suffix = search.toString() ? `?${search.toString()}` : "";
    return apiRequest<Record<string, unknown>>(`/admin/knowledge/${id}/soft-delete${suffix}`, {
      method: "POST",
    });
  },
  restoreKnowledgeVersion: (id: string, versionNumber: number) =>
    apiRequest<Record<string, unknown>>(`/admin/knowledge/${id}/restore/${versionNumber}`, {
      method: "POST",
    }),
  publishKnowledgeItem: (id: string) =>
    apiRequest<Record<string, unknown>>(`/admin/knowledge/${id}/publish`, { method: "POST" }),
  sentryTest: () =>
    apiRequest<Record<string, unknown>>("/admin/dev/sentry-test", { method: "POST" }),
};
