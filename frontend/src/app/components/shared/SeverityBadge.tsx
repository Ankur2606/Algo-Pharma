import type { Severity } from "../../data/mockData";

interface SeverityBadgeProps {
  severity: Severity;
  size?: "sm" | "md";
}

const config = {
  RED: {
    label: "RED",
    dot: "bg-red-500",
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/20",
  },
  AMBER: {
    label: "AMBER",
    dot: "bg-amber-400",
    bg: "bg-amber-400/10",
    text: "text-amber-400",
    border: "border-amber-400/20",
  },
  GREEN: {
    label: "GREEN",
    dot: "bg-green-500",
    bg: "bg-green-400/10",
    text: "text-green-400",
    border: "border-green-400/20",
  },
};

export function SeverityBadge({ severity, size = "md" }: SeverityBadgeProps) {
  const c = config[severity];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${c.bg} ${c.text} ${c.border} ${
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs"
      } font-medium`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
