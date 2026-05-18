
"use client";

import { motion } from "framer-motion";

const NEWS_ITEMS = [
  "BREAKING: VerifyAI Phase 3 Live — New Keynote Experience Unleashed",
  "RUMOR: Global Markets Await Verification Verdict",
  "TECH: RoBERTa-base classifier achieves 98.2% accuracy in latest benchmarks",
  "ALERT: Fact-Check API integration expanded to 15+ trusted sources",
  "EXPLAIN: SHAP attributions now providing sub-millisecond visualisations",
];

export function NewsTicker() {
  return (
    <div className="w-full bg-[#fbfbfd] border-b border-[#d2d2d7]/30 py-2.5 overflow-hidden">
      <div className="flex whitespace-nowrap">
        <motion.div
          animate={{ x: [0, -1000] }}
          transition={{
            x: {
              repeat: Infinity,
              repeatType: "loop",
              duration: 40,
              ease: "linear",
            },
          }}
          className="flex items-center gap-16 px-4"
        >
          {[...NEWS_ITEMS, ...NEWS_ITEMS].map((item, index) => (
            <div key={index} className="flex items-center gap-4">
              <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
              <span className="text-[11px] font-medium tracking-tight text-[#1d1d1f] uppercase">
                {item}
              </span>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
