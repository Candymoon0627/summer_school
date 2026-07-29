import { Refine } from "@refinedev/core";
import { RefineThemes } from "@refinedev/mui";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const theme = createTheme({
  ...RefineThemes.Blue,
  shape: { borderRadius: 8 },
  typography: {
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  palette: {
    ...RefineThemes.Blue.palette,
    background: {
      default: "#f8fafc",
      paper: "#ffffff",
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderColor: "#e2e8f0",
          boxShadow: "none",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 700,
        },
      },
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Refine
          resources={[
            { name: "overview", list: "/" },
            { name: "submissions", list: "/submissions", show: "/submissions/:id" },
            { name: "lessons", list: "/lessons" },
            { name: "knowledge", list: "/knowledge" },
            { name: "schools", list: "/schools" },
            { name: "operations", list: "/operations" },
            { name: "admin-users", list: "/admin-users" },
            { name: "audit-logs", list: "/audit-logs" },
          ]}
          options={{
            syncWithLocation: false,
            warnWhenUnsavedChanges: false,
          }}
        >
          <App />
        </Refine>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
