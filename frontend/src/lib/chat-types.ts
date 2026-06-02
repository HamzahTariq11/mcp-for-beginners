/**
 * Local chat types. The UI is driven entirely by the Python backend's SSE
 * stream (no AI SDK), so we define our own minimal message/part shapes here.
 * The shape intentionally mirrors what the rendering components expect:
 *   - text parts:  { type: "text", text }
 *   - tool parts:  { type: "tool-<name>", state, input, output }
 */

export type ToolState =
  | "input-streaming"
  | "input-available"
  | "output-available"
  | "output-error";

export type TextPart = { type: "text"; text: string };

export type ToolPart = {
  type: string; // "tool-<toolName>"
  toolCallId?: string;
  state?: ToolState;
  input?: unknown;
  output?: unknown;
  errorText?: string;
};

export type MessagePart = TextPart | ToolPart;

export type UiMessage = {
  id: string;
  role: "user" | "assistant";
  parts: MessagePart[];
};

export type ChatStatus = "ready" | "submitted" | "streaming" | "error";
