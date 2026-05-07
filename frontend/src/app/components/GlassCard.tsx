import type { CSSProperties, ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  style?: CSSProperties;
  className?: string;
  /** Stronger top-edge reflection for hero/featured cards */
  bright?: boolean;
  onClick?: () => void;
}

/**
 * Reusable glass card with built-in:
 *   • bright top-edge specular highlight
 *   • diagonal light-streak reflection overlay
 *   • proper backdrop-blur + low-opacity base for see-through glass feel
 */
export function GlassCard({ children, style, className, bright, onClick }: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={className}
      style={{
        position: "relative",
        overflow: "hidden",
        background: "rgba(20, 20, 30, 0.25)",
        backdropFilter: "blur(12px) saturate(120%)",
        WebkitBackdropFilter: "blur(12px) saturate(120%)",
        borderRadius: 6,
        border: "1px solid rgba(255,255,255,0.08)",
        /* bright top & left edges */
        borderTop: `1px solid rgba(255,255,255,${bright ? "0.15" : "0.1"})`,
        borderLeft: "1px solid rgba(255,255,255,0.08)",
        boxShadow: `
          0 4px 12px rgba(0,0,0,0.3),
          0 1px 0 rgba(255,255,255,0.08) inset
        `,
        ...style,
      }}
    >
      {/* ── Strong diagonal light-streak reflection ── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "inherit",
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 40%)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* ── Bright top-edge specular highlight ── */}
      <div
        style={{
          position: "absolute",
          top: 0, left: 0, right: 0,
          height: 1,
          background:
            "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.5) 50%, transparent 100%)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* ── Top-face ambient reflection ── */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "55%",
          borderRadius: "6px 6px 0 0",
          background:
            "linear-gradient(to bottom, rgba(255,255,255,0.09) 0%, rgba(255,255,255,0.02) 50%, transparent 100%)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* ── Content sits above overlays ── */}
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
}

/** Smaller inner glass panel (for nested cards) */
export function GlassInner({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        background: "rgba(15, 15, 25, 0.3)",
        backdropFilter: "blur(8px) saturate(100%)",
        WebkitBackdropFilter: "blur(8px) saturate(100%)",
        borderRadius: 6,
        border: "1px solid rgba(255,255,255,0.08)",
        borderTop: "1px solid rgba(255,255,255,0.12)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "inherit",
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 40%)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
}

/**
 * Full-page background: dark base + lit grid + floor glow lights
 * Wrap your page with this.
 */
export function PageBackground({ children }: { children: ReactNode }) {
  return (
    <div style={{ position: "relative", background: "#080c10", minHeight: "100vh" }}>
      {/* ── Grid overlay (subtle) ── */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          zIndex: 0,
          backgroundImage:
            "linear-gradient(rgba(100,185,230,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(100,185,230,0.03) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          maskImage:
            "linear-gradient(to top, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0) 100%)",
          WebkitMaskImage:
            "linear-gradient(to top, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0) 100%)",
        }}
      />

      {/* ── Floor lighting system ── */}
      <div className="fixed inset-x-0 bottom-0 pointer-events-none" style={{ zIndex: 0 }}>
        {/* Central blue floor glow */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: "50%",
            transform: "translateX(-50%)",
            width: "130%",
            height: "50vh",
            background:
              "radial-gradient(ellipse 100% 50% at 50% 100%, rgba(59, 130, 246, 0.15) 0%, rgba(30, 90, 200, 0.08) 40%, transparent 70%)",
          }}
        />
      </div>

      {/* ── Subtle top-center glow ── */}
      <div
        className="fixed pointer-events-none"
        style={{
          top: -100,
          left: "50%",
          transform: "translateX(-50%)",
          width: 600,
          height: 300,
          background:
            "radial-gradient(ellipse at 50% 0%, rgba(59, 130, 246, 0.05) 0%, transparent 70%)",
          zIndex: 0,
        }}
      />

      {/* Page content */}
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
}
