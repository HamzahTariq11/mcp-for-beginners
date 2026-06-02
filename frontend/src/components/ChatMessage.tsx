import { Bot, User } from "lucide-react";

import type { UiMessage } from "@/lib/chat-types";
import { Markdown } from "./Markdown";
import { ToolInvocation, type ToolPart } from "./ToolInvocation";

export function ChatMessage({ message }: { message: UiMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    const text = message.parts
      .map((p) => (p.type === "text" ? p.text : ""))
      .join("");
    return (
      <div className="flex justify-end gap-3">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-[15px] text-primary-foreground">
          {text}
        </div>
        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-foreground">
          <User className="h-4 w-4" />
        </span>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
        <Bot className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1 space-y-3 pt-1">
        {message.parts.map((part, i) => {
          if (part.type === "text") {
            return part.text ? <Markdown key={i}>{part.text}</Markdown> : null;
          }
          if (part.type.startsWith("tool-") || part.type === "dynamic-tool") {
            return <ToolInvocation key={i} part={part as unknown as ToolPart} />;
          }
          return null;
        })}
      </div>
    </div>
  );
}