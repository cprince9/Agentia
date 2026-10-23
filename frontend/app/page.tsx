"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Sparkles,
  ArrowRight,
  Loader2,
  Code2,
  Layers,
  FlaskConical,
  ShieldCheck,
  Rocket,
  Compass,
  Cpu,
  Bot,
  Zap,
  CheckCircle,
  Terminal,
} from "lucide-react";
import { api } from "../lib/api";
import { useSessionStore } from "../stores/sessionStore";

const EXAMPLE_REQUIREMENTS = [
  "Build a real-time collaborative whiteboarding canvas with WebSockets, room management, and Redis pub/sub.",
  "Build a high-performance REST API in FastAPI with PostgreSQL, Redis cache, and JWT authentication.",
  "Build an e-commerce microservice with Stripe checkout, inventory management, and Docker Compose.",
  "Build a SaaS analytics dashboard with event tracking, telemetry, and automated PDF report generation.",
];

const AGENT_BADGES = [
  { name: "Planner", role: "User Stories & Spec", icon: Compass, color: "text-blue-400 border-blue-500/30 bg-blue-500/10", x: -80, y: -40, delay: 0 },
  { name: "Architect", role: "System Design", icon: Layers, color: "text-purple-400 border-purple-500/30 bg-purple-500/10", x: 120, y: -60, delay: 0.5 },
  { name: "Coder", role: "Implementation", icon: Code2, color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10", x: -140, y: 80, delay: 1 },
  { name: "Tester", role: "Test Suites", icon: FlaskConical, color: "text-amber-400 border-amber-500/30 bg-amber-500/10", x: 150, y: 70, delay: 1.5 },
  { name: "Reviewer", role: "RAG Security Audit", icon: ShieldCheck, color: "text-orange-400 border-orange-500/30 bg-orange-500/10", x: -100, y: 180, delay: 2 },
  { name: "DevOps", role: "Docker & Staging", icon: Rocket, color: "text-rose-400 border-rose-500/30 bg-rose-500/10", x: 110, y: 190, delay: 2.5 },
];

export default function LandingPage() {
  const router = useRouter();
  const initSession = useSessionStore((state) => state.initSession);

  const [requirement, setRequirement] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleStartBuilding = async () => {
    if (!requirement.trim()) {
      setErrorMessage("Please describe the software requirement you want to build.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await api.createSession(requirement.trim());
      const sessionId =
        response.data.id || response.data.session_id || `session-${Date.now()}`;

      initSession(sessionId, requirement.trim());
      router.push(`/session/${sessionId}`);
    } catch (err: any) {
      console.warn("API creation failed, creating autonomous local session fallback:", err);
      // Fallback gracefully so user can immediately experience the dashboard even if backend hasn't booted
      const fallbackId = `session-${Date.now().toString(36)}`;
      initSession(fallbackId, requirement.trim());
      router.push(`/session/${fallbackId}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleStartBuilding();
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-between overflow-hidden bg-[#0a0a0f]">
      {/* Background Cyber Glowing Orbs & Grid */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-gradient-to-tr from-brand-600/15 via-purple-600/10 to-transparent blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute top-2/3 right-10 w-[400px] h-[400px] bg-emerald-600/10 blur-[130px] pointer-events-none rounded-full" />
      <div className="absolute top-1/3 left-10 w-[350px] h-[350px] bg-rose-600/10 blur-[130px] pointer-events-none rounded-full" />

      {/* ── TOP NAV ── */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/30">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white">
                MASDS
              </span>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30">
                Autonomous
              </span>
            </div>
            <span className="text-[11px] text-gray-400 block -mt-0.5">
              Multi-Agent Software Development System
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#141420] border border-gray-800 text-gray-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            6 AI Agents Active
          </span>
        </div>
      </header>

      {/* ── HERO SECTION ── */}
      <main className="relative z-10 max-w-5xl mx-auto px-6 py-12 flex-1 flex flex-col items-center justify-center text-center">
        {/* Floating animated Agent Icons */}
        <div className="hidden lg:block absolute inset-0 pointer-events-none overflow-hidden">
          {AGENT_BADGES.map((agent, i) => {
            const Icon = agent.icon;
            return (
              <motion.div
                key={agent.name}
                className={`absolute px-3 py-1.5 rounded-xl border flex items-center gap-2 shadow-lg backdrop-blur-md ${agent.color}`}
                style={{
                  top: `calc(40% + ${agent.y}px)`,
                  left: `calc(50% + ${agent.x * 2.2}px)`,
                }}
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  duration: 4 + i,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: agent.delay,
                }}
              >
                <Icon className="w-4 h-4" />
                <div className="text-left">
                  <span className="text-xs font-bold block">{agent.name}</span>
                  <span className="text-[10px] opacity-75 font-mono">{agent.role}</span>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Title & Subtitle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-4 max-w-3xl"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium mb-2">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            Next-Gen Autonomous Agent Orchestration
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white leading-[1.1]">
            Build Software with{" "}
            <span className="bg-gradient-to-r from-brand-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
              AI Agents
            </span>
          </h1>

          <p className="text-sm sm:text-base text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Specify your requirement. Watch six collaborative AI agents plan user stories, design architecture, generate code, execute automated test suites, audit security, and deploy staging containers in real time.
          </p>
        </motion.div>

        {/* ── INTERACTIVE INPUT BOX ── */}
        <motion.div
          initial={{ opacity: 0, y: 25 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="w-full max-w-3xl mt-8"
        >
          <div className="p-1 rounded-2xl bg-gradient-to-b from-brand-500/30 via-indigo-500/10 to-transparent shadow-2xl">
            <div className="bg-[#11111a] rounded-2xl border border-gray-800 p-4 md:p-5 text-left space-y-4">
              <label
                htmlFor="requirement-input"
                className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center justify-between"
              >
                <span>Software Requirement</span>
                <span className="font-mono text-[11px] text-gray-500">
                  Ctrl / Cmd + Enter to execute
                </span>
              </label>

              <div className="relative">
                <textarea
                  id="requirement-input"
                  rows={4}
                  value={requirement}
                  onChange={(e) => setRequirement(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe the software you want to build (e.g., 'Build a high-performance REST API in FastAPI with PostgreSQL, Redis caching, and JWT authentication')..."
                  className="w-full bg-[#161622] text-gray-100 placeholder-gray-500 text-sm p-4 rounded-xl border border-gray-700/60 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all resize-none"
                />
              </div>

              {/* Example Chips */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                  Or select an example architecture:
                </span>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_REQUIREMENTS.map((ex, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setRequirement(ex)}
                      className="text-xs text-left px-3 py-1.5 rounded-lg bg-[#181826] hover:bg-brand-950/60 hover:text-brand-200 text-gray-300 border border-gray-800 hover:border-brand-500/40 transition-all"
                    >
                      {ex.length > 55 ? `${ex.substring(0, 55)}...` : ex}
                    </button>
                  ))}
                </div>
              </div>

              {errorMessage && (
                <div className="text-xs text-rose-400 bg-rose-950/30 p-2.5 rounded-lg border border-rose-500/30">
                  {errorMessage}
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                    Multi-Agent Pipeline
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                    Live WebSockets
                  </span>
                </div>

                <button
                  type="button"
                  disabled={isLoading}
                  onClick={handleStartBuilding}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-brand-600 via-indigo-600 to-brand-600 hover:from-brand-500 hover:to-indigo-500 shadow-lg shadow-brand-500/25 transition-all transform active:scale-95 disabled:opacity-60"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Initializing Agents...</span>
                    </>
                  ) : (
                    <>
                      <span>Start Building</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── FEATURE CARDS ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl w-full mt-16 text-left"
        >
          <div className="p-4 rounded-xl bg-[#11111a] border border-gray-800">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3">
              <Bot className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-bold text-gray-100 uppercase tracking-wider mb-1">
              Autonomous Handshakes
            </h4>
            <p className="text-xs text-gray-400">
              Agents coordinate over structured protocol streams — Planner generates specs, Architect drafts interfaces, and Coder writes modular code.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#11111a] border border-gray-800">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3">
              <FlaskConical className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-bold text-gray-100 uppercase tracking-wider mb-1">
              Self-Healing Test Cycles
            </h4>
            <p className="text-xs text-gray-400">
              Tester executes unit & integration test suites, returning stack traces and failure diffs to the Coder agent for autonomous resolution.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#11111a] border border-gray-800">
            <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center mb-3">
              <Rocket className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-bold text-gray-100 uppercase tracking-wider mb-1">
              Instant Staging Deployment
            </h4>
            <p className="text-xs text-gray-400">
              DevOps agent generates Dockerfiles, CI/CD pipelines, and health checks, exposing a live staging URL once review criteria pass.
            </p>
          </div>
        </motion.div>
      </main>

      {/* ── FOOTER ── */}
      <footer className="w-full border-t border-gray-800/80 py-4 px-6 text-center text-xs text-gray-500 relative z-20">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>MASDS © 2026 Multi-Agent Software Development System</span>
          <div className="flex items-center gap-4 font-mono text-[11px]">
            <span>Next.js 14</span>
            <span>•</span>
            <span>FastAPI</span>
            <span>•</span>
            <span>WebSockets</span>
            <span>•</span>
            <span>Monaco Editor</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
