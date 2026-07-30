import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { adminApi } from "../api";
import {
  ErrorState,
  KeyValue,
  LoadingState,
  PageHeader,
  RefreshButton,
  SectionCard,
  StatusChip,
} from "../components";
import { useKnowledge, useMe } from "../hooks";
import type { KnowledgeItem, KnowledgeVersion } from "../types";

type KnowledgeMutation =
  | { kind: "action"; id: string; action: string }
  | { kind: "check"; id: string; check: "sensitive-check" | "copyright-check" | "duplicate-check" }
  | { kind: "soft-delete"; id: string; reason?: string }
  | { kind: "restore"; id: string; versionNumber: number }
  | { kind: "publish"; id: string };

export function KnowledgePage() {
  const query = useKnowledge();
  const me = useMe();
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string>("");
  const [importOpen, setImportOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeItem | null>(null);
  const [reason, setReason] = useState("Rejected from admin UI.");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const selectedItem = query.data?.items.find((item) => item.id === selectedId) ?? null;
  const isScoped = Boolean(me.data?.is_scoped);
  const scopedSchoolIds = me.data?.school_ids ?? [];
  const selectedIsSchoolOwned =
    !isScoped ||
    (selectedItem?.owner_school_id ? scopedSchoolIds.includes(selectedItem.owner_school_id) : false);
  const canPublish = me.data?.role === "super_admin";
  const versions = useQuery({
    queryKey: ["knowledge-versions", selectedId],
    queryFn: () => adminApi.knowledgeVersions(selectedId),
    enabled: Boolean(selectedId),
  });
  const mutation = useMutation({
    mutationFn: (request: KnowledgeMutation) => {
      if (request.kind === "check") {
        return adminApi.knowledgeCheck(request.id, request.check);
      }
      if (request.kind === "soft-delete") {
        return adminApi.softDeleteKnowledge(request.id, request.reason);
      }
      if (request.kind === "restore") {
        return adminApi.restoreKnowledgeVersion(request.id, request.versionNumber);
      }
      if (request.kind === "publish") {
        return adminApi.publishKnowledgeItem(request.id);
      }
      return adminApi.knowledgeAction(request.id, request.action);
    },
    onSuccess: async (data) => {
      setResult(data);
      setDeleteTarget(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["knowledge"] }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-versions", selectedId] }),
        queryClient.invalidateQueries({ queryKey: ["overview"] }),
      ]);
    },
  });
  const importKnowledge = useMutation({
    mutationFn: (body: Record<string, unknown>) => adminApi.importKnowledge(body),
    onSuccess: async (data) => {
      setResult(data);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["knowledge"] }),
        queryClient.invalidateQueries({ queryKey: ["overview"] }),
      ]);
      setImportOpen(false);
    },
  });
  const columns = useMemo<GridColDef<KnowledgeItem>[]>(
    () => [
      { field: "title", headerName: "Title", flex: 1, minWidth: 240 },
      { field: "knowledge_type", headerName: "Type", width: 170 },
      { field: "subject", headerName: "Subject", width: 120 },
      { field: "topic", headerName: "Topic", width: 160 },
      {
        field: "review_status",
        headerName: "Review",
        width: 170,
        renderCell: ({ value }) => <StatusChip value={value} />,
      },
      {
        field: "vector_status",
        headerName: "Vector",
        width: 140,
        renderCell: ({ value }) => <StatusChip value={value} />,
      },
      { field: "visibility_scope", headerName: "Visibility", width: 160 },
    ],
    [],
  );
  const versionColumns = useMemo<GridColDef<KnowledgeVersion>[]>(
    () => [
      {
        field: "actions",
        headerName: "",
        width: 110,
        sortable: false,
        renderCell: ({ row }) => (
          <Button
            size="small"
            disabled={!selectedId || mutation.isPending}
            onClick={() =>
              mutation.mutate({
                kind: "restore",
                id: selectedId,
                versionNumber: row.version_number,
              })
            }
          >
            Restore
          </Button>
        ),
      },
      { field: "version_number", headerName: "Version", width: 100 },
      { field: "change_type", headerName: "Change", width: 140 },
      { field: "change_summary", headerName: "Summary", flex: 1, minWidth: 180 },
      {
        field: "created_at",
        headerName: "Created",
        width: 180,
        valueFormatter: (value) => formatDate(value as string | null),
      },
    ],
    [mutation, selectedId],
  );

  if (query.isLoading) {
    return <LoadingState />;
  }
  if (query.error) {
    return <ErrorState error={query.error} />;
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Knowledge"
        subtitle="Import, review, embed, version, and publish knowledge items."
        actions={
          <Stack direction="row" spacing={1}>
            <Button data-testid="open-import-knowledge" variant="contained" onClick={() => setImportOpen(true)}>
              Import knowledge
            </Button>
            <RefreshButton onClick={() => void query.refetch()} />
          </Stack>
        }
      />
      {mutation.error ? <Alert severity="error">{mutation.error.message}</Alert> : null}
      {importKnowledge.error ? <Alert severity="error">{importKnowledge.error.message}</Alert> : null}
      {result ? (
        <Alert severity="info">
          <JsonResult value={result} />
        </Alert>
      ) : null}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 1.45fr) minmax(360px, 0.55fr)" },
          gap: 2,
          alignItems: "start",
        }}
      >
        <SectionCard title="Knowledge Items">
          <DataGrid
            rows={query.data?.items ?? []}
            columns={columns}
            autoHeight
            disableRowSelectionOnClick
            pageSizeOptions={[25, 50, 100]}
            initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
            onRowClick={(params) => setSelectedId(String(params.id))}
            rowSelectionModel={selectedId ? [selectedId] : []}
            sx={{ bgcolor: "#fff", borderColor: "#e2e8f0" }}
          />
        </SectionCard>
        <Stack spacing={2}>
          <SectionCard title="Selected Item">
            {selectedItem ? (
              <Stack spacing={2}>
                <KeyValue label="ID" value={selectedItem.id} />
                <KeyValue label="Title" value={selectedItem.title} />
                <KeyValue label="Subject" value={selectedItem.subject || "-"} />
                <KeyValue label="Topic" value={selectedItem.topic || "-"} />
                <KeyValue label="Grade" value={formatGrade(selectedItem)} />
                <KeyValue label="Visibility" value={selectedItem.visibility_scope} />
                <KeyValue label="Owner school" value={selectedItem.owner_school_id || "-"} />
                <KeyValue label="Owner region" value={selectedItem.owner_region_id || "-"} />
                <KeyValue label="Review" value={<StatusChip value={selectedItem.review_status} />} />
                <KeyValue label="Vector" value={<StatusChip value={selectedItem.vector_status} />} />
                <KeyValue label="GitHub path" value={selectedItem.github_path || "-"} />
                <KeyValue label="GitHub commit" value={selectedItem.github_commit_sha || "-"} />
                <TextField
                  label="Reason"
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  multiline
                  minRows={2}
                />
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={mutation.isPending || !selectedIsSchoolOwned}
                    onClick={() =>
                      mutation.mutate({ kind: "check", id: selectedItem.id, check: "sensitive-check" })
                    }
                  >
                    Sensitive
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={mutation.isPending || !selectedIsSchoolOwned}
                    onClick={() =>
                      mutation.mutate({ kind: "check", id: selectedItem.id, check: "copyright-check" })
                    }
                  >
                    Copyright
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={mutation.isPending || !selectedIsSchoolOwned}
                    onClick={() =>
                      mutation.mutate({ kind: "check", id: selectedItem.id, check: "duplicate-check" })
                    }
                  >
                    Duplicate
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    disabled={mutation.isPending || isScoped}
                    onClick={() =>
                      mutation.mutate({
                        kind: "action",
                        id: selectedItem.id,
                        action: "approve-region-shared",
                      })
                    }
                  >
                    Approve region
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={mutation.isPending || !selectedIsSchoolOwned}
                    onClick={() =>
                      mutation.mutate({
                        kind: "action",
                        id: selectedItem.id,
                        action: "approve-school-private",
                      })
                    }
                  >
                    Approve school
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={mutation.isPending || !selectedIsSchoolOwned}
                    onClick={() =>
                      mutation.mutate({ kind: "action", id: selectedItem.id, action: "reembed" })
                    }
                  >
                    Re-embed
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={mutation.isPending || !canPublish}
                    onClick={() => mutation.mutate({ kind: "publish", id: selectedItem.id })}
                  >
                    Publish item
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    variant="outlined"
                    disabled={mutation.isPending || !selectedIsSchoolOwned}
                    onClick={() =>
                      mutation.mutate({ kind: "action", id: selectedItem.id, action: "reject" })
                    }
                  >
                    Reject
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    variant="outlined"
                    disabled={mutation.isPending || !selectedIsSchoolOwned}
                    onClick={() => setDeleteTarget(selectedItem)}
                  >
                    Delete
                  </Button>
                </Stack>
              </Stack>
            ) : (
              <Typography color="text.secondary">Select a knowledge item to review.</Typography>
            )}
          </SectionCard>
          <SectionCard title="Versions">
            {versions.isLoading ? (
              <LoadingState />
            ) : versions.error ? (
              <ErrorState error={versions.error} />
            ) : (
              <DataGrid
                rows={versions.data?.items ?? []}
                columns={versionColumns}
                autoHeight
                disableRowSelectionOnClick
                hideFooter={(versions.data?.items.length ?? 0) <= 10}
                pageSizeOptions={[10, 25]}
                initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              />
            )}
          </SectionCard>
        </Stack>
      </Box>
      <KnowledgeImportDialog
        open={importOpen}
        isScoped={isScoped}
        loading={importKnowledge.isPending}
        error={importKnowledge.error}
        onClose={() => setImportOpen(false)}
        onSubmit={(body) => importKnowledge.mutate(body)}
      />
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Knowledge</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <Alert severity="warning">
              This will remove the knowledge item from normal lists and RAG retrieval while keeping its
              audit history.
            </Alert>
            <KeyValue label="Title" value={deleteTarget?.title ?? "-"} />
            <TextField
              label="Reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              multiline
              minRows={2}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            disabled={mutation.isPending || !deleteTarget}
            onClick={() =>
              deleteTarget
                ? mutation.mutate({ kind: "soft-delete", id: deleteTarget.id, reason })
                : undefined
            }
          >
            {mutation.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}

function KnowledgeImportDialog({
  open,
  isScoped,
  loading,
  error,
  onClose,
  onSubmit,
}: {
  open: boolean;
  isScoped: boolean;
  loading: boolean;
  error: Error | null;
  onClose: () => void;
  onSubmit: (body: Record<string, unknown>) => void;
}) {
  const [title, setTitle] = useState("Fish sharing for fractions");
  const [knowledgeType, setKnowledgeType] = useState("local_example");
  const [subject, setSubject] = useState("math");
  const [topic, setTopic] = useState("fractions");
  const [targetGrade, setTargetGrade] = useState(4);
  const [gradeMin, setGradeMin] = useState(4);
  const [gradeMax, setGradeMax] = useState(4);
  const [contentEn, setContentEn] = useState("Use fish sharing at a local market to explain fractions.");
  const [contentTh, setContentTh] = useState("");
  const [contentMs, setContentMs] = useState("");
  const [sourceNote, setSourceNote] = useState("admin manual entry");
  const [verified, setVerified] = useState(false);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Import Knowledge</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error ? <Alert severity="error">{error.message}</Alert> : null}
          <TextField label="Title" value={title} onChange={(event) => setTitle(event.target.value)} />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              select
              label="Knowledge type"
              value={knowledgeType}
              onChange={(event) => setKnowledgeType(event.target.value)}
              fullWidth
            >
              {["local_example", "term_explanation", "teaching_activity"].map((value) => (
                <MenuItem key={value} value={value}>
                  {value}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Subject" value={subject} onChange={(event) => setSubject(event.target.value)} fullWidth />
            <TextField label="Topic" value={topic} onChange={(event) => setTopic(event.target.value)} fullWidth />
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              label="Target grade"
              type="number"
              value={targetGrade}
              onChange={(event) => setTargetGrade(Number(event.target.value))}
              fullWidth
            />
            <TextField
              label="Grade min"
              type="number"
              value={gradeMin}
              onChange={(event) => setGradeMin(Number(event.target.value))}
              fullWidth
            />
            <TextField
              label="Grade max"
              type="number"
              value={gradeMax}
              onChange={(event) => setGradeMax(Number(event.target.value))}
              fullWidth
            />
          </Stack>
          <TextField label="English content" value={contentEn} onChange={(event) => setContentEn(event.target.value)} multiline minRows={3} />
          <TextField label="Thai content" value={contentTh} onChange={(event) => setContentTh(event.target.value)} multiline minRows={3} />
          <TextField label="Local Malay content" value={contentMs} onChange={(event) => setContentMs(event.target.value)} multiline minRows={3} />
          <TextField label="Source note" value={sourceNote} onChange={(event) => setSourceNote(event.target.value)} />
          <TextField
            select
            label="Approve and embed immediately"
            value={String(verified)}
            disabled={isScoped}
            onChange={(event) => setVerified(event.target.value === "true")}
          >
            <MenuItem value="false">false</MenuItem>
            <MenuItem value="true">true</MenuItem>
          </TextField>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          data-testid="knowledge-import-submit"
          variant="contained"
          disabled={loading || !title}
          onClick={() =>
            onSubmit({
              knowledge_type: knowledgeType,
              title,
              region_code: "pattani",
              visibility_scope: "shared_region",
              subject,
              topic,
              target_grade: targetGrade,
              grade_min: gradeMin,
              grade_max: gradeMax,
              content_th: contentTh || null,
              content_ms: contentMs || null,
              content_en: contentEn || null,
              source_note: sourceNote || null,
              verified,
            })
          }
        >
          {loading ? "Importing..." : "Import knowledge"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function JsonResult({ value }: { value: unknown }) {
  return (
    <Box
      component="pre"
      sx={{
        m: 0,
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        fontFamily: "monospace",
      }}
    >
      {JSON.stringify(value, null, 2)}
    </Box>
  );
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}

function formatGrade(item: KnowledgeItem) {
  if (item.target_grade) {
    return item.target_grade;
  }
  if (item.grade_min && item.grade_max) {
    return `${item.grade_min}-${item.grade_max}`;
  }
  return "-";
}
