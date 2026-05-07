import { createBrowserRouter, Navigate } from "react-router";
import { AuthPage } from "./pages/AuthPage";
import { ChatPage } from "./pages/ChatPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ValidationPage } from "./pages/ValidationPage";
import { DashboardLayout } from "./components/layout/DashboardLayout";

export const router = createBrowserRouter([
  { path: "/", Component: AuthPage },
  { path: "/chat", Component: ChatPage },
  { path: "/processing", Component: ProcessingPage },
  // Dashboard and sub-pages share the sidebar layout
  {
    Component: DashboardLayout,
    children: [
      { path: "/dashboard", Component: DashboardPage },
      { path: "/validation", Component: ValidationPage },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
