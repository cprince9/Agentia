"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ActivityItem } from "../stores/sessionStore";
import { AgentName } from "../lib/api";
import {
  Terminal,
  FileCode2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sparkles,
  ArrowDownCircle,
  PauseCircle,
  PlayCircle,
  Brain,
  MessageSquare,
  Flame,
} from "lucide-react";

interface ActivityFeedProps {
  items: ActivityItem[];
  className?: string;
  onFileClick?: (path: string) => void;
}

const AGENT_COLORS: Record<AgentName, { bg: string; text: string; dot: string }> = {
  planner: {
    bg: "bg-blue-500/10 text-blue-300 border-blue-500/20",
    text: "text-blue-400",
    dot: "bg-blue-400",
  },
  architect: {
    bg: "bg-purple-500/10 text-purple-300 border-purple-500/20",
    text: "text-purple-400",
    dot: "bg-purple-400",
  },
  coder: {
    bg: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
    text: "text-emerald-400",
    dot: "bg-emerald-400",
  },
  tester: {
    bg: "bg-amber-500/10 text-amber-300 border-amber-500/20",
    text: "text-amber-400",
    dot: "bg-amber-400",
  },
  reviewer: {
    bg: "bg-orange-500/10 text-orange-300 border-orange-500/20",
    text: "text-orange-400",
    dot: "bg-orange-400",
  },
  devops: {
    bg: "bg-rose-500/10 text-rose-300 border-rose-500/20",
    text: "text-rose-400",
    dot: "bg-rose-400",
  },
};

export function ActivityFeed({ items, className = "", onFileClick }: ActivityFeedProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [filter, setFilter] = useState<string>("ALL");

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [items, autoScroll]);

  const handleUserScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    if (autoScroll !== isAtBottom) {
      setAutoScroll(isAtBottom);
    }
  };

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
      setAutoScroll(true);
    }
  };

  const filteredItems = items.filter((item) => {
    if (filter === "ALL") return true;
    if (filter === "FILES") return item.type === "FILE_CREATED";
    if (filter === "TESTS") return item.type === "TEST_RESULT";
    if (filter === "REVIEW") return item.type === "REVIEW_ISSUE";
    if (filter === "AGENTS")
      return [
        "AGENT_STARTED",
        "AGENT_THINKING",
        "AGENT_COMPLETE",
        "AGENT_FAILED",
        "AGENT_MESSAGE",
      ].includes(item.type);
    return true;
  });

  const renderItemContent = (item: ActivityItem) => {
    const timeFormatted = item.timestamp
      ? new Date(item.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      : "--:--:--";

    const agentColor = item.agent && AGENT_COLORS[item.agent] ? AGENT_COLORS[item.agent] : null;

    switch (item.type) {
      case "FILE_CREATED": {
        const filePath = item.metadata?.path || item.message;
        return (
          <div className="flex items-start gap-3 p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20">
            <div className="w-7 h-7 rounded-md bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
              <FileCode2 className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-semibold text-emerald-300">File Generated</span>
                <span className="text-[11px] font-mono text-gray-500">{timeFormatted}</span>
              </div>
              <button
                type="button"
                onClick={() => onFileClick?.(filePath)}
                className="text-xs font-mono text-emerald-200 bg-emerald-900/40 hover:bg-emerald-800/40 px-2 py-1 rounded border border-emerald-500/30 transition-colors break-all text-left"
              >
                {filePath}
              </button>
            </div>
          </div>
        );
      }

      case "TEST_RESULT": {
        const passed = item.metadata?.passed ?? 0;
        const failed = item.metadata?.failed ?? 0;
        const isSuccess = failed === 0;

        return (
          <div
            className={`flex items-start gap-3 p-2.5 rounded-lg border ${
              isSuccess
                ? "bg-emerald-950/20 border-emerald-500/20"
                : "bg-rose-950/20 border-rose-500/25"
            }`}
          >
            <div
              className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 ${
                isSuccess
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "bg-rose-500/20 text-rose-400"
              }`}
            >
              {isSuccess ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between text-xs mb-1">
                <span
                  className={`font-semibold ${
                    isSuccess ? "text-emerald-300" : "text-rose-300"
                  }`}
                >
                  {isSuccess ? "Tests Passed" : "Tests Failed"}
                </span>
                <span className="text-[11px] font-mono text-gray-500">{timeFormatted}</span>
              </div>
              <p className="text-xs text-gray-300">{item.message}</p>
              <div className="flex items-center gap-3 mt-1.5 text-xs font-mono">
                <span className="text-emerald-400">✓ {passed} passed</span>
                {failed > 0 && <span className="text-rose-400">✗ {failed} failed</span>}
                {item.metadata?.coverage !== undefined && (
                  <span className="text-gray-400">Coverage: {item.metadata.coverage}%</span>
                )}
              </div>
            </div>
          </div>
        );
      }

      case "REVIEW_ISSUE": {
        const severity = item.metadata?.severity || "MEDIUM";
        const severityColor =
          severity === "HIGH"
            ? "text-rose-400 bg-rose-500/10 border-rose-500/30"
            : severity === "LOW"
            ? "text-blue-400 bg-blue-500/10 border-blue-500/30"
            : "text-amber-400 bg-amber-500/10 border-amber-500/30";

        return (
          <div className="flex items-start gap-3 p-2.5 rounded-lg bg-orange-950/20 border border-orange-500/20">
            <div className="w-7 h-7 rounded-md bg-orange-500/20 text-orange-400 flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between text-xs mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-orange-300">Code Audit Finding</span>
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.2 rounded border ${severityColor}`}
                  >
                    {severity}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-gray-500">{timeFormatted}</span>
              </div>
              <p className="text-xs text-gray-200">{item.message}</p>
              {item.metadata?.file && (
                <div className="text-[11px] font-mono text-gray-400 mt-1">
                  in {item.metadata.file} {item.metadata.line ? `:${item.metadata.line}` : ""}
                </div>
              )}
            </div>
          </div>
        );
      }

      case "PIPELINE_COMPLETE": {
        return (
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/40 via-indigo-950/40 to-emerald-950/40 border border-emerald-500/40 text-center shadow-lg shadow-emerald-500/10">
            <div className="flex items-center justify-center gap-2 text-emerald-400 font-bold text-sm mb-1">
              <Sparkles className="w-4 h-4 animate-spin" />
              <span>Full Pipeline Completed Successfully</span>
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <p className="text-xs text-gray-300">{item.message}</p>
            <div className="text-[11px] font-mono text-emerald-400/80 mt-1">
              {timeFormatted}
            </div>
          </div>
        );
      }

      case "PIPELINE_FAILED": {
        return (
          <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/40 text-center shadow-lg shadow-rose-500/10">
            <div className="flex items-center justify-center gap-2 text-rose-400 font-bold text-sm mb-1">
              <Flame className="w-4 h-4" />
              <span>Pipeline Execution Failed</span>
            </div>
            <p className="text-xs text-rose-200">{item.message}</p>
            <div className="text-[11px] font-mono text-gray-500 mt-1">{timeFormatted}</div>
          </div>
        );
      }

      default: {
        return (
          <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-white/[0.02] transition-colors border border-transparent hover:border-gray-800/40">
            {/* Agent Avatar Circle */}
            <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 bg-gray-900 border border-gray-700/60">
              {agentColor ? (
                <div className={`w-2.5 h-2.5 rounded-full ${agentColor.dot}`} />
              ) : (
                <Brain className="w-3 h-3 text-gray-400" />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between text-xs mb-0.5">
                <div className="flex items-center gap-2">
                  {item.agent && (
                    <span
                      className={`text-[11px] font-semibold uppercase tracking-wider ${
                        agentColor ? agentColor.text : "text-gray-400"
                      }`}
                    >
                      {item.agent}
                    </span>
                  )}
                  {item.from && item.to && (
                    <span className="text-[10px] text-gray-500 font-mono flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" />
                      {item.from} → {item.to}
                    </span>
                  )}
                  <span className="text-[10px] text-gray-500 uppercase">{item.type}</span>
                </div>
                <span className="text-[11px] font-mono text-gray-500">{timeFormatted}</span>
              </div>
              <p
                className={`text-xs leading-relaxed ${
                  item.isError ? "text-rose-400 font-mono" : "text-gray-300"
                }`}
              >
                {item.message}
              </p>
            </div>
          </div>
        );
      }
    }
  };

  return (
    <div
      className={`flex flex-col h-full bg-[#101018] rounded-xl border border-gray-800/80 overflow-hidden ${className}`}
    >
      {/* Header & Filter Controls */}
      <div className="p-3 bg-[#141420] border-b border-gray-800 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-brand-400" />
          <h3 className="text-xs font-semibold text-gray-200 tracking-wide uppercase">
            Live Agent Activity Feed
          </h3>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-brand-500/20 text-brand-300 border border-brand-500/30">
            {items.length} events
          </span>
        </div>

        <div className="flex items-center gap-1">
          {["ALL", "AGENTS", "FILES", "TESTS", "REVIEW"].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFilter(tab)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                filter === tab
                  ? "bg-brand-600 text-white shadow-sm"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/60"
              }`}
            >
              {tab}
            </button>
          ))}

          <button
            type="button"
            onClick={() => setAutoScroll(!autoScroll)}
            title={autoScroll ? "Disable auto-scroll" : "Enable auto-scroll"}
            className={`ml-2 p-1 rounded transition-colors text-xs flex items-center gap-1 ${
              autoScroll
                ? "text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20"
                : "text-gray-500 bg-gray-800/40 hover:bg-gray-800"
            }`}
          >
            {autoScroll ? <PlayCircle className="w-3.5 h-3.5" /> : <PauseCircle className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Feed List */}
      <div
        ref={containerRef}
        onScroll={handleUserScroll}
        className="flex-1 overflow-y-auto p-3 space-y-2.5 relative"
      >
        {filteredItems.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-500">
            <Terminal className="w-8 h-8 mb-2 opacity-40 text-brand-400" />
            <p className="text-xs">No activity recorded yet.</p>
            <p className="text-[11px] text-gray-600">Events from agents will stream in real-time.</p>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {filteredItems.map((item) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {renderItemContent(item)}
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {!autoScroll && filteredItems.length > 0 && (
        <div className="absolute bottom-4 right-4 z-10">
          <button
            type="button"
            onClick={scrollToBottom}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-brand-600 hover:bg-brand-500 text-white shadow-lg transition-transform active:scale-95"
          >
            <ArrowDownCircle className="w-3.5 h-3.5" />
            New Updates
          </button>
        </div>
      )}
    </div>
  );
}
