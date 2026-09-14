"use client";

import { useEffect, useRef } from "react";

const STORAGE_KEY = "reverse-engineer-sdlc:v1-workspace";
const SESSION_EXPIRY_MS = 60 * 60 * 1000;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type StoredWorkspace = {
  runId?: string;
  status?: string;
};

type RunStatus = {
  status: string;
  completed_at?: string | null;
};

export default function SessionExpiryControl() {
  const expiryTimerRef = useRef<number | null>(null);

  useEffect(() => {
    let completedCheckTimer: number | null = null;

    const expire = () => {
      if (completedCheckTimer !== null) window.clearInterval(completedCheckTimer);
      if (expiryTimerRef.current !== null) {
        window.clearTimeout(expiryTimerRef.current);
        expiryTimerRef.current = null;
      }
      window.sessionStorage.removeItem(STORAGE_KEY);
      window.location.replace("/session-expired");
    };

    const scheduleExpiry = (completedAt: string) => {
      const completedTime = Date.parse(completedAt);
      if (!Number.isFinite(completedTime)) return;
      const remaining = completedTime + SESSION_EXPIRY_MS - Date.now();
      if (remaining <= 0) {
        expire();
        return;
      }
      if (completedCheckTimer !== null) {
        window.clearInterval(completedCheckTimer);
        completedCheckTimer = null;
      }
      if (expiryTimerRef.current !== null) window.clearTimeout(expiryTimerRef.current);
      expiryTimerRef.current = window.setTimeout(expire, remaining);
    };

    const checkCompletedSession = async () => {
      try {
        const raw = window.sessionStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        const stored = JSON.parse(raw) as StoredWorkspace;
        if (!stored.runId || stored.status !== "completed") return;

        const response = await fetch(`${API_BASE_URL}/api/analysis/${stored.runId}/status`, { cache: "no-store" });
        if (response.status === 404) {
          expire();
          return;
        }
        if (!response.ok) return;

        const status = await response.json() as RunStatus;
        if (status.status === "completed" && status.completed_at) {
          scheduleExpiry(status.completed_at);
        }
      } catch {
        // A transient network error must not expire an otherwise valid session.
      }
    };

    completedCheckTimer = window.setInterval(checkCompletedSession, 1000);
    checkCompletedSession();

    return () => {
      if (completedCheckTimer !== null) window.clearInterval(completedCheckTimer);
      if (expiryTimerRef.current !== null) window.clearTimeout(expiryTimerRef.current);
    };
  }, []);

  return null;
}
