import { createBrowserRouter, Navigate } from "react-router";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { ChatPage } from "./pages/ChatPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { AdminPage } from "./pages/AdminPage";

export const router = createBrowserRouter([
  // Landing page is the entry point
  { path: "/", Component: LandingPage },
  // Login page
  { path: "/login", Component: LoginPage },
  // Chat interface to input query
  { path: "/chat", Component: ChatPage },
  // Processing animation
  { path: "/processing", Component: ProcessingPage },
  // Final intelligent dashboard
  { path: "/dashboard", Component: DashboardPage },
  // Admin Dashboard
  { path: "/admin", Component: AdminPage },
  // Catch-all
  { path: "*", element: <Navigate to="/" replace /> },
]);
