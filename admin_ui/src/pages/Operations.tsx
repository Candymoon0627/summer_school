import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { adminApi } from "../api";
import { ErrorState, LoadingState, PageHeader, SectionCard, StatusChip } from "../components";
import { useMe } from "../hooks";
import type { CoverageItem, PublishingCandidate } from "../types";

const subjects = ["math", "science"];

export function OperationsPage() {
  const me = useMe();
  const isScoped = Boolean(me.data?.is_scoped);
  return (
    <Stack spacing={3}>
      <PageHeader
        title="Operations"
        subtitle="Admin tools for setup, smoke checks, RAG, and publishing."
      />
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" },
          gap: 2,
          alignItems: "start",
        }}
      >
        <SchoolSetupPanel isScoped={isScoped} />
        <LessonDebugPanel />
        <RagSearchPanel />
        <PublishingPanel isScoped={isScoped} />
        <SentryPanel isScoped={isScoped} />
      </Box>
      <CoveragePanel />
    </Stack>
  );
}

function SentryPanel({ isScoped }: { isScoped: boolean }) {
  const sentry = useMutation({
    mutationFn: adminApi.sentryTest,
  });

  return (
    <SectionCard title="Sentry Smoke">
      <Stack spacing={2}>
        {sentry.error ? <Alert severity="error">{sentry.error.message}</Alert> : null}
        <Button
          data-testid="sentry-test"
          variant="outlined"
          disabled={isScoped || sentry.isPending}
          onClick={() => sentry.mutate()}
        >
          Send test event
        </Button>
        {sentry.data ? <JsonResult value={sentry.data} /> : null}
      </Stack>
    </SectionCard>
  );
}

function SchoolSetupPanel({ isScoped }: { isScoped: boolean }) {
  const [name, setName] = useState("");
  const [regionCode, setRegionCode] = useState("pattani");
  const [regionName, setRegionName] = useState("Pattani");
  const [resourceLevel, setResourceLevel] = useState("low");
  const [lineUserId, setLineUserId] = useState("");
  const [schoolCode, setSchoolCode] = useState("");
  const createSchool = useMutation({
    mutationFn: () =>
      adminApi.createSchool({
        name,
        region_code: regionCode,
        region_name: regionName,
        resource_level: resourceLevel,
      }),
    onSuccess: (result) => setSchoolCode(result.school_code),
  });
  const bindTeacher = useMutation({
    mutationFn: () => adminApi.bindTeacher(lineUserId, schoolCode),
  });

  return (
    <SectionCard title="School Setup">
      <Stack spacing={2}>
        {createSchool.error ? <Alert severity="error">{createSchool.error.message}</Alert> : null}
        {createSchool.data ? (
          <Alert severity="success">School code: {createSchool.data.school_code}</Alert>
        ) : null}
        <TextField label="School name" value={name} onChange={(e) => setName(e.target.value)} />
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            label="Region code"
            value={regionCode}
            onChange={(e) => setRegionCode(e.target.value)}
            fullWidth
          />
          <TextField
            label="Region name"
            value={regionName}
            onChange={(e) => setRegionName(e.target.value)}
            fullWidth
          />
          <TextField
            select
            label="Resource"
            value={resourceLevel}
            onChange={(e) => setResourceLevel(e.target.value)}
            fullWidth
          >
            {["low", "medium", "high"].map((value) => (
              <MenuItem key={value} value={value}>
                {value}
              </MenuItem>
            ))}
          </TextField>
        </Stack>
        <Button
          variant="contained"
          disabled={isScoped || !name || createSchool.isPending}
          onClick={() => createSchool.mutate()}
        >
          Create school
        </Button>
        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
          Bind test teacher
        </Typography>
        {bindTeacher.error ? <Alert severity="error">{bindTeacher.error.message}</Alert> : null}
        {bindTeacher.data ? <Alert severity="success">Teacher bind result recorded.</Alert> : null}
        <TextField
          label="LINE user ID"
          value={lineUserId}
          onChange={(e) => setLineUserId(e.target.value)}
        />
        <TextField
          label="School code"
          value={schoolCode}
          onChange={(e) => setSchoolCode(e.target.value)}
        />
        <Button
          variant="outlined"
          disabled={!lineUserId || !schoolCode || bindTeacher.isPending}
          onClick={() => bindTeacher.mutate()}
        >
          Bind teacher
        </Button>
      </Stack>
    </SectionCard>
  );
}

function LessonDebugPanel() {
  const [lineUserId, setLineUserId] = useState("");
  const [text, setText] = useState("Grade 4 science water cycle");
  const [enqueue, setEnqueue] = useState(false);
  const [lessonRequestId, setLessonRequestId] = useState("");
  const createLesson = useMutation({
    mutationFn: () => adminApi.createLessonRequest(lineUserId, text, enqueue),
    onSuccess: (result) => {
      const id = String(result.lesson_request_id ?? "");
      if (id) setLessonRequestId(id);
    },
  });
  const generateNow = useMutation({
    mutationFn: () => adminApi.generateLessonNow(lessonRequestId),
  });

  return (
    <SectionCard title="Lesson Debug">
      <Stack spacing={2}>
        {createLesson.error ? <Alert severity="error">{createLesson.error.message}</Alert> : null}
        {createLesson.data ? <JsonResult value={createLesson.data} /> : null}
        <TextField
          label="LINE user ID"
          value={lineUserId}
          onChange={(e) => setLineUserId(e.target.value)}
        />
        <TextField
          label="Lesson request text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          multiline
          minRows={2}
        />
        <FormControlLabel
          control={<Checkbox checked={enqueue} onChange={(e) => setEnqueue(e.target.checked)} />}
          label="Enqueue worker job"
        />
        <Button
          variant="contained"
          disabled={!lineUserId || !text || createLesson.isPending}
          onClick={() => createLesson.mutate()}
        >
          Create lesson request
        </Button>
        <TextField
          label="Lesson request ID"
          value={lessonRequestId}
          onChange={(e) => setLessonRequestId(e.target.value)}
        />
        <Button
          variant="outlined"
          disabled={!lessonRequestId || generateNow.isPending}
          onClick={() => generateNow.mutate()}
        >
          Generate now
        </Button>
        {generateNow.error ? <Alert severity="error">{generateNow.error.message}</Alert> : null}
        {generateNow.data ? <JsonResult value={generateNow.data} /> : null}
      </Stack>
    </SectionCard>
  );
}

function RagSearchPanel() {
  const [lineUserId, setLineUserId] = useState("");
  const [subject, setSubject] = useState("science");
  const [grade, setGrade] = useState(4);
  const [topic, setTopic] = useState("water cycle");
  const search = useMutation({
    mutationFn: () => adminApi.ragSearch({ lineUserId, subject, grade, topic }),
  });

  return (
    <SectionCard title="RAG Search">
      <Stack spacing={2}>
        {search.error ? <Alert severity="error">{search.error.message}</Alert> : null}
        <TextField
          label="LINE user ID"
          value={lineUserId}
          onChange={(e) => setLineUserId(e.target.value)}
        />
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            select
            label="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            fullWidth
          >
            {subjects.map((value) => (
              <MenuItem key={value} value={value}>
                {value}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Grade"
            type="number"
            value={grade}
            onChange={(e) => setGrade(Number(e.target.value))}
            fullWidth
          />
        </Stack>
        <TextField label="Topic" value={topic} onChange={(e) => setTopic(e.target.value)} />
        <Button
          variant="contained"
          disabled={!lineUserId || !subject || !topic || search.isPending}
          onClick={() => search.mutate()}
        >
          Search RAG
        </Button>
        {search.data ? <JsonResult value={search.data} /> : null}
      </Stack>
    </SectionCard>
  );
}

function PublishingPanel({ isScoped }: { isScoped: boolean }) {
  const [region, setRegion] = useState("pattani");
  const [subject, setSubject] = useState("science");
  const [allowTestData, setAllowTestData] = useState(false);
  const [allowWarnings, setAllowWarnings] = useState(false);
  const [confirmPublish, setConfirmPublish] = useState("");
  const candidates = useMutation({
    mutationFn: () => adminApi.publishingCandidates({ region, subject, allowTestData, limit: 50 }),
  });
  const publish = useMutation({
    mutationFn: (execute: boolean) =>
      adminApi.publishBatch({
        region,
        subject,
        allowTestData,
        allowWarnings,
        execute,
        limit: 50,
      }),
  });
  const columns: GridColDef<PublishingCandidate>[] = [
    { field: "title", headerName: "Title", flex: 1, minWidth: 220 },
    { field: "subject", headerName: "Subject", width: 120 },
    {
      field: "blocked",
      headerName: "Blocked",
      width: 110,
      renderCell: ({ value }) => <StatusChip value={value ? "blocked" : "ready"} />,
    },
    {
      field: "warnings",
      headerName: "Warnings",
      flex: 1,
      minWidth: 180,
      renderCell: ({ row }) => row.warnings.join(", "),
    },
  ];

  return (
    <SectionCard title="GitHub Publishing">
      <Stack spacing={2}>
        {(candidates.error || publish.error) ? (
          <Alert severity="error">{(candidates.error ?? publish.error)?.message}</Alert>
        ) : null}
        {isScoped ? (
          <Alert severity="info">GitHub publishing is available only to unscoped super admins.</Alert>
        ) : null}
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField label="Region" value={region} onChange={(e) => setRegion(e.target.value)} />
          <TextField
            select
            label="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            sx={{ minWidth: 160 }}
          >
            {subjects.map((value) => (
              <MenuItem key={value} value={value}>
                {value}
              </MenuItem>
            ))}
          </TextField>
        </Stack>
        <Stack direction="row" spacing={2}>
          <FormControlLabel
            control={
              <Checkbox
                checked={allowTestData}
                onChange={(e) => setAllowTestData(e.target.checked)}
              />
            }
            label="Allow test data"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={allowWarnings}
                onChange={(e) => setAllowWarnings(e.target.checked)}
              />
            }
            label="Allow warnings"
          />
        </Stack>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" disabled={isScoped} onClick={() => candidates.mutate()}>
            Load candidates
          </Button>
          <Button variant="outlined" disabled={isScoped} onClick={() => publish.mutate(false)}>
            Dry run
          </Button>
          <Button
            color="warning"
            variant="contained"
            disabled={isScoped || confirmPublish !== "PUBLISH"}
            onClick={() => publish.mutate(true)}
          >
            Execute publish
          </Button>
        </Stack>
        <TextField
          label="Type PUBLISH to enable execute"
          value={confirmPublish}
          onChange={(e) => setConfirmPublish(e.target.value)}
        />
        {publish.data ? <JsonResult value={publish.data} /> : null}
        <DataGrid
          rows={candidates.data?.items ?? []}
          columns={columns}
          autoHeight
          disableRowSelectionOnClick
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </Stack>
    </SectionCard>
  );
}

function CoveragePanel() {
  const query = useQuery({
    queryKey: ["coverage"],
    queryFn: adminApi.coverage,
  });
  const rows = query.data?.items ?? [];
  const columns: GridColDef<CoverageItem>[] = Object.keys(rows[0] ?? {}).map((key) => ({
    field: key,
    headerName: key.replaceAll("_", " "),
    flex: 1,
    minWidth: 140,
  }));

  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState error={query.error} />;

  return (
    <SectionCard title="Knowledge Coverage">
      <DataGrid
        rows={rows.map((row, index) => ({ id: index, ...row }))}
        columns={columns}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[10, 25, 50]}
        initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
      />
    </SectionCard>
  );
}

function JsonResult({ value }: { value: unknown }) {
  return (
    <Box
      component="pre"
      sx={{
        m: 0,
        p: 1.5,
        borderRadius: 2,
        bgcolor: "#f8fafc",
        border: "1px solid #e2e8f0",
        whiteSpace: "pre-wrap",
        maxHeight: 260,
        overflow: "auto",
      }}
    >
      {JSON.stringify(value, null, 2)}
    </Box>
  );
}
