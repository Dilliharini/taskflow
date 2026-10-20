import { useEffect, useRef, useState } from 'react';
import { TOKEN_KEY } from '../api/client';

function websocketUrl(projectId) {
  const configured = import.meta.env.VITE_WS_BASE_URL || import.meta.env.VITE_API_BASE_URL || '';
  const base = configured ? new URL(configured, window.location.href) : new URL(window.location.href);
  base.protocol = ['https:', 'wss:'].includes(base.protocol) ? 'wss:' : 'ws:';
  base.pathname = `${base.pathname.replace(/\/$/, '')}/api/v1/ws/projects/${projectId}`;
  base.search = '';
  return base.toString();
}

export function useProjectUpdates(projectId, onEvent) {
  const [connected, setConnected] = useState(false);
  const callbackRef = useRef(onEvent);
  callbackRef.current = onEvent;

  useEffect(() => {
    if (!projectId) return undefined;
    let socket;
    let retryTimer;
    let attempts = 0;
    let stopped = false;
    const maxAttempts = 5;

    const connect = () => {
      if (stopped) return;
      const token = window.localStorage.getItem(TOKEN_KEY);
      if (!token) return;
      try {
        socket = new WebSocket(websocketUrl(projectId));
      } catch {
        scheduleReconnect();
        return;
      }
      socket.onopen = () => {
        attempts = 0;
        setConnected(true);
        socket.send(JSON.stringify({ type: 'auth', access_token: token }));
      };
      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data);
          if (event.project_id === projectId) {
            if (event.type === 'notification_created') window.dispatchEvent(new Event('taskflow:notification'));
            callbackRef.current?.(event);
          }
        } catch {
          // Ignore malformed frames; REST remains the source of truth.
        }
      };
      socket.onerror = () => socket.close();
      socket.onclose = (event) => {
        setConnected(false);
        if (event.code !== 4401 && event.code !== 4403) scheduleReconnect();
      };
    };

    const scheduleReconnect = () => {
      if (stopped || attempts >= maxAttempts) return;
      const delay = Math.min(1000 * (2 ** attempts), 16000);
      attempts += 1;
      retryTimer = window.setTimeout(connect, delay);
    };

    connect();
    return () => {
      stopped = true;
      window.clearTimeout(retryTimer);
      if (socket) {
        socket.onclose = null;
        socket.close(1000, 'Project view closed');
      }
      setConnected(false);
    };
  }, [projectId]);

  return connected;
}