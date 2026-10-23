import { create } from "zustand";
import { AgentName, AgentStatus, SessionStatus, SessionData } from "../lib/api";
import { WSEvent, WSEventType } from "../lib/ws";

export interface AgentState {
  name: AgentName;
  status: AgentStatus;
  startedAt?: string;
  endedAt?: string;
  durationS?: number;
  outputSummary?: string;
}

export interface ActivityItem {
  id: string;
  type: WSEventType;
  agent?: AgentName;
  from?: AgentName;
  to?: AgentName;
  message: string;
  timestamp: string;
  isError?: boolean;
  metadata?: any;
}

export interface TestResultData {
  passed: number;
  failed: number;
  coverage: number;
  details?: Array<{
    name: string;
    status: "passed" | "failed";
    error?: string;
    durationMs?: number;
  }>;
}

export interface ReviewIssueItem {
  severity: "HIGH" | "MEDIUM" | "LOW" | string;
  file: string;
  line?: number;
  issue: string;
  suggestion?: string;
  source?: string;
}

export interface FileItem {
  path: string;
  type: string;
  id: string;
  size?: number;
}

export interface SessionState {
  sessionId: string | null;
  status: SessionStatus;
  requirement: string;
  progressPercent: number;
  currentAgent: AgentName | null;
  agents: Record<AgentName, AgentState>;
  activityFeed: ActivityItem[];
  files: FileItem[];
  selectedFile: string | null;
  selectedFileContent: string | null;
  selectedFileLoading: boolean;
  testResults: TestResultData | null;
  reviewIssues: ReviewIssueItem[];
  reviewScore: number | null;
  stagingUrl: string | null;
  error: string | null;

  // Actions
  initSession: (id: string, requirement: string) => void;
  syncFromApi: (data: SessionData) => void;
  processEvent: (event: WSEvent) => void;
  setSelectedFile: (path: string, content: string) => void;
  setSelectedFileLoading: (loading: boolean) => void;
  addActivity: (item: ActivityItem) => void;
  setFiles: (files: FileItem[]) => void;
  setStagingUrl: (url: string | null) => void;
  resetSession: () => void;
}

const AGENT_ORDER: AgentName[] = [
  "planner",
  "architect",
  "coder",
  "tester",
  "reviewer",
  "devops",
];

const initialAgents: Record<AgentName, AgentState> = {
  planner: { name: "planner", status: "pending" },
  architect: { name: "architect", status: "pending" },
  coder: { name: "coder", status: "pending" },
  tester: { name: "tester", status: "pending" },
  reviewer: { name: "reviewer", status: "pending" },
  devops: { name: "devops", status: "pending" },
};

function calculateProgress(
  agents: Record<AgentName, AgentState>,
  overallStatus: SessionStatus
): number {
  if (overallStatus === "complete") return 100;
  let total = 0;
  const stepWeight = 100 / AGENT_ORDER.length;

  for (const name of AGENT_ORDER) {
    const ag = agents[name];
    if (!ag) continue;
    if (ag.status === "complete") {
      total += stepWeight;
    } else if (ag.status === "running") {
      total += stepWeight * 0.45;
    }
  }

  return Math.min(Math.round(total), overallStatus === "complete" ? 100 : 99);
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessionId: null,
  status: "pending",
  requirement: "",
  progressPercent: 0,
  currentAgent: null,
  agents: { ...initialAgents },
  activityFeed: [],
  files: [],
  selectedFile: null,
  selectedFileContent: null,
  selectedFileLoading: false,
  testResults: null,
  reviewIssues: [],
  reviewScore: null,
  stagingUrl: null,
  error: null,

  initSession: (id: string, requirement: string) => {
    set({
      sessionId: id,
      requirement,
      status: "running",
      progressPercent: 5,
      currentAgent: "planner",
      agents: {
        planner: { name: "planner", status: "running", startedAt: new Date().toISOString() },
        architect: { name: "architect", status: "pending" },
        coder: { name: "coder", status: "pending" },
        tester: { name: "tester", status: "pending" },
        reviewer: { name: "reviewer", status: "pending" },
        devops: { name: "devops", status: "pending" },
      },
      activityFeed: [
        {
          id: `init-${Date.now()}`,
          type: "AGENT_STARTED",
          agent: "planner",
          message: "Initialized autonomous MASDS session. Planner agent started requirement analysis.",
          timestamp: new Date().toISOString(),
        },
      ],
      files: [],
      selectedFile: null,
      selectedFileContent: null,
      testResults: null,
      reviewIssues: [],
      reviewScore: null,
      stagingUrl: null,
      error: null,
    });
  },

  syncFromApi: (data: SessionData) => {
    set((state) => {
      const updatedAgents = { ...state.agents };
      if (data.agents) {
        for (const [name, info] of Object.entries(data.agents)) {
          const agentName = name as AgentName;
          if (updatedAgents[agentName]) {
            updatedAgents[agentName] = {
              ...updatedAgents[agentName],
              status: info.status || updatedAgents[agentName].status,
              startedAt: info.startedAt || updatedAgents[agentName].startedAt,
              endedAt: info.endedAt || updatedAgents[agentName].endedAt,
              durationS: info.durationS ?? updatedAgents[agentName].durationS,
              outputSummary: info.outputSummary || updatedAgents[agentName].outputSummary,
            };
          }
        }
      }

      const newStatus = data.status || state.status;
      const progress =
        data.progressPercent ?? calculateProgress(updatedAgents, newStatus);

      return {
        status: newStatus,
        requirement: data.requirement || state.requirement,
        progressPercent: progress,
        currentAgent: data.currentAgent !== undefined ? data.currentAgent : state.currentAgent,
        stagingUrl: data.stagingUrl !== undefined ? data.stagingUrl : state.stagingUrl,
        agents: updatedAgents,
        testResults: data.testResults || state.testResults,
        reviewIssues: data.reviewIssues || state.reviewIssues,
        reviewScore: data.reviewScore ?? state.reviewScore,
      };
    });
  },

  processEvent: (event: WSEvent) => {
    const { type, agent, message, payload, timestamp } = event;
    const now = timestamp || new Date().toISOString();

    set((state) => {
      const updatedAgents = { ...state.agents };
      let newCurrentAgent = state.currentAgent;
      let newStatus = state.status;
      let newTestResults = state.testResults;
      let newReviewIssues = [...state.reviewIssues];
      let newReviewScore = state.reviewScore;
      let newStagingUrl = state.stagingUrl;
      const newFiles = [...state.files];
      let isError = false;

      switch (type) {
        case "AGENT_STARTED": {
          if (agent && updatedAgents[agent]) {
            updatedAgents[agent] = {
              ...updatedAgents[agent],
              status: "running",
              startedAt: updatedAgents[agent].startedAt || now,
            };
            newCurrentAgent = agent;
            newStatus = "running";
          }
          break;
        }

        case "AGENT_THINKING": {
          if (agent && updatedAgents[agent]) {
            if (updatedAgents[agent].status !== "complete") {
              updatedAgents[agent].status = "running";
            }
            newCurrentAgent = agent;
          }
          break;
        }

        case "AGENT_COMPLETE": {
          if (agent && updatedAgents[agent]) {
            const started = updatedAgents[agent].startedAt
              ? new Date(updatedAgents[agent].startedAt!).getTime()
              : Date.now() - 5000;
            const duration = payload?.durationS || Math.max(1, Math.round((Date.now() - started) / 1000));
            updatedAgents[agent] = {
              ...updatedAgents[agent],
              status: "complete",
              endedAt: now,
              durationS: duration,
              outputSummary: payload?.summary || message,
            };

            // Advance current agent to next in sequence if any
            const currentIndex = AGENT_ORDER.indexOf(agent);
            if (currentIndex >= 0 && currentIndex < AGENT_ORDER.length - 1) {
              newCurrentAgent = AGENT_ORDER[currentIndex + 1];
            }
          }
          break;
        }

        case "AGENT_FAILED": {
          isError = true;
          if (agent && updatedAgents[agent]) {
            updatedAgents[agent] = {
              ...updatedAgents[agent],
              status: "failed",
              endedAt: now,
              outputSummary: message,
            };
          }
          newStatus = "failed";
          break;
        }

        case "FILE_CREATED": {
          const filePath = payload?.path || payload?.filename || message;
          const fileId = payload?.id || `${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
          const fileType =
            payload?.type ||
            (filePath.includes("test")
              ? "test"
              : filePath.includes("Dockerfile") || filePath.includes(".yml") || filePath.includes(".yaml")
              ? "devops"
              : "source");

          if (filePath && !newFiles.some((f) => f.path === filePath)) {
            newFiles.push({
              path: filePath,
              type: fileType,
              id: fileId,
              size: payload?.size || (payload?.content ? payload.content.length : undefined),
            });
          }
          break;
        }

        case "TEST_RESULT": {
          if (payload) {
            newTestResults = {
              passed: payload.passed ?? (newTestResults?.passed || 0),
              failed: payload.failed ?? (newTestResults?.failed || 0),
              coverage: payload.coverage ?? (newTestResults?.coverage || 0),
              details: payload.details || newTestResults?.details,
            };
          }
          break;
        }

        case "REVIEW_ISSUE": {
          if (payload?.issue || payload?.issues) {
            const issuesToAdd: ReviewIssueItem[] = Array.isArray(payload.issues)
              ? payload.issues
              : [payload];
            for (const issue of issuesToAdd) {
              if (issue && issue.issue) {
                newReviewIssues.push({
                  severity: issue.severity || "MEDIUM",
                  file: issue.file || "unknown",
                  line: issue.line,
                  issue: issue.issue,
                  suggestion: issue.suggestion,
                  source: issue.source || "Static Analysis",
                });
              }
            }
          }
          if (payload?.score !== undefined) {
            newReviewScore = payload.score;
          }
          break;
        }

        case "PIPELINE_COMPLETE": {
          newStatus = "complete";
          newCurrentAgent = null;
          // Mark all agents complete
          for (const a of AGENT_ORDER) {
            if (updatedAgents[a].status !== "failed") {
              updatedAgents[a].status = "complete";
            }
          }
          if (payload?.stagingUrl) {
            newStagingUrl = payload.stagingUrl;
          }
          break;
        }

        case "PIPELINE_FAILED": {
          newStatus = "failed";
          isError = true;
          break;
        }

        default:
          break;
      }

      // Add to activity feed (keep up to 200 items)
      const newActivity: ActivityItem = {
        id: String(event.id || `${Date.now()}-${Math.random().toString(36).substr(2, 6)}`),
        type,
        agent,
        from: event.from,
        to: event.to,
        message: message || `Event: ${type}`,
        timestamp: now,
        isError: isError || type === "AGENT_FAILED" || type === "PIPELINE_FAILED",
        metadata: payload,
      };

      const updatedFeed = [...state.activityFeed, newActivity].slice(-200);
      const computedProgress = calculateProgress(updatedAgents, newStatus);

      return {
        agents: updatedAgents,
        currentAgent: newCurrentAgent,
        status: newStatus,
        progressPercent: computedProgress,
        activityFeed: updatedFeed,
        files: newFiles,
        testResults: newTestResults,
        reviewIssues: newReviewIssues,
        reviewScore: newReviewScore,
        stagingUrl: newStagingUrl,
      };
    });
  },

  setSelectedFile: (path: string, content: string) => {
    set({
      selectedFile: path,
      selectedFileContent: content,
      selectedFileLoading: false,
    });
  },

  setSelectedFileLoading: (loading: boolean) => {
    set({ selectedFileLoading: loading });
  },

  addActivity: (item: ActivityItem) => {
    set((state) => ({
      activityFeed: [...state.activityFeed, item].slice(-200),
    }));
  },

  setFiles: (files: FileItem[]) => {
    set({ files });
  },

  setStagingUrl: (stagingUrl: string | null) => {
    set({ stagingUrl });
  },

  resetSession: () => {
    set({
      sessionId: null,
      status: "pending",
      requirement: "",
      progressPercent: 0,
      currentAgent: null,
      agents: { ...initialAgents },
      activityFeed: [],
      files: [],
      selectedFile: null,
      selectedFileContent: null,
      selectedFileLoading: false,
      testResults: null,
      reviewIssues: [],
      reviewScore: null,
      stagingUrl: null,
      error: null,
    });
  },
}));
