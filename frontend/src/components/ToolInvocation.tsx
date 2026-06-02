import { useState } from "react";
import { ChevronDown, Loader2, Check, X, ArrowRight, ArrowLeft } from "lucide-react";

import { ToolIcon } from "./ToolIcon";
import { getToolMeta } from "@/lib/mcp-tools";

export type ToolPart = {
  type: string;
  toolCallId?: string;
  state?: "input-streaming" | "input-available" | "output-available" | "output-error";
  input?: unknown;
  output?: unknown;
  errorText?: string;
};

function fmt(value: unknown) {
  if (value === undefined) return "";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function ToolInvocation({ part }: { part: ToolPart }) {
  const toolName = part.type.replace(/^tool-/, "");
  const meta = getToolMeta(toolName);
  const isError = part.state === "output-error";
  const isRunning = part.state === "input-streaming" || part.state === "input-available";
  const isDone = part.state === "output-available";
  const [open, setOpen] = useState(true);

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card/60">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-secondary/50"
      >
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary">
          <ToolIcon name={meta?.icon ?? "wrench"} className="h-4 w-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <code className="font-mono text-sm font-medium text-foreground">{toolName}</code>
            {meta && (
              <span className="rounded bg-secondary px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                {meta.server}
              </span>
            )}
          </span>
        </span>
        <span className="flex shrink-0 items-center gap-2">
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-primary">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> running
            </span>
          )}
          {isDone && (
            <span className="flex items-center gap-1.5 text-xs text-success">
              <Check className="h-3.5 w-3.5" /> done
            </span>
          )}
          {isError && (
            <span className="flex items-center gap-1.5 text-xs text-destructive">
              <X className="h-3.5 w-3.5" /> error
            </span>
          )}
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
          />
        </span>
      </button>

      {open && (
        <div className="space-y-2.5 border-t border-border px-3 py-3">
          <div>
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              <ArrowRight className="h-3 w-3 text-accent" /> Input
            </div>
            <pre className="overflow-x-auto rounded-lg bg-secondary/70 p-2.5 font-mono text-[12px] text-foreground">
              {fmt(part.input) || "…"}
            </pre>
          </div>

          <div>
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              <ArrowLeft className="h-3 w-3 text-primary" /> Output
            </div>
            {isRunning ? (
              <div className="flex items-center gap-2 rounded-lg bg-secondary/70 p-2.5 font-mono text-[12px] text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> awaiting response from {meta?.server ?? "MCP server"}…
              </div>
            ) : (
              <pre
                className={`overflow-x-auto rounded-lg bg-secondary/70 p-2.5 font-mono text-[12px] ${
                  isError ? "text-destructive" : "text-foreground"
                }`}
              >
                {isError ? part.errorText ?? "Tool error" : fmt(part.output)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}