'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, Copy, CheckCheck, ExternalLink, RefreshCw,
  Activity, Code2, TestTube2, ShieldCheck, Package, Wifi, WifiOff,
} from 'lucide-react';

import { useWebSocket } from '@/hooks/useWebSocket';
import { useSession } from '@/hooks/useSession';
import { useSessionStore } from '@/stores/sessionStore';
import { AgentCard } from '@/components/AgentCard';
import { PipelineProgress } from '@/components/PipelineProgress';
import { ActivityFeed } from '@/components/ActivityFeed';
import { CodePanel } from '@/components/CodePanel';
import { TestResultPanel } from '@/components/TestResultPanel';
import { ReviewPanel } from '@/components/ReviewPanel';
import { ArtifactList } from '@/components/ArtifactList';
import { api, AgentName } from '@/lib/api';
import { cn } from '@/lib/utils';

const TABS = [
  { id: 'activity',  label: 'Activity',   icon: Activity    },
  { id: 'code',      label: 'Code',       icon: Code2       },
  { id: 'tests',     label: 'Tests',      icon: TestTube2   },
  { id: 'review',    label: 'Review',     icon: ShieldCheck },
  { id: 'artifacts', label: 'Artifacts',  icon: Package     },
] as const;

const AGENT_ORDER: AgentName[] = ['planner','architect','coder','tester','reviewer','devops'];

export default function SessionPage() {
  const params   = useParams();
  const router   = useRouter();
  const id       = params.id as string;

  const [activeTab,  setActiveTab]  = useState<string>('activity');
  const [copied,     setCopied]     = useState(false);
  const [showBanner, setShowBanner] = useState(false);

  const { isConnected } = useWebSocket(id);
  const { session }     = useSession(id);

  const {
    status, requirement, progressPercent, agents, activityFeed,
    files, selectedFile, selectedFileContent, testResults,
    reviewIssues, stagingUrl, review_result,
    initSession, setSelectedFile,
  } = useSessionStore();

  /* bootstrap store once */
  useEffect(() => {
    if (id) initSession(id, '');
  }, [id, initSession]);

  /* show completion banner */
  useEffect(() => {
    if (status === 'complete') setShowBanner(true);
  }, [status]);

  /* auto-switch tabs on events */
  useEffect(() => {
    const lastType = activityFeed[activityFeed.length - 1]?.type;
    if (lastType === 'TEST_RESULT')  setActiveTab('tests');
    if (lastType === 'REVIEW_ISSUE') setActiveTab('review');
    if (lastType === 'FILE_CREATED') setActiveTab('code');
  }, [activityFeed.length]);

  const handleCopy = () => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFileSelect = async (path: string, artifactId: string) => {
    try {
      const res = await api.getArtifactContent(artifactId);
      setSelectedFile(path, typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2));
      setActiveTab('code');
    } catch { /* silent */ }
  };

  const statusColor: Record<string, string> = {
    pending:  'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
    running:  'text-blue-400   bg-blue-400/10   border-blue-400/30',
    complete: 'text-green-400  bg-green-400/10  border-green-400/30',
    failed:   'text-red-400    bg-red-400/10    border-red-400/30',
  };

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0f] text-white overflow-hidden">

      {/* ── Header ─────────────────────────────────────────── */}
      <header className="flex-none flex items-center justify-between px-6 py-3 border-b border-white/5 bg-black/40 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bot className="w-5 h-5" />
          </div>
          <span className="font-bold text-lg tracking-tight">MASDS</span>
          <span className="text-white/20 mx-1">|</span>
          <span className="text-xs font-mono text-white/40 hidden sm:block">{id}</span>
          <button onClick={handleCopy} className="text-white/30 hover:text-white/70 transition-colors">
            {copied ? <CheckCheck className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>

        <div className="flex items-center gap-3">
          {/* WS status */}
          <div className={cn("flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border",
            isConnected ? "text-green-400 bg-green-400/5 border-green-400/20" : "text-red-400 bg-red-400/5 border-red-400/20")}>
            {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {isConnected ? 'Live' : 'Reconnecting'}
          </div>
          {/* Pipeline status */}
          <span className={cn("text-xs px-2.5 py-1 rounded-full border font-medium capitalize", statusColor[status] || statusColor.pending)}>
            {status === 'running' && <RefreshCw className="w-3 h-3 inline mr-1 animate-spin" />}
            {status}
          </span>
        </div>
      </header>

      {/* ── Completion Banner ───────────────────────────────── */}
      <AnimatePresence>
        {showBanner && stagingUrl && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="flex-none bg-gradient-to-r from-green-900/60 to-emerald-900/60 border-b border-green-500/20 px-6 py-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-2 text-sm">
              <span className="text-2xl">🎉</span>
              <span className="text-green-300 font-medium">Pipeline complete!</span>
              <span className="text-white/50">Your app is deployed to staging.</span>
            </div>
            <a href={stagingUrl} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-green-300 hover:text-green-100 transition-colors bg-green-500/10 border border-green-500/30 px-3 py-1.5 rounded-lg">
              <ExternalLink className="w-3.5 h-3.5" />
              {stagingUrl}
            </a>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Main layout ─────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Left Sidebar ──────────────────────────────────── */}
        <aside className="w-72 flex-none flex flex-col border-r border-white/5 bg-black/20 overflow-y-auto">
          {/* Progress bar */}
          <div className="p-4 border-b border-white/5">
            <PipelineProgress />
          </div>

          {/* Agent cards */}
          <div className="p-3 flex flex-col gap-2">
            {AGENT_ORDER.map(name => (
              <AgentCard
                key={name}
                name={name}
                status={agents[name]?.status ?? 'pending'}
                durationS={agents[name]?.durationS}
                isActive={agents[name]?.status === 'running'}
              />
            ))}
          </div>

          {/* Staging URL */}
          {stagingUrl && (
            <div className="m-3 mt-auto p-3 rounded-xl border border-green-500/20 bg-green-500/5">
              <p className="text-xs text-white/40 mb-1">Staging URL</p>
              <a href={stagingUrl} target="_blank" rel="noopener noreferrer"
                className="text-xs text-green-400 hover:text-green-300 flex items-center gap-1 break-all">
                <ExternalLink className="w-3 h-3 flex-none" />
                {stagingUrl}
              </a>
            </div>
          )}
        </aside>

        {/* ── Main content ──────────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="flex-none flex items-center gap-1 px-4 pt-3 pb-0 border-b border-white/5">
            {TABS.map(({ id: tid, label, icon: Icon }) => (
              <button
                key={tid}
                onClick={() => setActiveTab(tid)}
                className={cn(
                  "flex items-center gap-1.5 text-sm px-3 py-2 rounded-t-lg border-b-2 transition-all",
                  activeTab === tid
                    ? "border-blue-500 text-blue-400 bg-blue-500/5"
                    : "border-transparent text-white/40 hover:text-white/70"
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
                {tid === 'tests' && testResults && (
                  <span className={cn("text-xs ml-1 px-1.5 rounded-full",
                    testResults.failed > 0 ? "bg-red-500/20 text-red-400" : "bg-green-500/20 text-green-400")}>
                    {testResults.passed}/{testResults.passed + testResults.failed}
                  </span>
                )}
                {tid === 'review' && reviewIssues.length > 0 && (
                  <span className="text-xs ml-1 px-1.5 rounded-full bg-orange-500/20 text-orange-400">
                    {reviewIssues.length}
                  </span>
                )}
                {tid === 'code' && files.length > 0 && (
                  <span className="text-xs ml-1 px-1.5 rounded-full bg-white/10 text-white/50">
                    {files.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'activity'  && <ActivityFeed items={activityFeed} />}
            {activeTab === 'code'      && (
              <CodePanel
                files={files}
                selectedFile={selectedFile}
                selectedContent={selectedFileContent}
                onFileSelect={handleFileSelect}
              />
            )}
            {activeTab === 'tests'     && <TestResultPanel results={testResults} />}
            {activeTab === 'review'    && <ReviewPanel result={review_result} issues={reviewIssues} />}
            {activeTab === 'artifacts' && (
              <ArtifactList
                files={files}
                sessionId={id}
                onFileSelect={handleFileSelect}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
