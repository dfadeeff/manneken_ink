"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useMemo } from "react";
import type { ChatMessage, Learner, Topic, TutorSession } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export function useApi() {
  const { getToken } = useAuth();

  const request = useCallback(
    async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
      const token = await getToken();
      const response = await fetch(`${API}${path}`, {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...init.headers,
        },
      });
      if (!response.ok) {
        throw new ApiError(response.status, await response.text());
      }
      return response.status === 204 ? (undefined as T) : response.json();
    },
    [getToken],
  );

  return useMemo(
    () => ({
      listLearners: () => request<Learner[]>("/api/learners"),

      createLearner: (body: Omit<Learner, "id">) =>
        request<Learner>("/api/learners", { method: "POST", body: JSON.stringify(body) }),

      topics: (learnerId: string) => request<Topic[]>(`/api/learners/${learnerId}/topics`),

      createSession: (body: { learner_id: string; subject?: string; topic_id?: string }) =>
        request<TutorSession>("/api/chat/sessions", {
          method: "POST",
          body: JSON.stringify(body),
        }),

      messages: (sessionId: string) =>
        request<ChatMessage[]>(`/api/chat/sessions/${sessionId}/messages`),

      /** Streams the tutor's reply, calling onDelta for each safe chunk. */
      streamReply: async (
        sessionId: string,
        message: string,
        onDelta: (text: string) => void,
      ): Promise<void> => {
        const token = await getToken();
        const response = await fetch(`${API}/api/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ session_id: sessionId, message }),
        });
        if (!response.ok || !response.body) {
          throw new ApiError(response.status, "stream failed");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          // SSE frames are separated by a blank line; keep any partial tail.
          const frames = buffer.split("\n\n");
          buffer = frames.pop() ?? "";
          for (const frame of frames) {
            const line = frame.split("\n").find((l) => l.startsWith("data: "));
            if (!line) continue;
            const event = JSON.parse(line.slice(6));
            if (event.type === "delta") onDelta(event.text);
          }
        }
      },
    }),
    [request, getToken],
  );
}
