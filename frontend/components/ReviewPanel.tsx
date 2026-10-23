"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertOctagon,
  AlertTriangle,
  Info,
  BookOpen,
  CheckCircle2,
  FileCode,
  Sparkles,
} from "lucide-react";
import { ReviewIssueItem } from "../stores/sessionStore";

interface ReviewPanelProps {
  issues: ReviewIssueItem[];
  score: number | null;
  onNavigateToFile?: (file: string, line?: number) => void;
}

export function ReviewPanel({ issues, score, onNavigateToFile }: ReviewPanelProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");

  const effectiveScore = score !== null ? score : issues.length === 0 ? 100 : Math.max(30, 100 - issues.length * 12);
  const isApproved = effectiveScore >= 80 && !issues.some((i) => i.severity === "HIGH");

  const highCount = issues.filter((i) => i.severity === "HIGH").length;
  const medCount = issues.filter((i) => i.severity === "MEDIUM").length;
  const lowCount = issues.filter((i) => i.severity === "LOW").length;

  const filteredIssues = issues.filter((i) => {
    if (selectedSeverity === "ALL") return true;
    return i.severity === selectedSeverity;
  });

  // Calculate SVG circular gauge
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    circumference - (effectiveScore / 100) * circumference;

  return (
    <div className="flex flex-col h-full bg-[#101018] rounded-xl border border-gray-800/80 overflow-hidden">
      {/* Top Header Card */}
      <div className="p-4 bg-[#141420] border-b border-gray-800/80">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Left: Quality Score Gauge */}
          <div className="flex items-center gap-4">
            <div className="relative w-24 h-24 flex items-center justify-center">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle
                  cx="48"
                  cy="48"
                  r={radius}
                  stroke="#1f1f2e"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="48"
                  cy="48"
                  r={radius}
                  stroke={
                    effectiveScore >= 80
                      ? "#10b981"
                      : effectiveScore >= 60
                      ? "#f59e0b"
                      : "#ef4444"
                  }
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-xl font-bold font-mono text-gray-100">
                  {effectiveScore}
                </span>
                <span className="text-[10px] text-gray-400 font-sans uppercase">
                  Score
                </span>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-bold text-gray-100">
                  Code & Architecture Audit
                </h3>
                {isApproved ? (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approved
                  </span>
                ) : (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                    <AlertOctagon className="w-3.5 h-3.5" /> Changes Required
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400 max-w-sm">
                Evaluated against enterprise security baselines, architectural clean code standards, and RAG-verified best practices.
              </p>
            </div>
          </div>

          {/* Right: Severity Counter Chips */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSelectedSeverity("HIGH")}
              className={`px-3 py-2 rounded-lg border text-left transition-all ${
                selectedSeverity === "HIGH"
                  ? "bg-rose-950/40 border-rose-500"
                  : "bg-rose-950/10 border-rose-500/20 hover:border-rose-500/40"
              }`}
            >
              <span className="text-[10px] uppercase font-bold text-rose-400 block">
                High Severity
              </span>
              <span className="text-lg font-bold font-mono text-rose-300">
                {highCount}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedSeverity("MEDIUM")}
              className={`px-3 py-2 rounded-lg border text-left transition-all ${
                selectedSeverity === "MEDIUM"
                  ? "bg-amber-950/40 border-amber-500"
                  : "bg-amber-950/10 border-amber-500/20 hover:border-amber-500/40"
              }`}
            >
              <span className="text-[10px] uppercase font-bold text-amber-400 block">
                Medium
              </span>
              <span className="text-lg font-bold font-mono text-amber-300">
                {medCount}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedSeverity("LOW")}
              className={`px-3 py-2 rounded-lg border text-left transition-all ${
                selectedSeverity === "LOW"
                  ? "bg-blue-950/40 border-blue-500"
                  : "bg-blue-950/10 border-blue-500/20 hover:border-blue-500/40"
              }`}
            >
              <span className="text-[10px] uppercase font-bold text-blue-400 block">
                Low
              </span>
              <span className="text-lg font-bold font-mono text-blue-300">
                {lowCount}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Filter bar */}
      <div className="px-4 py-2 bg-[#12121c] border-b border-gray-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-medium">Filter:</span>
          {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setSelectedSeverity(sev)}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                selectedSeverity === sev
                  ? "bg-brand-600 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-500 font-mono">
          {filteredIssues.length} issues listed
        </span>
      </div>

      {/* Issues List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredIssues.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center text-gray-500">
            <ShieldCheck className="w-12 h-12 text-emerald-400 mb-2 opacity-80" />
            <h4 className="text-sm font-semibold text-gray-200">
              Clean Audit Report
            </h4>
            <p className="text-xs text-gray-400 max-w-sm mt-1">
              No code review or vulnerability issues detected for this filter.
            </p>
          </div>
        ) : (
          filteredIssues.map((issue, idx) => {
            const isHigh = issue.severity === "HIGH";
            const isMed = issue.severity === "MEDIUM";

            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border transition-all ${
                  isHigh
                    ? "bg-rose-950/15 border-rose-500/30"
                    : isMed
                    ? "bg-amber-950/15 border-amber-500/30"
                    : "bg-[#141420] border-gray-800"
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        isHigh
                          ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                          : isMed
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                          : "bg-blue-500/20 text-blue-300 border-blue-500/40"
                      }`}
                    >
                      {issue.severity}
                    </span>

                    {/* File Path Button */}
                    <button
                      type="button"
                      onClick={() => onNavigateToFile?.(issue.file, issue.line)}
                      className="text-xs font-mono text-gray-300 hover:text-brand-300 flex items-center gap-1 transition-colors underline decoration-dotted"
                    >
                      <FileCode className="w-3.5 h-3.5 text-gray-500" />
                      {issue.file}
                      {issue.line ? `:${issue.line}` : ""}
                    </button>
                  </div>

                  {/* RAG Source Tag */}
                  {issue.source && (
                    <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700 shrink-0">
                      <BookOpen className="w-3 h-3 text-brand-400" />
                      {issue.source}
                    </span>
                  )}
                </div>

                <p className="text-xs text-gray-200 leading-relaxed font-medium mb-2">
                  {issue.issue}
                </p>

                {issue.suggestion && (
                  <div className="p-2.5 rounded-lg bg-black/40 border border-gray-800 text-xs">
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-emerald-400 flex items-center gap-1 mb-1">
                      <Sparkles className="w-3 h-3" /> Recommended Remediation
                    </span>
                    <p className="font-mono text-[11px] text-gray-300 whitespace-pre-wrap">
                      {issue.suggestion}
                    </p>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
