import { Stack } from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo } from "react";

import { ErrorState, LoadingState, PageHeader, RefreshButton, StatusChip } from "../components";
import { useAuditLogs } from "../hooks";
import type { AuditLog } from "../types";

export function AuditLogsPage() {
  const query = useAuditLogs();
  const columns = useMemo<GridColDef<AuditLog>[]>(
    () => [
      {
        field: "action",
        headerName: "Action",
        width: 220,
        renderCell: ({ value }) => <StatusChip value={value} />,
      },
      { field: "target_type", headerName: "Target", width: 180 },
      { field: "target_id", headerName: "Target ID", flex: 1, minWidth: 260 },
      {
        field: "created_at",
        headerName: "Created",
        width: 180,
        valueFormatter: (value) => formatDate(value as string | null),
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
        title="Audit Logs"
        subtitle="Recent admin and workflow actions."
        actions={<RefreshButton onClick={() => void query.refetch()} />}
      />
      <DataGrid
        rows={query.data?.items ?? []}
        columns={columns}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[25, 50]}
        initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        sx={{ bgcolor: "#fff", borderColor: "#e2e8f0" }}
      />
    </Stack>
  );
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}
