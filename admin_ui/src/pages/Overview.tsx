import { Box, Grid, Stack } from "@mui/material";

import {
  ErrorState,
  LoadingState,
  MetricCard,
  PageHeader,
  RefreshButton,
  SectionCard,
  StatusChip,
} from "../components";
import { useAuditLogs, useOverview } from "../hooks";

export function OverviewPage() {
  const overview = useOverview();
  const auditLogs = useAuditLogs();

  if (overview.isLoading) {
    return <LoadingState />;
  }
  if (overview.error) {
    return <ErrorState error={overview.error} />;
  }

  const data = overview.data;

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Overview"
        subtitle="Operational snapshot for LINE lessons, teacher submissions, and RAG knowledge."
        actions={<RefreshButton onClick={() => void overview.refetch()} />}
      />
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(2, minmax(0, 1fr))",
            md: "repeat(5, minmax(0, 1fr))",
          },
          gap: 2,
        }}
      >
        {Object.entries(data?.counts ?? {}).map(([key, value]) => (
          <Box key={key}>
            <MetricCard label={labelize(key)} value={value} />
          </Box>
        ))}
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <StatusSection title="Submission Status" values={data?.submission_status ?? {}} />
        </Grid>
        <Grid item xs={12} md={4}>
          <StatusSection title="Lesson Status" values={data?.lesson_status ?? {}} />
        </Grid>
        <Grid item xs={12} md={4}>
          <StatusSection title="Knowledge Vectors" values={data?.knowledge_vector_status ?? {}} />
        </Grid>
      </Grid>
      <SectionCard title="Recent Audit Logs">
        <Stack spacing={1}>
          {(auditLogs.data?.items ?? []).slice(0, 8).map((log) => (
            <Box
              key={log.id}
              sx={{
                display: "grid",
                gridTemplateColumns: "160px 1fr 170px",
                gap: 2,
                py: 1,
                borderBottom: "1px solid #e2e8f0",
              }}
            >
              <StatusChip value={log.action} />
              <span>{log.target_type}</span>
              <span>{formatDate(log.created_at)}</span>
            </Box>
          ))}
        </Stack>
      </SectionCard>
    </Stack>
  );
}

function StatusSection({ title, values }: { title: string; values: Record<string, number> }) {
  return (
    <SectionCard title={title}>
      <Stack spacing={1}>
        {Object.entries(values).map(([key, value]) => (
          <Box
            key={key}
            sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
          >
            <StatusChip value={key} />
            <strong>{value}</strong>
          </Box>
        ))}
      </Stack>
    </SectionCard>
  );
}

function labelize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}
