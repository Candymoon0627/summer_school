import {
  AppBar,
  Box,
  Button,
  Container,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import ArticleIcon from "@mui/icons-material/Article";
import DashboardIcon from "@mui/icons-material/Dashboard";
import HistoryIcon from "@mui/icons-material/History";
import LibraryBooksIcon from "@mui/icons-material/LibraryBooks";
import LogoutIcon from "@mui/icons-material/Logout";
import SchoolIcon from "@mui/icons-material/School";
import SettingsIcon from "@mui/icons-material/Settings";
import TaskAltIcon from "@mui/icons-material/TaskAlt";
import PeopleIcon from "@mui/icons-material/People";
import type { ReactNode } from "react";

import { clearCredentials } from "./api";
import { useMe } from "./hooks";

const drawerWidth = 260;

const navItems = [
  { label: "Overview", path: "/", icon: <DashboardIcon /> },
  { label: "Submissions", path: "/submissions", icon: <TaskAltIcon /> },
  { label: "Lessons", path: "/lessons", icon: <ArticleIcon /> },
  { label: "Knowledge", path: "/knowledge", icon: <LibraryBooksIcon /> },
  { label: "Schools", path: "/schools", icon: <SchoolIcon /> },
  { label: "Operations", path: "/operations", icon: <SettingsIcon /> },
  { label: "Admin Users", path: "/admin-users", icon: <PeopleIcon /> },
  { label: "Audit Logs", path: "/audit-logs", icon: <HistoryIcon /> },
];

export function AppLayout({
  children,
  currentPath,
  navigate,
}: {
  children: ReactNode;
  currentPath: string;
  navigate: (path: string) => void;
}) {
  const me = useMe();
  const visibleNavItems = navItems.filter((item) => {
    if (item.path === "/operations") {
      return !me.data?.is_scoped;
    }
    if (item.path === "/admin-users") {
      return me.data?.role === "super_admin";
    }
    return true;
  });
  const logout = () => {
    clearCredentials();
    navigate("/login");
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "#f8fafc" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          borderBottom: "1px solid #e2e8f0",
          bgcolor: "#ffffff",
          color: "#0f172a",
        }}
      >
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 800 }}>
            Edu AI Admin
          </Typography>
          <Button startIcon={<LogoutIcon />} onClick={logout} color="inherit">
            Logout
          </Button>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: drawerWidth,
            boxSizing: "border-box",
            borderRight: "1px solid #e2e8f0",
            bgcolor: "#ffffff",
          },
        }}
      >
        <Toolbar />
        <Stack sx={{ p: 2 }} spacing={2}>
          <Typography variant="caption" color="text.secondary" sx={{ px: 1 }}>
            Operations
          </Typography>
          <List disablePadding>
            {visibleNavItems.map((item) => (
              <ListItemButton
                key={item.path}
                selected={currentPath === item.path}
                onClick={() => navigate(item.path)}
                sx={{ borderRadius: 2, mb: 0.5 }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>
        </Stack>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, minWidth: 0 }}>
        <Toolbar />
        <Container maxWidth="xl" sx={{ py: 4 }}>
          {children}
        </Container>
      </Box>
    </Box>
  );
}
