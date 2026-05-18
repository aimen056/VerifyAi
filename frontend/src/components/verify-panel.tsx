
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Image as ImageIcon,
  Link2,
  Loader2,
  Zap,
  BarChart3,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  AlertTriangle,
  Brain,
  Clock,
} from "lucide-react";
import { verifyText, verifyUrl, verifyImage } from "@/lib/api";
import type { VerifyResponse } from "@/lib/api";
import { VerdictBadge } from "@/components/verdict-badge";

type TabType = "text" | "image" | "url";

export function VerifyPanel() {
  const [activeTab, setActiveTab] = useState<TabType>("text");
  const [textInput, setTextInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async (type: TabType) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      let res: VerifyResponse;
      if (type === "text") {
        if (!textInput.trim() || textInput.trim().length < 10) throw new Error("Please enter at least 10 characters.");
        res = await verifyText(textInput);
      } else if (type === "url") {
        if (!urlInput.trim()) throw new Error("Please enter a valid URL.");
        res = await verifyUrl(urlInput);
      } else {
        if (!imageFile) throw new Error("Please select an image file.");
        res = await verifyImage(imageFile);
      }
      setResult(res);
    } catch (e: any) {
      setError(e.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-8">
      {/* ── Tabs ───────────────────────────────────────────── */}
      <div className="apple-card p-2 bg-[#f5f5f7]/50 border-none">
        <div className="flex gap-1">
          {(["text", "image", "url"] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-[18px] text-sm font-medium transition-all ${
                activeTab === tab
                  ? "bg-white text-[#1d1d1f] shadow-[0_2px_12px_rgba(0,0,0,0.08)]"
                  : "text-[#86868b] hover:text-[#1d1d1f]"
              }`}
            >
              {tab === "text" && <FileText className="h-4 w-4" />}
              {tab === "image" && <ImageIcon className="h-4 w-4" />}
              {tab === "url" && <Link2 className="h-4 w-4" />}
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="p-4 pt-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === "text" && (
                <textarea
                  placeholder="Enter content to verify..."
                  className="w-full min-h-[160px] p-4 bg-transparent text-[#1d1d1f] placeholder-[#86868b] text-lg font-medium resize-none focus:outline-none"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                />
              )}
              {activeTab === "url" && (
                <input
                  type="url"
                  placeholder="https://news-source.com/article"
                  className="w-full p-4 bg-transparent text-[#1d1d1f] placeholder-[#86868b] text-lg font-medium focus:outline-none"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                />
              )}
              {activeTab === "image" && (
                <div 
                  className="w-full h-[160px] flex flex-col items-center justify-center border-2 border-dashed border-[#d2d2d7] rounded-2xl cursor-pointer hover:border-[#0066cc]/50 transition-colors"
                  onClick={() => document.getElementById("file-upload")?.click()}
                >
                  <input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    onChange={(e) => setImageFile(e.target.files?.[0] || null)}
                  />
                  <ImageIcon className="h-10 w-10 text-[#d2d2d7] mb-2" />
                  <p className="text-[#86868b] text-sm">
                    {imageFile ? imageFile.name : "Upload news screenshot"}
                  </p>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          <div className="mt-6 flex justify-end">
            <button
              onClick={() => handleVerify(activeTab)}
              disabled={loading}
              className="apple-button h-12 px-10 flex items-center gap-2 disabled:opacity-50 disabled:active:scale-100"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Zap className="h-5 w-5 fill-current" />
              )}
              {loading ? "Analyzing..." : "Verify Content"}
            </button>
          </div>
        </div>
      </div>

      {/* ── Results Container ───────────────────────────────── */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="p-4 bg-red-50 border border-red-100 rounded-2xl flex items-center gap-3 text-red-600 text-sm font-medium"
          >
            <ShieldAlert className="h-5 w-5" />
            {error}
          </motion.div>
        )}

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", damping: 20, stiffness: 100 }}
            className="apple-card p-0"
          >
            {/* Header section with big verdict */}
            <div className={`px-8 py-10 flex items-center justify-between ${
              result.verdict === "TRUE" ? "bg-emerald-50/50" : 
              result.verdict === "FALSE" ? "bg-red-50/50" : "bg-amber-50/50"
            }`}>
              <div className="flex items-center gap-6">
                <div className={`p-4 rounded-2xl ${
                  result.verdict === "TRUE" ? "bg-emerald-100 text-emerald-600" : 
                  result.verdict === "FALSE" ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-600"
                }`}>
                  {result.verdict === "TRUE" && <ShieldCheck className="h-8 w-8" />}
                  {result.verdict === "FALSE" && <ShieldAlert className="h-8 w-8" />}
                  {(result.verdict === "MISLEADING" || result.verdict === "UNVERIFIED") && <AlertTriangle className="h-8 w-8" />}
                </div>
                <div>
                  <h3 className="text-3xl font-bold tracking-tight text-[#1d1d1f]">
                    {result.verdict}
                  </h3>
                  <p className="text-[#86868b] font-medium">
                    Verified with {(result.confidence * 100).toFixed(1)}% AI confidence
                  </p>
                </div>
              </div>
              <div className="text-right">
                <VerdictBadge verdict={result.verdict} />
              </div>
            </div>

            <div className="p-8 space-y-10">
              {/* Summary */}
              <div className="space-y-3">
                <p className="text-[11px] font-bold uppercase tracking-widest text-[#86868b]">Analysis Summary</p>
                <p className="text-xl font-medium text-[#1d1d1f] leading-relaxed">
                  {result.summary}
                </p>
              </div>

              {/* Explainability Section */}
              {result.explanation?.tokens && result.explanation.tokens.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-[#0066cc]" />
                    <p className="text-[11px] font-bold uppercase tracking-widest text-[#86868b]">AI Attribution (SHAP)</p>
                  </div>
                  
                  {result.explanation.summary && (
                    <p className="text-sm text-[#424245] leading-relaxed italic">
                      {result.explanation.summary}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-2">
                    {result.explanation.tokens.map((t, i) => (
                      <span 
                        key={i}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
                          t.attribution > 0 
                            ? "bg-emerald-50 text-emerald-700 border-emerald-100" 
                            : "bg-red-50 text-red-700 border-red-100"
                        }`}
                      >
                        {t.token}
                        <span className="ml-1.5 opacity-50 font-mono">
                          {t.attribution > 0 ? "+" : ""}{t.attribution.toFixed(2)}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Technical Breakdown */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-8 border-t border-[#d2d2d7]/30">
                <div className="space-y-1">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-[#86868b]">Processing</p>
                  <div className="flex items-center gap-1.5 text-sm font-semibold text-[#1d1d1f]">
                    <Clock className="h-3.5 w-3.5" />
                    {result.processing_time_ms}ms
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-[#86868b]">Model</p>
                  <p className="text-sm font-semibold text-[#1d1d1f]">RoBERTa-base</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-[#86868b]">Method</p>
                  <p className="text-sm font-semibold text-[#1d1d1f]">NLP Inference</p>
                </div>
                <div className="space-y-1 text-right">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-[#86868b]">Report ID</p>
                  <p className="text-sm font-mono text-[#86868b]">{result.id.slice(0, 8)}</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
