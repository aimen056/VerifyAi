
"use client";

import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
} from "lucide-react";
import type { Verdict } from "@/lib/api";

const verdictConfig: Record<
  Verdict,
  { label: string; className: string; icon: React.ReactNode }
> = {
  TRUE: {
    label: "Verified True",
    className:
      "bg-emerald-50 text-emerald-700 border-emerald-100 hover:bg-emerald-100",
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
  },
  FALSE: {
    label: "Verified False",
    className:
      "bg-red-50 text-red-700 border-red-100 hover:bg-red-100",
    icon: <XCircle className="h-3.5 w-3.5" />,
  },
  MISLEADING: {
    label: "Misleading",
    className:
      "bg-amber-50 text-amber-700 border-amber-100 hover:bg-amber-100",
    icon: <AlertTriangle className="h-3.5 w-3.5" />,
  },
  UNVERIFIED: {
    label: "Unverified",
    className:
      "bg-zinc-50 text-zinc-700 border-zinc-100 hover:bg-zinc-100",
    icon: <HelpCircle className="h-3.5 w-3.5" />,
  },
};

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const config = verdictConfig[verdict] || verdictConfig.UNVERIFIED;
  return (
    <Badge
      variant="outline"
      className={`gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider transition-colors ${config.className}`}
    >
      {config.icon}
      {config.label}
    </Badge>
  );
}
