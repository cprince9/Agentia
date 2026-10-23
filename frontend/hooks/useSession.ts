"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { api, SessionData, ArtifactItem } from "../lib/api";
import { useSessionStore } from "../stores/sessionStore";

export function useSession(sessionId: string | null) {
  const [session, setSession] = useState<SessionData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const syncFromApi = useSessionStore((state) => state.syncFromApi);
  const setFiles = useSessionStore((state) => state.setFiles);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchSessionAndArtifacts = useCallback(async () => {
    if (!sessionId) {
      setIsLoading(false);
      return;
    }

    try {
      const [sessionRes, artifactsRes] = await Promise.allSettled([
        api.getSession(sessionId),
        api.getArtifacts(sessionId),
      ]);

      if (sessionRes.status === "fulfilled" && sessionRes.value.data) {
        const data = sessionRes.value.data;
        setSession(data);
        syncFromApi(data);
        setError(null);

        // If session finished, stop further polling
        if (data.status === "complete" || data.status === "failed") {
          if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
        }
      } else if (sessionRes.status === "rejected") {
        const err = sessionRes.reason;
        console.warn("[useSession] Session fetch warning:", err?.message || err);
      }

      if (artifactsRes.status === "fulfilled" && artifactsRes.value.data) {
        const artifacts: ArtifactItem[] = artifactsRes.value.data;
        if (Array.isArray(artifacts)) {
          setFiles(
            artifacts.map((a) => ({
              id: a.id,
              path: a.path || a.name,
              type: a.type || "source",
              size: a.size,
            }))
          );
        }
      }
    } catch (err: any) {
      console.error("[useSession] Error:", err);
      setError(err?.response?.data?.detail || err?.message || "Failed to load session");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, syncFromApi, setFiles]);

  useEffect(() => {
    if (!sessionId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    fetchSessionAndArtifacts();

    // Poll every 5 seconds
    pollTimerRef.current = setInterval(() => {
      fetchSessionAndArtifacts();
    }, 5000);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [sessionId, fetchSessionAndArtifacts]);

  return {
    session,
    isLoading,
    error,
    refetch: fetchSessionAndArtifacts,
  };
}
