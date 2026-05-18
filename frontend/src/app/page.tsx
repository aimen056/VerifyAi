
"use client";

import { VerifyPanel } from "@/components/verify-panel";
import { StatusIndicator } from "@/components/status-indicator";
import { Shield, ExternalLink, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="relative min-h-screen bg-[#f5f5f7] selection:bg-[#0066cc]/10 selection:text-[#0066cc] overflow-hidden">
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-[#d2d2d7]/30 shadow-sm">
        <div className="mx-auto max-w-[1200px] flex items-center justify-between px-8 py-4">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-[7px] bg-[#0066cc] shadow-md">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <h1 className="text-lg font-semibold tracking-tight text-[#1d1d1f]">
              VerifyAI
            </h1>
          </motion.div>

          <div className="flex items-center gap-8">
            <StatusIndicator />
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#86868b] hover:text-[#1d1d1f] transition-colors"
            >
              <ExternalLink className="h-5 w-5" />
            </a>
          </div>
        </div>
      </header>

      {/* ── Main Content ─────────────────────────────────────── */}
      <main className="relative z-10 mx-auto max-w-[980px] px-8 pt-24 pb-32">
        {/* Hero Section */}
        <div className="text-center mb-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <h2 className="text-6xl md:text-7xl font-bold tracking-tight text-[#1d1d1f] leading-[1.05] mb-8">
              Verify the news.<br />
              <span className="text-[#86868b]">Before you share it.</span>
            </h2>
            <p className="text-[#86868b] max-w-xl mx-auto text-xl font-medium leading-relaxed mb-12">
              Our advanced AI cross-references headlines, screenshots, and URLs with trusted global sources to keep you informed.
            </p>
            <div className="flex items-center justify-center gap-6">
              <button className="bg-[#0066cc] text-white font-semibold rounded-full px-8 py-3 hover:bg-[#005bb5] hover:scale-105 active:scale-95 transition-all shadow-md flex items-center gap-2">
                Verify Now <ArrowRight className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-2 text-sm font-medium text-[#0066cc] cursor-pointer hover:text-[#005bb5] transition-colors">
                See how it works
              </div>
            </div>
          </motion.div>
        </div>

        {/* Verification Hub */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="relative"
        >
          <div className="absolute -inset-4 bg-white rounded-[40px] shadow-lg -z-10" />
          <VerifyPanel />
        </motion.div>

        {/* Technical Specs / Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mt-40">
          {[
            {
              title: "DeBERTa Fact-Checker Engine",
              desc: "State-of-the-art NLI model specifically trained on the FEVER dataset to understand complex logical contradictions."
            },
            {
              title: "SHAP Explainability",
              desc: "Transparent attribution mapping showing exactly which words influenced the verdict."
            },
            {
              title: "Live Fact-Check",
              desc: "Real-time verification against the Google Fact Check API and global trusted databases."
            }
          ].map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="space-y-3"
            >
              <h3 className="text-lg font-semibold text-[#1d1d1f] drop-shadow-sm">{feature.title}</h3>
              <p className="text-[#86868b] text-sm leading-relaxed">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </main>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="border-t border-[#d2d2d7]/30 bg-white mt-32 relative z-10">
        <div className="mx-auto max-w-[980px] px-8 py-12 flex flex-col md:flex-row items-center justify-between gap-6 text-[12px] text-[#86868b] font-medium">
          <div className="flex items-center gap-8">
            <span>© 2026 VerifyAI Intelligence</span>
            <span className="hover:text-[#1d1d1f] cursor-pointer transition-colors">Privacy Policy</span>
            <span className="hover:text-[#1d1d1f] cursor-pointer transition-colors">Terms of Service</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="h-2 w-2 rounded-full bg-[#00cc44] shadow-sm animate-pulse" />
            <span className="text-[#86868b]">Systems Operational · v0.2.2</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
