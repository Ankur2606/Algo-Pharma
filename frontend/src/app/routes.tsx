import { createBrowserRouter, Navigate } from "react-router";
import { LandingPage } from "./pages/LandingPage";
import { AuthPage } from "./pages/AuthPage";
import { ChatPage } from "./pages/ChatPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ValidationPage } from "./pages/ValidationPage";
import { DashboardLayout } from "./components/layout/DashboardLayout";

export const router = createBrowserRouter([
  // Landing page is the entry point — no connections to internal pages
  { path: "/", Component: LandingPage },
  // App entry (login) lives at /login
  { path: "/login", Component: AuthPage },
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
