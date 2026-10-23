"use client";

import React from "react";
import { motion } from "framer-motion";
import { AgentName, AgentStatus } from "../lib/api";
import { formatDuration } from "../lib/utils";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  Layers,
  Code2,
  FlaskConical,
  ShieldCheck,
  Rocket,
  Compass,
} from "lucide-react";

interface AgentCardProps {
  name: AgentName;
  status: AgentStatus;
  durationS?: number;
  isActive: boolean;
  outputSummary?: string;
  onClick?: () => void;
}

const AGENT_CONFIG: Record<
  AgentName,
  {
    displayName: string;
    role: string;
    emoji: string;
    icon: React.ComponentType<{ className?: string }>;
    accentColor: string;
    glowClass: string;
    bgHover: string;
    badgeBg: string;
    borderActive: string;
  }
> = {
  planner: {
    displayName: "Planner",
    role: "Requirements & User Stories",
    emoji: "📋",
    icon: Compass,
    accentColor: "text-blue-400",
    glowClass: "shadow-[0_0_20px_rgba(59,130,246,0.35)]",
    bgHover: "hover:border-blue-500/40",
    badgeBg: "bg-blue-500/10 text-blue-300 border-blue-500/20",
    borderActive: "border-blue-500",
  },
  architect: {
    displayName: "Architect",
    role: "System Architecture & API Design",
    emoji: "🏛️",
    icon: Layers,
    accentColor: "text-purple-400",
    glowClass: "shadow-[0_0_20px_rgba(168,85,247,0.35)]",
    bgHover: "hover:border-purple-500/40",
    badgeBg: "bg-purple-500/10 text-purple-300 border-purple-500/20",
    borderActive: "border-purple-500",
  },
  coder: {
    displayName: "Coder",
    role: "Code Gen & Implementation",
    emoji: "💻",
    icon: Code2,
    accentColor: "text-emerald-400",
    glowClass: "shadow-[0_0_20px_rgba(16,185,129,0.35)]",
    bgHover: "hover:border-emerald-500/40",
    badgeBg: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
    borderActive: "border-emerald-500",
  },
  tester: {
    displayName: "Tester",
    role: "Unit & Integration Test Suites",
    emoji: "🧪",
    icon: FlaskConical,
    accentColor: "text-amber-400",
    glowClass: "shadow-[0_0_20px_rgba(234,179,8,0.35)]",
    bgHover: "hover:border-amber-500/40",
    badgeBg: "bg-amber-500/10 text-amber-300 border-amber-500/20",
    borderActive: "border-amber-500",
  },
  reviewer: {
    displayName: "Reviewer",
    role: "RAG Code & Security Audit",
    emoji: "🔍",
    icon: ShieldCheck,
    accentColor: "text-orange-400",
    glowClass: "shadow-[0_0_20px_rgba(249,115,22,0.35)]",
    bgHover: "hover:border-orange-500/40",
    badgeBg: "bg-orange-500/10 text-orange-300 border-orange-500/20",
    borderActive: "border-orange-500",
  },
  devops: {
    displayName: "DevOps",
    role: "Docker, CI/CD & Staging",
    emoji: "🚀",
    icon: Rocket,
    accentColor: "text-rose-400",
    glowClass: "shadow-[0_0_20px_rgba(239,68,68,0.35)]",
    bgHover: "hover:border-rose-500/40",
    badgeBg: "bg-rose-500/10 text-rose-300 border-rose-500/20",
    borderActive: "border-rose-500",
  },
};

export function AgentCard({
  name,
  status,
  durationS,
  isActive,
  outputSummary,
  onClick,
}: AgentCardProps) {
  const config = AGENT_CONFIG[name] || AGENT_CONFIG.planner;
  const Icon = config.icon;

  const renderStatusBadge = () => {
    switch (status) {
      case "running":
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin text-indigo-400" />
            Running
          </span>
        );
      case "complete":
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            Complete
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/15 text-rose-300 border border-rose-500/30">
            <AlertCircle className="w-3 h-3 text-rose-400" />
            Failed
          </span>
        );
      case "pending":
      default:
        return (
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-800/60 text-gray-400 border border-gray-700/50">
            <Clock className="w-3 h-3 text-gray-500" />
            Pending
          </span>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className={`relative overflow-hidden rounded-xl p-3.5 transition-all cursor-pointer border ${
        isActive
          ? `bg-[#161622] ${config.borderActive} ${config.glowClass}`
          : "bg-[#11111a] border-gray-800/80 hover:bg-[#141420] " + config.bgHover
      }`}
    >
      {/* Background highlight glow when active */}
      {isActive && (
        <div
          className="absolute inset-0 pointer-events-none opacity-20 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-shimmer"
        />
      )}

      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border text-lg transition-transform ${
              isActive ? "scale-105 border-white/20" : "border-gray-800"
            } bg-black/40`}
          >
            <span>{config.emoji}</span>
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-gray-100 tracking-tight truncate">
                {config.displayName}
              </h4>
              <Icon className={`w-3.5 h-3.5 ${config.accentColor}`} />
            </div>
            <p className="text-xs text-gray-400 truncate max-w-[170px]">
              {config.role}
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 shrink-0">
          {renderStatusBadge()}
          {status === "complete" && durationS !== undefined && (
            <span className="text-[11px] font-mono text-gray-400 flex items-center gap-1">
              {formatDuration(durationS)}
            </span>
          )}
        </div>
      </div>

      {outputSummary && (
        <div className="mt-2.5 pt-2 border-t border-gray-800/60 text-[11px] text-gray-400 line-clamp-2">
          {outputSummary}
        </div>
      )}
    </motion.div>
  );
}
