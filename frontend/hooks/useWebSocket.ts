"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { WSClient, WSEvent } from "../lib/ws";
import { useSessionStore } from "../stores/sessionStore";

export function useWebSocket(sessionId: string | null) {
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);
  const clientRef = useRef<WSClient | null>(null);

  const processEvent = useSessionStore((state) => state.processEvent);

  const handleEvent = useCallback(
    (event: WSEvent) => {
      processEvent(event);
    },
    [processEvent]
  );

  const handleStatusChange = useCallback(
    (connected: boolean, attempts: number) => {
      setIsConnected(connected);
      setReconnectCount(attempts);
    },
    []
  );

  useEffect(() => {
    if (!sessionId) {
      setIsConnected(false);
      setReconnectCount(0);
      return;
    }

    const client = new WSClient(sessionId, handleEvent, handleStatusChange);
    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
      clientRef.current = null;
      setIsConnected(false);
    };
  }, [sessionId, handleEvent, handleStatusChange]);

  return {
    isConnected,
    reconnectCount,
  };
}
