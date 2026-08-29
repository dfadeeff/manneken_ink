"use client";

import { useCallback, useRef, useState } from "react";

/**
 * Push-to-talk capture. Kept deliberately dumb: it hands back a blob and
 * nothing else, because everything a child says has to travel the same
 * guardrail path as everything a child types.
 */
export function useRecorder(onFinished: (audio: Blob) => void) {
  const [recording, setRecording] = useState(false);
  const [denied, setDenied] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const media = new MediaRecorder(stream);
      recorder.current = media;
      chunks.current = [];

      media.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.current.push(event.data);
      };
      media.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        if (blob.size > 0) onFinished(blob);
      };

      media.start();
      setRecording(true);
      setDenied(false);
    } catch {
      setDenied(true);
    }
  }, [onFinished]);

  const stop = useCallback(() => {
    recorder.current?.stop();
    setRecording(false);
  }, []);

  return { recording, denied, start, stop, toggle: () => (recording ? stop() : start()) };
}
