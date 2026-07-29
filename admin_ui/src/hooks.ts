import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApi } from "./api";

export function useOverview() {
  return useQuery({
    queryKey: ["overview"],
    queryFn: adminApi.overview,
  });
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: adminApi.me,
  });
}

export function useSchools(params: { limit?: number; offset?: number; q?: string } = {}) {
  return useQuery({
    queryKey: ["schools", params],
    queryFn: () => adminApi.schools(params),
  });
}

export function useTeachers(params: { limit?: number; offset?: number; schoolId?: string } = {}) {
  return useQuery({
    queryKey: ["teachers", params],
    queryFn: () => adminApi.teachers(params),
  });
}

export function useLessons() {
  return useQuery({
    queryKey: ["lessons"],
    queryFn: adminApi.lessons,
  });
}

export function useSubmissions(status?: string) {
  return useQuery({
    queryKey: ["submissions", status ?? "all"],
    queryFn: () => adminApi.submissions(status),
  });
}

export function useSubmission(id: string | undefined) {
  return useQuery({
    queryKey: ["submission", id],
    queryFn: () => adminApi.submission(id ?? ""),
    enabled: Boolean(id),
  });
}

export function useKnowledge() {
  return useQuery({
    queryKey: ["knowledge"],
    queryFn: adminApi.knowledge,
  });
}

export function useAuditLogs() {
  return useQuery({
    queryKey: ["audit-logs"],
    queryFn: adminApi.auditLogs,
  });
}

export function useAdminUsers() {
  return useQuery({
    queryKey: ["admin-users"],
    queryFn: adminApi.adminUsers,
  });
}

export function useSubmissionAction(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ action, note }: { action: string; note?: string }) =>
      action === "publish-to-knowledge"
        ? adminApi.publishSubmission(id)
        : adminApi.submissionAction(id, action, note),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["submission", id] }),
        queryClient.invalidateQueries({ queryKey: ["submissions"] }),
        queryClient.invalidateQueries({ queryKey: ["overview"] }),
        queryClient.invalidateQueries({ queryKey: ["knowledge"] }),
      ]);
    },
  });
}
