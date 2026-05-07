import { Bell, Search, RefreshCw } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function Header({ title, subtitle, actions }: HeaderProps) {
  return (
    <header
      className="flex items-center justify-between px-6 shrink-0"
      style={{
        height: "56px",
        borderBottom: "1px solid rgba(255,255,255,0.055)",
        background: "#050508",
      }}
    >
      <div>
        <h1
          style={{
            fontSize: "15px",
            fontWeight: 600,
            color: "rgba(255,255,255,0.88)",
            lineHeight: 1.3,
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              fontSize: "11px",
              color: "rgba(255,255,255,0.32)",
              lineHeight: 1.3,
              marginTop: "1px",
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        {actions}

        <button
          className="flex items-center gap-1.5 rounded-md transition-colors hover:bg-white/[0.04]"
          style={{
            padding: "6px 10px",
            fontSize: "12px",
            color: "rgba(255,255,255,0.40)",
            fontWeight: 500,
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLElement).style.color =
              "rgba(255,255,255,0.7)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLElement).style.color =
              "rgba(255,255,255,0.40)")
          }
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Refresh</span>
        </button>

        <button
          className="relative flex items-center justify-center rounded-md transition-colors hover:bg-white/[0.04]"
          style={{
            width: "32px",
            height: "32px",
            color: "rgba(255,255,255,0.40)",
          }}
        >
          <Bell className="w-4 h-4" />
          <span
            className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full"
            style={{ background: "#f59e0b" }}
          />
        </button>

        <button
          className="flex items-center justify-center rounded-md transition-colors hover:bg-white/[0.04]"
          style={{
            width: "32px",
            height: "32px",
            color: "rgba(255,255,255,0.40)",
          }}
        >
          <Search className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
