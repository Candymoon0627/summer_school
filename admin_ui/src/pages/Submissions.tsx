import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { adminApi } from "../api";
import { ErrorState, LoadingState, PageHeader, RefreshButton, StatusChip } from "../components";
import { useSubmissions } from "../hooks";
import type { SubmissionSummary } from "../types";

const statusFilters = [
  { label: "All", value: "" },
  { label: "Pending review", value: "pending_review" },
  { label: "First approved", value: "first_approved" },
  { label: "Second approved", value: "second_approved" },
  { label: "Embedded", value: "embedded" },
  { label: "Needs revision", value: "needs_revision" },
  { label: "Rejected", value: "rejected" },
  { label: "Deleted", value: "deleted" },
];

export function SubmissionsPage({ navigate }: { navigate: (path: string) => void }) {
  const [status, setStatus] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const query = useSubmissions(status || undefined);
  const queryClient = useQueryClient();
  const createSubmission = useMutation({
    mutationFn: (body: Record<string, unknown>) => adminApi.createSubmission(body),
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ["submissions"] });
      setCreateOpen(false);
      navigate(`/submissions/${result.id}`);
    },
  });

  const columns = useMemo<GridColDef<SubmissionSummary>[]>(
    () => [
      {
        field: "status",
        headerName: "Status",
        width: 150,
        renderCell: ({ value }) => <StatusChip value={value} />,
      },
      { field: "title", headerName: "Title", flex: 1, minWidth: 220 },
      { field: "subject", headerName: "Subject", width: 120 },
      { field: "topic", headerName: "Topic", width: 160 },
      { field: "grade", headerName: "Grade", width: 90 },
      { field: "visibility_scope", headerName: "Visibility", width: 150 },
      {
        field: "knowledge_item_id",
        headerName: "Knowledge",
        width: 130,
        valueFormatter: (value) => (value ? "published" : "-"),
      },
      { field: "source_type", headerName: "Source", width: 120 },
      {
        field: "created_at",
        headerName: "Created",
        width: 180,
        valueFormatter: (value) => formatDate(value as string | null),
      },
      {
        field: "actions",
        headerName: "",
        sortable: false,
        width: 120,
        renderCell: ({ row }) => (
          <Button size="small" onClick={() => navigate(`/submissions/${row.id}`)}>
            Review
          </Button>
        ),
      },
    ],
    [navigate],
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
        title="Submissions"
        subtitle="Review teacher contributions and publish approved content into the knowledge base."
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="contained" onClick={() => setCreateOpen(true)}>
              Create submission
            </Button>
            <RefreshButton onClick={() => void query.refetch()} />
          </Stack>
        }
      />
      <TextField
        select
        label="Status"
        value={status}
        onChange={(event) => setStatus(event.target.value)}
        sx={{ width: 260 }}
      >
        {statusFilters.map((item) => (
          <MenuItem key={item.value} value={item.value}>
            {item.label}
          </MenuItem>
        ))}
      </TextField>
      <DataGrid
        rows={query.data?.items ?? []}
        columns={columns}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[25, 50, 100]}
        initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        sx={{ bgcolor: "#fff", borderColor: "#e2e8f0" }}
      />
      <SubmissionCreateDialog
        open={createOpen}
        error={createSubmission.error}
        loading={createSubmission.isPending}
        onClose={() => setCreateOpen(false)}
        onSubmit={(body) => createSubmission.mutate(body)}
      />
    </Stack>
  );
}

function SubmissionCreateDialog({
  open,
  error,
  loading,
  onClose,
  onSubmit,
}: {
  open: boolean;
  error: Error | null;
  loading: boolean;
  onClose: () => void;
  onSubmit: (body: Record<string, unknown>) => void;
}) {
  const [title, setTitle] = useState("Local market example");
  const [knowledgeType, setKnowledgeType] = useState("local_example");
  const [visibilityScope, setVisibilityScope] = useState("shared_region");
  const [subject, setSubject] = useState("math");
  const [topic, setTopic] = useState("fractions");
  const [gradeMin, setGradeMin] = useState(4);
  const [gradeMax, setGradeMax] = useState(4);
  const [contentEn, setContentEn] = useState("");
  const [contentTh, setContentTh] = useState("");
  const [contentMs, setContentMs] = useState("");
  const [localContext, setLocalContext] = useState("");

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create Submission</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error ? <Alert severity="error">{error.message}</Alert> : null}
          <TextField label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              select
              label="Knowledge type"
              value={knowledgeType}
              onChange={(e) => setKnowledgeType(e.target.value)}
              fullWidth
            >
              {["local_example", "term_explanation", "teaching_activity"].map((value) => (
                <MenuItem key={value} value={value}>
                  {value}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Visibility"
              value={visibilityScope}
              onChange={(e) => setVisibilityScope(e.target.value)}
              fullWidth
            >
              {["shared_region", "private_school", "shared_global"].map((value) => (
                <MenuItem key={value} value={value}>
                  {value}
                </MenuItem>
              ))}
            </TextField>
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} fullWidth />
            <TextField label="Topic" value={topic} onChange={(e) => setTopic(e.target.value)} fullWidth />
            <TextField
              label="Grade min"
              type="number"
              value={gradeMin}
              onChange={(e) => setGradeMin(Number(e.target.value))}
              fullWidth
            />
            <TextField
              label="Grade max"
              type="number"
              value={gradeMax}
              onChange={(e) => setGradeMax(Number(e.target.value))}
              fullWidth
            />
          </Stack>
          <TextField label="English content" value={contentEn} onChange={(e) => setContentEn(e.target.value)} multiline minRows={3} />
          <TextField label="Thai content" value={contentTh} onChange={(e) => setContentTh(e.target.value)} multiline minRows={3} />
          <TextField label="Local Malay content" value={contentMs} onChange={(e) => setContentMs(e.target.value)} multiline minRows={3} />
          <TextField label="Local context" value={localContext} onChange={(e) => setLocalContext(e.target.value)} multiline minRows={2} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          data-testid="submission-create-submit"
          variant="contained"
          disabled={loading || !title}
          onClick={() =>
            onSubmit({
              title,
              knowledge_type: knowledgeType,
              visibility_scope: visibilityScope,
              subject,
              topic,
              target_grade: gradeMin === gradeMax ? gradeMin : null,
              grade_min: gradeMin,
              grade_max: gradeMax,
              content_en: contentEn || null,
              content_th: contentTh || null,
              content_ms: contentMs || null,
              local_context: localContext || null,
              submit: true,
            })
          }
        >
          {loading ? "Creating..." : "Create and submit"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}
