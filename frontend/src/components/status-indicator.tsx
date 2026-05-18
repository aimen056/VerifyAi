"use client";

import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";
import type { HealthResponse } from "@/lib/api";

export function StatusIndicator() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;

    const check = async () => {
      try {
        const res = await checkHealth();
        if (isMounted) {
          setHealth(res);
          setConnected(true);
        }
      } catch {
        if (isMounted) {
          setHealth(null);
          setConnected(false);
        }
      }
    };

    check();
    const interval = setInterval(check, 15_000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex items-center gap-2 text-xs">
      {/* Pulsing dot */}
      <span className="relative flex h-2.5 w-2.5">
        {connected && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
        )}
        <span
          className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
            connected === null
              ? "bg-[#86868b]"
              : connected
                ? "bg-[#00cc44]"
                : "bg-[#ff3b30]"
          }`}
        />
      </span>

      {/* Label */}
      <span className="text-[#86868b] font-medium tracking-tight">
        {connected === null
          ? "Checking..."
          : connected
            ? `API v${health?.version}`
            : "Offline"}
      </span>
    </div>
  );
}
