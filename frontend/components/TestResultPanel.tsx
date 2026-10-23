"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  FlaskConical,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  ShieldAlert,
  Percent,
} from "lucide-react";
import { TestResultData } from "../stores/sessionStore";

interface TestResultPanelProps {
  testResults: TestResultData | null;
  isRunning?: boolean;
}

export function TestResultPanel({ testResults, isRunning }: TestResultPanelProps) {
  const [filter, setFilter] = useState<"ALL" | "FAILED" | "PASSED">("ALL");
  const [expandedTest, setExpandedTest] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!testResults) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-[#101018] rounded-xl border border-gray-800/80">
        <FlaskConical className="w-12 h-12 text-amber-500/50 mb-3 animate-pulse" />
        <h3 className="text-sm font-semibold text-gray-200 mb-1">
          {isRunning ? "Running Automated Test Suite..." : "No Test Results Available"}
        </h3>
        <p className="text-xs text-gray-500 max-w-md">
          {isRunning
            ? "The Tester agent is actively writing and executing unit & integration tests against the codebase."
            : "Test results and coverage metrics will appear here once the Tester agent executes test suites."}
        </p>
      </div>
    );
  }

  const { passed, failed, coverage, details = [] } = testResults;
  const total = passed + failed;
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;

  const filteredDetails = details.filter((item) => {
    if (filter === "FAILED") return item.status === "failed";
    if (filter === "PASSED") return item.status === "passed";
    return true;
  });

  const handleCopy = (id: string, text?: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-[#101018] rounded-xl border border-gray-800/80 overflow-hidden">
      {/* Top Metrics Cards */}
      <div className="p-4 bg-[#13131e] border-b border-gray-800/80">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Passed Card */}
          <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
                Tests Passed
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold font-mono text-emerald-300">
                  {passed}
                </span>
                <span className="text-xs text-emerald-500/80">
                  ({passRate}% of {total})
                </span>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>

          {/* Failed Card */}
          <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/30 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">
                Tests Failed
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold font-mono text-rose-300">
                  {failed}
                </span>
                <span className="text-xs text-rose-500/80">
                  {failed === 0 ? "All passing" : "Needs fix"}
                </span>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <XCircle className="w-5 h-5" />
            </div>
          </div>

          {/* Code Coverage Card */}
          <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/30 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">
                Code Coverage
              </span>
              <Percent className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="mt-1">
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-2xl font-bold font-mono text-indigo-300">
                  {coverage}%
                </span>
                <span className="text-[11px] text-gray-400">
                  {coverage >= 80 ? "Target met (≥80%)" : "Target: 80%+"}
                </span>
              </div>
              <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    coverage >= 80
                      ? "bg-emerald-500"
                      : coverage >= 60
                      ? "bg-amber-500"
                      : "bg-rose-500"
                  }`}
                  style={{ width: `${Math.min(coverage, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="px-4 py-2 bg-[#151522] border-b border-gray-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-medium">Filter cases:</span>
          <div className="flex items-center gap-1 bg-black/40 p-0.5 rounded-lg border border-gray-800">
            {(["ALL", "FAILED", "PASSED"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setFilter(tab)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  filter === tab
                    ? "bg-brand-600 text-white"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
        <span className="text-xs text-gray-500 font-mono">
          Showing {filteredDetails.length} items
        </span>
      </div>

      {/* Test List Accordion */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filteredDetails.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-500">
            {filter === "FAILED" && failed === 0 ? (
              <div className="flex flex-col items-center">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
                <span className="text-sm font-semibold text-emerald-300">
                  Zero test failures!
                </span>
                <span className="text-gray-400 mt-1">
                  All automated test suites executed cleanly.
                </span>
              </div>
            ) : (
              "No test items to show for this filter."
            )}
          </div>
        ) : (
          filteredDetails.map((test, idx) => {
            const isFailed = test.status === "failed";
            const testKey = `${test.name}-${idx}`;
            const isExpanded = expandedTest === testKey || (isFailed && expandedTest === null && idx === 0);

            return (
              <div
                key={testKey}
                className={`rounded-lg border transition-all ${
                  isFailed
                    ? "bg-rose-950/15 border-rose-500/30"
                    : "bg-[#141420] border-gray-800/80 hover:border-gray-700"
                }`}
              >
                <div
                  className="flex items-center justify-between p-3 cursor-pointer select-none"
                  onClick={() =>
                    setExpandedTest(isExpanded ? "" : testKey)
                  }
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {isFailed ? (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    )}
                    <span
                      className={`text-xs font-mono truncate font-medium ${
                        isFailed ? "text-rose-200" : "text-gray-200"
                      }`}
                    >
                      {test.name}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {test.durationMs !== undefined && (
                      <span className="text-[11px] font-mono text-gray-500">
                        {test.durationMs}ms
                      </span>
                    )}
                    {test.error && (
                      <span className="text-gray-400">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </span>
                    )}
                  </div>
                </div>

                {/* Expanded Error Details */}
                {isExpanded && test.error && (
                  <div className="p-3 border-t border-rose-500/20 bg-black/40 text-xs">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] uppercase tracking-wider font-semibold text-rose-400 flex items-center gap-1">
                        <ShieldAlert className="w-3.5 h-3.5" /> Stack Trace / Error
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopy(testKey, test.error)}
                        className="text-[11px] text-gray-400 hover:text-white flex items-center gap-1 bg-gray-800 px-2 py-0.5 rounded"
                      >
                        {copiedId === testKey ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-400" /> Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" /> Copy Trace
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="p-2.5 rounded bg-gray-950 font-mono text-[11px] text-rose-300 whitespace-pre-wrap overflow-x-auto border border-rose-900/30">
                      {test.error}
                    </pre>
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
