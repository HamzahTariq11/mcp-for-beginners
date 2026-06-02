import type { UiMessage } from "@/lib/chat-types";
import {
  CalendarDays,
  Plane,
  Hotel,
  Wallet,
  MapPin,
  StickyNote,
  Compass,
  Loader2,
} from "lucide-react";

export type Itinerary = {
  itinerary_id: string;
  trip_name: string;
  created_at?: string;
  flight_id?: string;
  hotel_id?: number;
  hotel_name?: string;
  checkin?: string;
  checkout?: string;
  total_flight_cost?: number;
  total_hotel_cost?: number;
  total_cost?: number;
  daily_schedule?: Record<string, string[]>;
  notes?: string;
};

function money(n?: number) {
  if (typeof n !== "number") return "—";
  return `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(d?: string) {
  if (!d) return "";
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return d;
  return date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

/** Extract the latest finalised itinerary from the assistant's tool calls. */
export function extractItinerary(messages: UiMessage[]): Itinerary | null {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.role !== "assistant") continue;
    for (let j = m.parts.length - 1; j >= 0; j--) {
      const part = m.parts[j] as { type?: string; state?: string; output?: unknown };
      if (
        part.type === "tool-create_itinerary" &&
        part.state === "output-available" &&
        part.output &&
        typeof part.output === "object" &&
        "itinerary_id" in (part.output as Record<string, unknown>)
      ) {
        return part.output as Itinerary;
      }
    }
  }
  return null;
}

function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card/50 p-3">
      <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className="mt-1 truncate text-sm font-semibold text-foreground" title={value}>
        {value}
      </div>
    </div>
  );
}

export function ItineraryPanel({
  itinerary,
  building,
}: {
  itinerary: Itinerary | null;
  building: boolean;
}) {
  return (
    <aside className="hidden h-full w-96 shrink-0 flex-col border-l border-border bg-sidebar lg:flex">
      <div className="flex items-center gap-2 border-b border-border px-5 py-4">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Compass className="h-4 w-4" />
        </span>
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">
            Itinerary
          </h2>
          <p className="text-xs text-muted-foreground">Live planner output</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        {!itinerary ? (
          <div className="flex h-full flex-col items-center justify-center px-4 text-center">
            {building ? (
              <>
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <p className="mt-3 text-sm text-muted-foreground">
                  Assembling your itinerary from tool results…
                </p>
              </>
            ) : (
              <>
                <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary text-muted-foreground">
                  <MapPin className="h-7 w-7" />
                </span>
                <p className="mt-3 text-sm font-medium text-foreground">No itinerary yet</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Ask the agent to plan a trip and the finished itinerary will appear here.
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold leading-tight text-foreground">
                {itinerary.trip_name}
              </h3>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <code className="rounded bg-secondary px-1.5 py-0.5 font-mono">
                  {itinerary.itinerary_id}
                </code>
                {itinerary.checkin && itinerary.checkout && (
                  <span className="flex items-center gap-1">
                    <CalendarDays className="h-3.5 w-3.5" />
                    {formatDate(itinerary.checkin)} – {formatDate(itinerary.checkout)}
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <Stat
                icon={<Wallet className="h-3 w-3 text-primary" />}
                label="Total"
                value={money(itinerary.total_cost)}
              />
              <Stat
                icon={<Plane className="h-3 w-3 text-accent" />}
                label="Flight"
                value={money(itinerary.total_flight_cost)}
              />
              <Stat
                icon={<Hotel className="h-3 w-3 text-accent" />}
                label="Hotel"
                value={itinerary.hotel_name ?? money(itinerary.total_hotel_cost)}
              />
              <Stat
                icon={<Hotel className="h-3 w-3 text-primary" />}
                label="Lodging cost"
                value={money(itinerary.total_hotel_cost)}
              />
            </div>

            {itinerary.daily_schedule && (
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Daily schedule
                </h4>
                {Object.entries(itinerary.daily_schedule).map(([date, items], di) => (
                  <div
                    key={date}
                    className="rounded-xl border border-border bg-card/50 p-3"
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/15 text-[11px] font-semibold text-primary">
                        {di + 1}
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {formatDate(date)}
                      </span>
                    </div>
                    <ul className="space-y-1.5">
                      {items.map((item, ii) => (
                        <li
                          key={ii}
                          className="flex gap-2 text-[13px] leading-snug text-muted-foreground"
                        >
                          <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary/70" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}

            {itinerary.notes && (
              <div className="rounded-xl border border-border bg-card/50 p-3">
                <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  <StickyNote className="h-3 w-3 text-accent" /> Notes
                </div>
                <p className="text-[13px] leading-relaxed text-muted-foreground">
                  {itinerary.notes}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="border-t border-border px-5 py-3 text-[11px] text-muted-foreground">
        Powered by Pydantic AI · MCP travel demo
      </div>
    </aside>
  );
}