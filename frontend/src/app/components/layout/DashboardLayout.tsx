import { Outlet } from "react-router";
import { Sidebar } from "./Sidebar";

export function DashboardLayout() {
  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ background: "#050508" }}
    >
      {/* ── Dark grid background ── */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)",
          backgroundSize: "52px 52px",
          zIndex: 0,
        }}
      />

      {/* ── Subtle radial glow top-center ── */}
      <div
        className="fixed pointer-events-none"
        style={{
          top: "-120px",
          left: "50%",
          transform: "translateX(-50%)",
          width: "700px",
          height: "400px",
          background: "radial-gradient(ellipse at center, rgba(99,102,241,0.07) 0%, transparent 70%)",
          zIndex: 0,
        }}
      />

      <Sidebar />

      <main
        className="flex-1 flex flex-col min-w-0 overflow-hidden"
        style={{ position: "relative", zIndex: 1 }}
      >
        <Outlet />
      </main>
    </div>
  );
}
