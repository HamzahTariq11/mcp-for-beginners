import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { ArrowUp, Plane, Loader2, Square } from "lucide-react";
import { toast } from "sonner";

import { ChatMessage } from "@/components/ChatMessage";
import { ItineraryPanel, extractItinerary } from "@/components/ItineraryPanel";
import { useTripChat } from "@/lib/useTripChat";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Trip Planner · Live MCP Tool-Calling Demo" },
      {
        name: "description",
        content:
          "An interactive Model Context Protocol demo. Ask the travel agent to plan a trip and watch it call flight, hotel, weather and attraction tools live, then build a full itinerary.",
      },
      { property: "og:title", content: "Trip Planner · Live MCP Tool-Calling Demo" },
      {
        property: "og:description",
        content: "Watch a travel agent call MCP tools live and build a full trip itinerary.",
      },
    ],
  }),
  component: Index,
});

const SUGGESTIONS = [
  "Plan a 3-day cultural weekend in Istanbul from Karachi departing 2026-06-03, " +
    "back 2026-06-06. I have about 650 USD for the flight. I love museums and " +
    "historic sites, but want outdoor time too when the weather is nice. Compare a " +
    "few flights and hotels, check the forecast for each day, and give me a full " +
    "day-by-day plan.",
  "Research a luxury 3-night Dubai escape from London, 2026-06-03 to 2026-06-06. " +
    "I want a 5-star hotel, ideally with a spa. Compare flights, find the best hotel " +
    "within reason, check the weather, and mix indoor attractions (malls, galleries) " +
    "with outdoor ones for the cooler parts of the day. Save a full day-by-day itinerary.",
  "Plan a budget-friendly 3-night Bangkok trip from Karachi, 2026-06-04 to " +
    "2026-06-07, under 600 USD for the flight. I'm into temples, street-food markets, " +
    "and a couple of museums. Compare flight options, find a well-rated central hotel, " +
    "check the forecast, and build a daily schedule of outdoor and indoor spots.",
  "I want a relaxed weekend in Istanbul from Dubai, 2026-06-04 to 2026-06-06. Prefer " +
    "a highly-rated hotel near the historic centre. Find good flights, check the " +
    "forecast, pick scenic outdoor spots plus a couple of art museums, and save a " +
    "day-by-day itinerary.",
];

function Index() {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { messages, sendMessage, status, stop } = useTripChat({
    onError: (message) => toast.error(message),
  });

  const isBusy = status === "submitted" || status === "streaming";
  const itinerary = extractItinerary(messages);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, status]);

  useEffect(() => {
    if (!isBusy) inputRef.current?.focus();
  }, [isBusy]);

  const submit = (text: string) => {
    const value = text.trim();
    if (!value || isBusy) return;
    sendMessage({ text: value });
    setInput("");
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border px-6 py-3.5">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/15 text-primary">
              <Plane className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-base font-semibold leading-tight text-foreground">
                Trip Planner Agent
              </h1>
              <p className="text-xs text-muted-foreground">
                Ask for a trip — watch MCP tools get called live
              </p>
            </div>
          </div>
          <span className="hidden items-center gap-1.5 rounded-full border border-border px-3 py-1 text-xs text-muted-foreground sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            claude-sonnet-4-6 · live
          </span>
        </header>

        <div ref={scrollRef} className="relative flex-1 overflow-y-auto">
          <div className="pointer-events-none absolute inset-0 bg-grid opacity-30" />
          <div className="relative mx-auto w-full max-w-3xl px-6 py-6">
            {messages.length === 0 ? (
              <EmptyState onPick={submit} />
            ) : (
              <div className="space-y-7">
                {messages.map((m) => (
                  <ChatMessage key={m.id} message={m} />
                ))}
                {status === "submitted" && (
                  <div className="flex items-center gap-2 pl-11 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" /> thinking…
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-border px-6 py-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(input);
            }}
            className="mx-auto w-full max-w-3xl"
          >
            <div className="flex items-end gap-2 rounded-2xl border border-border bg-card px-3 py-2 focus-within:border-primary/60">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submit(input);
                  }
                }}
                rows={1}
                placeholder="Ask me to plan a trip…"
                className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-[15px] text-foreground outline-none placeholder:text-muted-foreground"
              />
              {isBusy ? (
                <button
                  type="button"
                  onClick={stop}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary text-foreground transition-colors hover:bg-muted"
                  aria-label="Stop"
                >
                  <Square className="h-4 w-4" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
                  aria-label="Send"
                >
                  <ArrowUp className="h-4 w-4" />
                </button>
              )}
            </div>
            <p className="mt-2 text-center text-[11px] text-muted-foreground">
              Live MCP tools · responses stream live
            </p>
          </form>
        </div>
      </main>

      <ItineraryPanel itinerary={itinerary} building={isBusy && !itinerary} />
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 text-primary shadow-[var(--glow-primary)]">
        <Plane className="h-7 w-7" />
      </span>
      <h2 className="mt-4 text-2xl font-semibold text-foreground">
        Plan a trip, live
      </h2>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Ask the travel agent to plan a trip and watch it call flight, hotel,
        weather and attraction MCP tools live, then assemble a full itinerary.
      </p>
      <div className="mt-7 grid w-full max-w-2xl gap-2.5 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="rounded-xl border border-border bg-card/50 px-4 py-3 text-left text-sm text-foreground transition-colors hover:border-primary/50 hover:bg-card"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
