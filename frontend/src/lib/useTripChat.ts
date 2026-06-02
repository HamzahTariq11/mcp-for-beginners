import { useCallback, useRef, useState } from "react";

import type { ChatStatus, MessagePart, ToolPart, UiMessage } from "./chat-types";

/**
 * Minimal chat hook that talks to the Python FastAPI `/chat` endpoint and
 * consumes its Server-Sent Events, building up assistant message `parts` in the
 * shape the rendering components expect. No AI SDK involved — the agent (and
 * all tool-calling) lives in the backend.
 */

// The frontend dev server runs on :8080, so the backend must be elsewhere.
const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8090").replace(/\/+$/, "");

let counter = 0;
const newId = () => `m${counter++}-${Math.random().toString(36).slice(2, 8)}`;

type ServerEvent =
  | { type: "tool-input"; toolCallId: string; toolName: string; input: unknown }
  | { type: "tool-output"; toolCallId: string; toolName: string; output: unknown }
  | { type: "tool-error"; toolCallId: string; toolName: string; errorText: string }
  | { type: "text-delta"; delta: string }
  | { type: "error"; errorText: string }
  | { type: "done" };

export function useTripChat(options?: { onError?: (message: string) => void }) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus("ready");
  }, []);

  const sendMessage = useCallback(
    async ({ text }: { text: string }) => {
      const assistantId = newId();
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "user", parts: [{ type: "text", text }] },
        { id: assistantId, role: "assistant", parts: [] },
      ]);
      setStatus("submitted");

      const controller = new AbortController();
      abortRef.current = controller;

      // Mutate just the in-flight assistant message's parts.
      const patch = (fn: (parts: MessagePart[]) => MessagePart[]) =>
        setMessages((msgs) =>
          msgs.map((m) => (m.id === assistantId ? { ...m, parts: fn(m.parts) } : m)),
        );

      try {
        const res = await fetch(`${API_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) throw new Error(`Request failed (${res.status})`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let started = false;

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          // SSE messages are separated by a blank line.
          const blocks = buffer.split("\n\n");
          buffer = blocks.pop() ?? "";
          for (const block of blocks) {
            const dataLine = block.split("\n").find((l) => l.startsWith("data:"));
            if (!dataLine) continue;
            const evt = JSON.parse(dataLine.slice(5).trim()) as ServerEvent;
            if (!started) {
              started = true;
              setStatus("streaming");
            }
            applyEvent(evt, patch);
          }
        }
        setStatus("ready");
      } catch (err) {
        const e = err as Error;
        if (e.name === "AbortError") {
          setStatus("ready");
          return;
        }
        setStatus("error");
        options?.onError?.(e.message || "Something went wrong.");
      } finally {
        abortRef.current = null;
      }
    },
    [options],
  );

  return { messages, sendMessage, status, stop };
}

function applyEvent(evt: ServerEvent, patch: (fn: (parts: MessagePart[]) => MessagePart[]) => void) {
  switch (evt.type) {
    case "tool-input":
      patch((parts) => [
        ...parts,
        {
          type: `tool-${evt.toolName}`,
          toolCallId: evt.toolCallId,
          state: "input-available",
          input: evt.input,
        },
      ]);
      break;
    case "tool-output":
      patch((parts) =>
        parts.map((p) =>
          (p as ToolPart).toolCallId === evt.toolCallId
            ? { ...(p as ToolPart), state: "output-available", output: evt.output }
            : p,
        ),
      );
      break;
    case "tool-error":
      patch((parts) =>
        parts.map((p) =>
          (p as ToolPart).toolCallId === evt.toolCallId
            ? { ...(p as ToolPart), state: "output-error", errorText: evt.errorText }
            : p,
        ),
      );
      break;
    case "text-delta":
      patch((parts) => {
        const last = parts[parts.length - 1];
        if (last && last.type === "text") {
          return [...parts.slice(0, -1), { type: "text", text: last.text + evt.delta }];
        }
        return [...parts, { type: "text", text: evt.delta }];
      });
      break;
    case "error":
      patch((parts) => [...parts, { type: "text", text: `\n\n_Error: ${evt.errorText}_` }]);
      break;
    case "done":
    default:
      break;
  }
}
