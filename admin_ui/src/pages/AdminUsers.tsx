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
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { adminApi } from "../api";
import { ErrorState, LoadingState, PageHeader, RefreshButton, StatusChip } from "../components";
import { useAdminUsers } from "../hooks";
import type { AdminUser } from "../types";

export function AdminUsersPage() {
  const query = useAdminUsers();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const createUser = useMutation({
    mutationFn: adminApi.createAdminUser,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setCreateOpen(false);
    },
  });
  const updateUser = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      adminApi.updateAdminUser(id, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
  const columns = useMemo<GridColDef<AdminUser>[]>(
    () => [
      { field: "email", headerName: "Email", flex: 1, minWidth: 220 },
      {
        field: "role",
        headerName: "Role",
        width: 150,
        renderCell: ({ value }) => <StatusChip value={value} />,
      },
      {
        field: "school_ids",
        headerName: "School IDs",
        flex: 1,
        minWidth: 240,
        renderCell: ({ row }) => row.school_ids.join(", "),
      },
      {
        field: "active",
        headerName: "Active",
        width: 120,
        renderCell: ({ value }) => <StatusChip value={value ? "active" : "inactive"} />,
      },
      {
        field: "actions",
        headerName: "",
        width: 130,
        sortable: false,
        renderCell: ({ row }) => (
          <Button
            size="small"
            disabled={updateUser.isPending}
            onClick={() => updateUser.mutate({ id: row.id, body: { active: !row.active } })}
          >
            {row.active ? "Disable" : "Enable"}
          </Button>
        ),
      },
    ],
    [updateUser],
  );

  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState error={query.error} />;

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Admin Users"
        subtitle="Create and manage backend admin accounts and school scopes."
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="contained" onClick={() => setCreateOpen(true)}>
              Create admin
            </Button>
            <RefreshButton onClick={() => void query.refetch()} />
          </Stack>
        }
      />
      {createUser.error ? <Alert severity="error">{createUser.error.message}</Alert> : null}
      {updateUser.error ? <Alert severity="error">{updateUser.error.message}</Alert> : null}
      <DataGrid
        rows={query.data?.items ?? []}
        columns={columns}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[25, 50, 100]}
        initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        sx={{ bgcolor: "#fff", borderColor: "#e2e8f0" }}
      />
      <AdminUserCreateDialog
        open={createOpen}
        loading={createUser.isPending}
        error={createUser.error}
        onClose={() => setCreateOpen(false)}
        onSubmit={(body) => createUser.mutate(body)}
      />
    </Stack>
  );
}

function AdminUserCreateDialog({
  open,
  loading,
  error,
  onClose,
  onSubmit,
}: {
  open: boolean;
  loading: boolean;
  error: Error | null;
  onClose: () => void;
  onSubmit: (body: {
    email: string;
    password: string;
    role: string;
    school_ids: string[];
    region_ids: string[];
    active: boolean;
  }) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("school_admin");
  const [schoolIds, setSchoolIds] = useState("");
  const [regionIds, setRegionIds] = useState("");

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Admin User</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error ? <Alert severity="error">{error.message}</Alert> : null}
          <TextField label="Email / username" value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <TextField select label="Role" value={role} onChange={(e) => setRole(e.target.value)}>
            {["school_admin", "reviewer", "operator", "viewer", "super_admin"].map((value) => (
              <MenuItem key={value} value={value}>
                {value}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="School IDs"
            value={schoolIds}
            onChange={(e) => setSchoolIds(e.target.value)}
            multiline
            minRows={2}
          />
          <TextField
            label="Region IDs"
            value={regionIds}
            onChange={(e) => setRegionIds(e.target.value)}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          disabled={loading || !email || !password}
          onClick={() =>
            onSubmit({
              email,
              password,
              role,
              school_ids: splitIds(schoolIds),
              region_ids: splitIds(regionIds),
              active: true,
            })
          }
        >
          {loading ? "Creating..." : "Create admin"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function splitIds(value: string) {
  return value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}
