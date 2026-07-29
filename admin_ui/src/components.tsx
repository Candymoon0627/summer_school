import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      justifyContent="space-between"
      alignItems={{ xs: "flex-start", sm: "center" }}
      spacing={2}
      sx={{ mb: 3 }}
    >
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: 0 }}>
          {title}
        </Typography>
        {subtitle ? (
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        ) : null}
      </Box>
      {actions}
    </Stack>
  );
}

export function MetricCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string | number;
  helper?: string;
}) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h4" sx={{ mt: 1, fontWeight: 800, letterSpacing: 0 }}>
          {value}
        </Typography>
        {helper ? (
          <Typography variant="caption" color="text.secondary">
            {helper}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function StatusChip({ value }: { value?: string | null }) {
  const normalized = value ?? "unknown";
  const color =
    normalized.includes("approved") || normalized === "completed" || normalized === "embedded"
      ? "success"
      : normalized.includes("failed") || normalized === "rejected"
        ? "error"
        : normalized.includes("pending") || normalized.includes("review")
          ? "warning"
          : "default";
  return <Chip size="small" label={normalized} color={color} variant="outlined" />;
}

export function LoadingState() {
  return (
    <Stack alignItems="center" justifyContent="center" sx={{ minHeight: 260 }}>
      <CircularProgress />
    </Stack>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  return (
    <Alert severity="error">
      {error instanceof Error ? error.message : "Something went wrong."}
    </Alert>
  );
}

export function EmptyState({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2} alignItems="flex-start">
          <Typography color="text.secondary">{title}</Typography>
          {action}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function KeyValue({
  label,
  value,
}: {
  label: string;
  value?: ReactNode;
}) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography sx={{ wordBreak: "break-word" }}>{value || "-"}</Typography>
    </Box>
  );
}

export function SectionCard({
  title,
  children,
  actions,
}: {
  title: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {title}
            </Typography>
            {actions}
          </Stack>
          <Divider />
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function RefreshButton({ onClick }: { onClick: () => void }) {
  return (
    <Button variant="outlined" onClick={onClick}>
      Refresh
    </Button>
  );
}
