import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Pagination,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid, type GridColDef, type GridPaginationModel } from "@mui/x-data-grid";
import { useEffect, useMemo, useState } from "react";

import { ErrorState, KeyValue, LoadingState, PageHeader, RefreshButton, StatusChip } from "../components";
import { useSchools, useTeachers } from "../hooks";
import type { School, Teacher } from "../types";

const schoolPageSize = 12;

export function SchoolsPage() {
  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [schoolPage, setSchoolPage] = useState(1);
  const [selectedSchoolId, setSelectedSchoolId] = useState<string | null>(null);
  const [teacherPagination, setTeacherPagination] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 10,
  });

  const schools = useSchools({
    limit: schoolPageSize,
    offset: (schoolPage - 1) * schoolPageSize,
    q: search || undefined,
  });
  const schoolItems = useMemo(() => schools.data?.items ?? [], [schools.data?.items]);
  const activeSchool = useMemo(
    () => schoolItems.find((school) => school.id === selectedSchoolId) ?? schoolItems[0] ?? null,
    [schoolItems, selectedSchoolId],
  );

  useEffect(() => {
    if (!schoolItems.length) {
      setSelectedSchoolId(null);
      return;
    }
    if (!activeSchool) {
      setSelectedSchoolId(schoolItems[0].id);
    }
  }, [activeSchool, schoolItems]);

  const teachers = useTeachers({
    schoolId: activeSchool?.id,
    limit: teacherPagination.pageSize,
    offset: teacherPagination.page * teacherPagination.pageSize,
  });

  const teacherColumns = useMemo<GridColDef<Teacher>[]>(
    () => [
      { field: "line_user_id", headerName: "LINE User", flex: 1, minWidth: 260 },
      {
        field: "status",
        headerName: "Status",
        width: 130,
        renderCell: ({ value }) => <StatusChip value={value} />,
      },
      {
        field: "last_active_at",
        headerName: "Last active",
        width: 180,
        valueFormatter: (value) => formatDate(value as string | null),
      },
      { field: "region_id", headerName: "Region ID", width: 260 },
    ],
    [],
  );

  if (schools.isLoading) {
    return <LoadingState />;
  }
  if (schools.error) {
    return <ErrorState error={schools.error} />;
  }
  if (teachers.error) {
    return <ErrorState error={teachers.error} />;
  }

  const totalSchools = schools.data?.total ?? schoolItems.length;
  const totalSchoolPages = Math.max(1, Math.ceil(totalSchools / schoolPageSize));
  const totalTeachers = teachers.data?.total ?? 0;

  const applySearch = () => {
    setSearch(searchDraft.trim());
    setSchoolPage(1);
    setSelectedSchoolId(null);
  };

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Schools & Teachers"
        subtitle="Search schools, select one, then review teachers registered under that school."
        actions={
          <RefreshButton
            onClick={() => {
              void schools.refetch();
              void teachers.refetch();
            }}
          />
        }
      />
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "380px minmax(0, 1fr)" },
          gap: 2,
          alignItems: "start",
        }}
      >
        <Card variant="outlined">
          <CardContent>
            <Stack spacing={2}>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  School Directory
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {totalSchools} schools
                </Typography>
              </Box>
              <Stack direction="row" spacing={1}>
                <TextField
                  label="Search schools"
                  value={searchDraft}
                  onChange={(event) => setSearchDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      applySearch();
                    }
                  }}
                  size="small"
                  fullWidth
                />
                <Button variant="contained" onClick={applySearch}>
                  Search
                </Button>
              </Stack>
              <Divider />
              <Stack spacing={1}>
                {schoolItems.map((school) => (
                  <SchoolListItem
                    key={school.id}
                    school={school}
                    selected={school.id === activeSchool?.id}
                    onClick={() => {
                      setSelectedSchoolId(school.id);
                      setTeacherPagination({ page: 0, pageSize: teacherPagination.pageSize });
                    }}
                  />
                ))}
                {schoolItems.length === 0 ? (
                  <Typography color="text.secondary">No schools match this search.</Typography>
                ) : null}
              </Stack>
              <Pagination
                count={totalSchoolPages}
                page={schoolPage}
                onChange={(_, page) => {
                  setSchoolPage(page);
                  setSelectedSchoolId(null);
                  setTeacherPagination({ page: 0, pageSize: teacherPagination.pageSize });
                }}
                shape="rounded"
                size="small"
              />
            </Stack>
          </CardContent>
        </Card>

        <Stack spacing={2}>
          <Card variant="outlined">
            <CardContent>
              {activeSchool ? (
                <Stack spacing={2}>
                  <Stack
                    direction={{ xs: "column", sm: "row" }}
                    spacing={2}
                    alignItems={{ xs: "flex-start", sm: "center" }}
                    justifyContent="space-between"
                  >
                    <Box>
                      <Typography variant="h5" sx={{ fontWeight: 800 }}>
                        {activeSchool.name}
                      </Typography>
                      <Typography color="text.secondary">
                        {totalTeachers} registered teachers
                      </Typography>
                    </Box>
                    <StatusChip value={activeSchool.active ? "active" : "inactive"} />
                  </Stack>
                  <Box
                    sx={{
                      display: "grid",
                      gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" },
                      gap: 2,
                    }}
                  >
                    <KeyValue label="School ID" value={activeSchool.id} />
                    <KeyValue label="Region ID" value={activeSchool.region_id} />
                    <KeyValue label="Resource level" value={activeSchool.resource_level} />
                  </Box>
                </Stack>
              ) : (
                <Typography color="text.secondary">Select a school to view details.</Typography>
              )}
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Teachers in This School
                </Typography>
                <DataGrid
                  rows={teachers.data?.items ?? []}
                  columns={teacherColumns}
                  loading={teachers.isLoading}
                  autoHeight
                  disableRowSelectionOnClick
                  paginationMode="server"
                  rowCount={totalTeachers}
                  paginationModel={teacherPagination}
                  onPaginationModelChange={setTeacherPagination}
                  pageSizeOptions={[10, 25, 50]}
                  sx={{ borderColor: "#e2e8f0" }}
                />
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Box>
    </Stack>
  );
}

function SchoolListItem({
  school,
  selected,
  onClick,
}: {
  school: School;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      variant={selected ? "contained" : "outlined"}
      onClick={onClick}
      sx={{
        justifyContent: "space-between",
        textAlign: "left",
        minHeight: 66,
        px: 1.5,
        gap: 1.5,
      }}
    >
      <Box sx={{ minWidth: 0 }}>
        <Typography sx={{ fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis" }}>
          {school.name}
        </Typography>
        <Typography
          variant="caption"
          sx={{ display: "block", overflow: "hidden", textOverflow: "ellipsis" }}
        >
          {school.resource_level} resource
        </Typography>
      </Box>
      <Chip size="small" label={school.active ? "active" : "inactive"} />
    </Button>
  );
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}
