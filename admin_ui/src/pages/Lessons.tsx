import {
  Button,
  Drawer,
  FormControlLabel,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { adminApi } from "../api";
import { ErrorState, LoadingState, PageHeader, RefreshButton, StatusChip } from "../components";
import { useLessons } from "../hooks";
import type { Lesson } from "../types";

export function LessonsPage() {
  const query = useLessons();
  const [selectedLessonId, setSelectedLessonId] = useState<string | null>(null);
  const [includeSignedUrls, setIncludeSignedUrls] = useState(false);
  const detail = useQuery({
    queryKey: ["lesson", selectedLessonId, includeSignedUrls],
    queryFn: () => adminApi.lesson(selectedLessonId ?? "", includeSignedUrls),
    enabled: Boolean(selectedLessonId),
  });
  const columns = useMemo<GridColDef<Lesson>[]>(
    () => [
      {
        field: "status",
        headerName: "Status",
        width: 140,
        renderCell: ({ value }) => <StatusChip value={value} />,
      },
      { field: "subject", headerName: "Subject", width: 120 },
      { field: "grade", headerName: "Grade", width: 90 },
      { field: "topic", headerName: "Topic", flex: 1, minWidth: 220 },
      { field: "rag_confidence", headerName: "RAG", width: 110 },
      { field: "model", headerName: "Model", width: 170 },
      {
        field: "created_at",
        headerName: "Created",
        width: 180,
        valueFormatter: (value) => formatDate(value as string | null),
      },
      {
        field: "actions",
        headerName: "",
        width: 110,
        sortable: false,
        renderCell: ({ row }) => (
          <Button size="small" onClick={() => setSelectedLessonId(row.id)}>
            Details
          </Button>
        ),
      },
    ],
    [],
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
        title="Lessons"
        subtitle="Lesson requests created from LINE and admin debug flows."
        actions={<RefreshButton onClick={() => void query.refetch()} />}
      />
      <DataGrid
        rows={query.data?.items ?? []}
        columns={columns}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[25, 50, 100]}
        initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        sx={{ bgcolor: "#fff", borderColor: "#e2e8f0" }}
      />
      <Drawer
        anchor="right"
        open={Boolean(selectedLessonId)}
        onClose={() => setSelectedLessonId(null)}
        PaperProps={{ sx: { width: { xs: "100%", md: 720 }, p: 3 } }}
      >
        <Stack spacing={2}>
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            Lesson Detail
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={includeSignedUrls}
                onChange={(event) => setIncludeSignedUrls(event.target.checked)}
              />
            }
            label="Include signed DOCX URLs"
          />
          {detail.isLoading ? <LoadingState /> : null}
          {detail.error ? <ErrorState error={detail.error} /> : null}
          {detail.data ? (
            <Stack spacing={2}>
              <pre>{JSON.stringify({
                id: detail.data.id,
                status: detail.data.status,
                subject: detail.data.subject,
                grade: detail.data.grade,
                topic: detail.data.topic,
                rag_confidence: detail.data.rag_confidence,
                error_message: detail.data.error_message,
              }, null, 2)}</pre>
              <Typography variant="h6">DOCX Assets</Typography>
              <pre>{JSON.stringify(detail.data.docx_assets, null, 2)}</pre>
              <Typography variant="h6">Knowledge Refs</Typography>
              <pre>{JSON.stringify(detail.data.knowledge_refs, null, 2)}</pre>
              <Typography variant="h6">Structured Content</Typography>
              <pre>{JSON.stringify(detail.data.structured_content, null, 2)}</pre>
            </Stack>
          ) : null}
        </Stack>
      </Drawer>
    </Stack>
  );
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}
