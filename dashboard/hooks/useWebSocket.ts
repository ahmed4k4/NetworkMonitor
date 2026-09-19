"use client";

import { useEffect, useRef, useState } from "react";

import { createWebSocketClient, type WebSocketStatus } from "@/lib/websocket";

export function useWebSocket(
  onMessage: (data: unknown) => void,
): WebSocketStatus {
  const [status, setStatus] = useState<WebSocketStatus>("closed");
  const onMessageRef = useRef(onMessage);

  // Keep the latest callback reference
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    const client = createWebSocketClient(
      (data) => {
        onMessageRef.current(data);
      },
      (newStatus) => {
        setStatus(newStatus);
      },
    );

    client.connect();

    return () => {
      client.disconnect();
    };
  }, []);

  return status;
}