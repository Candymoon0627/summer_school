import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { adminApi } from "../api";
import {
  ErrorState,
  KeyValue,
  LoadingState,
  PageHeader,
  SectionCard,
  StatusChip,
} from "../components";
import { useSubmission, useSubmissionAction } from "../hooks";
import type { SubmissionDetail } from "../types";

const reviewActions = [
  {
    action: "first-approve",
    label: "First approve",
    allowed: ["pending_review"],
  },
  {
    action: "second-approve",
    label: "Second approve",
    allowed: ["first_approved"],
  },
  {
    action: "publish-to-knowledge",
    label: "Publish to Knowledge",
    allowed: ["second_approved"],
  },
  {
    action: "request-revision",
    label: "Request revision",
    allowed: ["pending_review", "first_approved"],
  },
  {
    action: "reject",
    label: "Reject",
    allowed: ["pending_review", "first_approved", "second_approved"],
  },
];

export function SubmissionDetailPage({
  submissionId,
  navigate,
}: {
  submissionId: string;
  navigate: (path: string) => void;
}) {
  const query = useSubmission(submissionId);
  const mutation = useSubmissionAction(submissionId);
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [editOpen, setEditOpen] = useState(false);
  const updateSubmission = useMutation({
    mutationFn: (body: Record<string, unknown>) => adminApi.updateSubmission(submissionId, body),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["submission", submissionId] }),
        queryClient.invalidateQueries({ queryKey: ["submissions"] }),
        queryClient.invalidateQueries({ queryKey: ["overview"] }),
      ]);
      setEditOpen(false);
    },
  });

  if (query.isLoading) {
    return <LoadingState />;
  }
  if (query.error) {
    return <ErrorState error={query.error} />;
  }
  const submission = query.data;
  if (!submission) {
    return <Alert severity="warning">Submission not found.</Alert>;
  }

  const runAction = async (action: string) => {
    await mutation.mutateAsync({ action, note: note || undefined });
    setNote("");
  };

  return (
    <Stack spacing={3}>
      <PageHeader
        title={submission.title || "Untitled submission"}
        subtitle={`Submission ${submission.id}`}
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="contained" onClick={() => setEditOpen(true)}>
              Edit
            </Button>
            <Button onClick={() => navigate("/submissions")} variant="outlined">
              Back
            </Button>
          </Stack>
        }
      />
      {mutation.error ? <Alert severity="error">{mutation.error.message}</Alert> : null}
      {updateSubmission.error ? <Alert severity="error">{updateSubmission.error.message}</Alert> : null}
      <Grid container spacing={2}>
        <Grid item xs={12} md={8}>
          <SectionCard title="Content">
            <Stack spacing={3}>
              <KeyValue label="English" value={<Multiline value={submission.content_en} />} />
              <KeyValue label="Thai" value={<Multiline value={submission.content_th} />} />
              <KeyValue label="Local Malay" value={<Multiline value={submission.content_ms} />} />
              <KeyValue label="Local context" value={<Multiline value={submission.local_context} />} />
              <KeyValue label="Classroom use" value={<Multiline value={submission.classroom_use} />} />
            </Stack>
          </SectionCard>
        </Grid>
        <Grid item xs={12} md={4}>
          <Stack spacing={2}>
            <SectionCard title="Review State">
              <Stack spacing={2}>
                <KeyValue label="Status" value={<StatusChip value={submission.status} />} />
                <KeyValue label="Stage" value={submission.stage} />
                <KeyValue label="Knowledge item" value={submission.knowledge_item_id || "-"} />
                <KeyValue label="Sensitive" value={<StatusChip value={submission.sensitive_status} />} />
                <KeyValue label="Copyright" value={<StatusChip value={submission.copyright_status} />} />
                <KeyValue label="Duplicate" value={<StatusChip value={submission.duplicate_status} />} />
              </Stack>
            </SectionCard>
            <SectionCard title="Actions">
              <Stack spacing={2}>
                <TextField
                  label="Review note"
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  multiline
                  minRows={2}
                />
                {reviewActions.map((item) => (
                  <Button
                    key={item.action}
                    variant={item.action === "publish-to-knowledge" ? "contained" : "outlined"}
                    disabled={
                      mutation.isPending ||
                      !item.allowed.includes(submission.status)
                    }
                    onClick={() => void runAction(item.action)}
                  >
                    {mutation.isPending ? "Working..." : item.label}
                  </Button>
                ))}
              </Stack>
            </SectionCard>
          </Stack>
        </Grid>
      </Grid>
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <SectionCard title="Metadata">
            <Stack spacing={2}>
              <KeyValue label="Subject" value={submission.subject} />
              <KeyValue label="Topic" value={submission.topic} />
              <KeyValue label="Grade" value={submission.grade} />
              <KeyValue label="Knowledge type" value={submission.knowledge_type} />
              <KeyValue label="Visibility" value={submission.visibility_scope} />
              <KeyValue label="Source" value={submission.source_type} />
              <KeyValue label="Source note" value={submission.source_note} />
            </Stack>
          </SectionCard>
        </Grid>
        <Grid item xs={12} md={8}>
          <SectionCard title="Review History">
            <Stack spacing={1.5}>
              {submission.reviews.length === 0 ? (
                <Typography color="text.secondary">No review events yet.</Typography>
              ) : (
                submission.reviews.map((review) => (
                  <Box
                    key={review.id}
                    sx={{
                      border: "1px solid #e2e8f0",
                      borderRadius: 2,
                      p: 2,
                      bgcolor: "#fff",
                    }}
                  >
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                      <StatusChip value={review.action} />
                      <Chip size="small" label={`stage ${review.stage}`} />
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(review.created_at)}
                      </Typography>
                    </Stack>
                    <Typography variant="body2">
                      {review.before_status || "-"} {"->"} {review.after_status || "-"}
                    </Typography>
                    {review.note ? (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {review.note}
                      </Typography>
                    ) : null}
                  </Box>
                ))
              )}
            </Stack>
          </SectionCard>
        </Grid>
      </Grid>
      <SubmissionEditDialog
        open={editOpen}
        submission={submission}
        loading={updateSubmission.isPending}
        error={updateSubmission.error}
        onClose={() => setEditOpen(false)}
        onSubmit={(body) => updateSubmission.mutate(body)}
      />
    </Stack>
  );
}

function SubmissionEditDialog({
  open,
  submission,
  loading,
  error,
  onClose,
  onSubmit,
}: {
  open: boolean;
  submission: SubmissionDetail;
  loading: boolean;
  error: Error | null;
  onClose: () => void;
  onSubmit: (body: Record<string, unknown>) => void;
}) {
  const [title, setTitle] = useState(submission.title ?? "");
  const [knowledgeType, setKnowledgeType] = useState(submission.knowledge_type ?? "local_example");
  const [visibilityScope, setVisibilityScope] = useState(
    submission.visibility_scope ?? "shared_region",
  );
  const [subject, setSubject] = useState(submission.subject ?? "");
  const [topic, setTopic] = useState(submission.topic ?? "");
  const [gradeMin, setGradeMin] = useState(submission.grade_min ?? submission.target_grade ?? 4);
  const [gradeMax, setGradeMax] = useState(submission.grade_max ?? submission.target_grade ?? 4);
  const [contentEn, setContentEn] = useState(submission.content_en ?? "");
  const [contentTh, setContentTh] = useState(submission.content_th ?? "");
  const [contentMs, setContentMs] = useState(submission.content_ms ?? "");
  const [localContext, setLocalContext] = useState(submission.local_context ?? "");
  const [classroomUse, setClassroomUse] = useState(submission.classroom_use ?? "");
  const [sourceNote, setSourceNote] = useState(submission.source_note ?? "");

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Edit Submission</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error ? <Alert severity="error">{error.message}</Alert> : null}
          <TextField
            label="Title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
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
            <TextField
              select
              label="Visibility"
              value={visibilityScope}
              onChange={(event) => setVisibilityScope(event.target.value)}
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
            <TextField label="Subject" value={subject} onChange={(event) => setSubject(event.target.value)} fullWidth />
            <TextField label="Topic" value={topic} onChange={(event) => setTopic(event.target.value)} fullWidth />
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
          <TextField label="Local context" value={localContext} onChange={(event) => setLocalContext(event.target.value)} multiline minRows={2} />
          <TextField label="Classroom use" value={classroomUse} onChange={(event) => setClassroomUse(event.target.value)} multiline minRows={2} />
          <TextField label="Source note" value={sourceNote} onChange={(event) => setSourceNote(event.target.value)} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          data-testid="submission-save-edits"
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
              classroom_use: classroomUse || null,
              source_note: sourceNote || null,
            })
          }
        >
          {loading ? "Saving..." : "Save edits"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function Multiline({ value }: { value?: string | null }) {
  if (!value) {
    return "-";
  }
  return (
    <Typography component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", m: 0 }}>
      {value}
    </Typography>
  );
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}
