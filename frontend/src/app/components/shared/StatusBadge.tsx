import type { SignalStatus } from "../../data/mockData";

interface StatusBadgeProps {
  status: SignalStatus;
}

const config: Record<SignalStatus, { label: string; bg: string; text: string; border: string }> = {
  NEW: {
    label: "New",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/20",
  },
  IN_REVIEW: {
    label: "In Review",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/20",
  },
  CONFIRMED: {
    label: "Confirmed",
    bg: "bg-green-500/10",
    text: "text-green-400",
    border: "border-green-500/20",
  },
  EXPORTED: {
    label: "Exported",
    bg: "bg-white/5",
    text: "text-white/50",
    border: "border-white/10",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const c = config[status];
  return (
    <span
      className={`inline-flex items-center rounded-full border ${c.bg} ${c.text} ${c.border} px-2.5 py-0.5 text-xs font-medium`}
    >
      {c.label}
    </span>
  );
}
