"use client";

import React from "react";
import { motion } from "framer-motion";
import { AgentName } from "../lib/api";
import { AgentState } from "../stores/sessionStore";
import { formatDuration } from "../lib/utils";
import {
  CheckCircle2,
  Loader2,
  Clock,
  AlertCircle,
  Compass,
  Layers,
  Code2,
  FlaskConical,
  ShieldCheck,
  Rocket,
} from "lucide-react";

interface PipelineProgressProps {
  agents: Record<AgentName, AgentState>;
  currentAgent: AgentName | null;
  progressPercent: number;
  onStepClick?: (agent: AgentName) => void;
}

interface StepMeta {
  name: AgentName;
  title: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
}

const STEPS: StepMeta[] = [
  {
    name: "planner",
    title: "Planner",
    subtitle: "Spec & Requirements",
    icon: Compass,
  },
  {
    name: "architect",
    title: "Architect",
    subtitle: "System Architecture",
    icon: Layers,
  },
  {
    name: "coder",
    title: "Coder",
    subtitle: "Code Generation",
    icon: Code2,
  },
  {
    name: "tester",
    title: "Tester",
    subtitle: "Unit & Integration",
    icon: FlaskConical,
  },
  {
    name: "reviewer",
    title: "Reviewer",
    subtitle: "Code & Security Audit",
    icon: ShieldCheck,
  },
  {
    name: "devops",
    title: "DevOps",
    subtitle: "Docker & Staging",
    icon: Rocket,
  },
];

export function PipelineProgress({
  agents,
  currentAgent,
  progressPercent,
  onStepClick,
}: PipelineProgressProps) {
  return (
    <div className="bg-[#101018] rounded-xl border border-gray-800/80 p-4 space-y-4">
      {/* Top Header & Progress Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
            Pipeline Progress
          </span>
          <span className="text-xs font-mono font-bold text-brand-400">
            {progressPercent}%
          </span>
        </div>
        <div className="w-full h-2 bg-gray-900 rounded-full overflow-hidden border border-gray-800/80 relative">
          <motion.div
            className="h-full bg-gradient-to-r from-brand-600 via-indigo-500 to-emerald-400 rounded-full relative"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <div className="absolute inset-0 bg-white/20 animate-pulse" />
          </motion.div>
        </div>
      </div>

      {/* Stepper List */}
      <div className="relative pt-1 pb-1">
        {STEPS.map((step, idx) => {
          const agentData = agents[step.name] || { status: "pending" };
          const status = agentData.status;
          const isCurrent = currentAgent === step.name || status === "running";
          const isComplete = status === "complete";
          const isFailed = status === "failed";
          const StepIcon = step.icon;
          const isLast = idx === STEPS.length - 1;

          return (
            <div
              key={step.name}
              className="relative flex items-start group cursor-pointer"
              onClick={() => onStepClick?.(step.name)}
            >
              {/* Connecting line to next step */}
              {!isLast && (
                <div
                  className={`absolute left-[17px] top-[34px] w-[2px] h-[calc(100%-8px)] transition-colors duration-300 z-0 ${
                    isComplete
                      ? "bg-emerald-500/80"
                      : isCurrent
                      ? "bg-gradient-to-b from-indigo-500 to-gray-800 animate-pulse"
                      : "bg-gray-800"
                  }`}
                />
              )}

              {/* Step Icon Badge */}
              <div className="relative z-10 shrink-0">
                <motion.div
                  animate={
                    isCurrent
                      ? {
                          scale: [1, 1.08, 1],
                          boxShadow: [
                            "0 0 0px rgba(99, 102, 241, 0)",
                            "0 0 16px rgba(99, 102, 241, 0.6)",
                            "0 0 0px rgba(99, 102, 241, 0)",
                          ],
                        }
                      : {}
                  }
                  transition={{ repeat: Infinity, duration: 2 }}
                  className={`w-9 h-9 rounded-xl flex items-center justify-center border transition-all ${
                    isComplete
                      ? "bg-emerald-950/70 border-emerald-500/60 text-emerald-300"
                      : isCurrent
                      ? "bg-brand-950 border-brand-500 text-brand-200"
                      : isFailed
                      ? "bg-rose-950 border-rose-500 text-rose-300"
                      : "bg-[#141420] border-gray-800 text-gray-500"
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />
                  ) : isFailed ? (
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                  ) : (
                    <StepIcon className="w-4 h-4 text-gray-500" />
                  )}
                </motion.div>
              </div>

              {/* Step Text Info */}
              <div className="ml-3 pb-6 flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-semibold tracking-tight transition-colors ${
                      isComplete
                        ? "text-gray-100"
                        : isCurrent
                        ? "text-brand-300"
                        : isFailed
                        ? "text-rose-400"
                        : "text-gray-400"
                    }`}
                  >
                    {step.title}
                  </span>

                  {/* Duration Pill */}
                  {isComplete && agentData.durationS !== undefined ? (
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-500/20">
                      {formatDuration(agentData.durationS)}
                    </span>
                  ) : isCurrent ? (
                    <span className="text-[10px] font-mono text-brand-300 bg-brand-950/40 px-1.5 py-0.5 rounded border border-brand-500/30 animate-pulse">
                      Active
                    </span>
                  ) : (
                    <span className="text-[10px] text-gray-600 font-mono">
                      Step {idx + 1}
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-gray-500 truncate mt-0.5">
                  {step.subtitle}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
