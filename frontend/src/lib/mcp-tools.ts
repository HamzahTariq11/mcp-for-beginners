/**
 * Client-safe metadata describing the MCP tools (icons, server labels, params).
 * Used by the UI to render tool-call cards. The real tools are executed by the
 * Python MCP server; the agent that calls them lives in the FastAPI backend.
 */

export type ToolParam = {
  name: string;
  type: string;
  description: string;
};

export type McpToolMeta = {
  name: string;
  /** lucide-react icon name */
  icon: string;
  /** simulated MCP server this tool belongs to */
  server: string;
  description: string;
  params: ToolParam[];
};

export const MCP_TOOLS: McpToolMeta[] = [
  {
    name: "search_flights",
    icon: "plane",
    server: "flights-mcp",
    description: "Find available flights between two cities for a date.",
    params: [
      { name: "origin", type: "string", description: "Origin city or airport, e.g. 'KHI'" },
      { name: "destination", type: "string", description: "Destination city or airport, e.g. 'IST'" },
      { name: "date", type: "string", description: "Departure date (YYYY-MM-DD)" },
    ],
  },
  {
    name: "search_hotels",
    icon: "hotel",
    server: "hotels-mcp",
    description: "Search hotels in a city for the given stay dates.",
    params: [
      { name: "city", type: "string", description: "City name, e.g. 'Istanbul'" },
      { name: "checkin", type: "string", description: "Check-in date (YYYY-MM-DD)" },
      { name: "checkout", type: "string", description: "Check-out date (YYYY-MM-DD)" },
    ],
  },
  {
    name: "get_weather",
    icon: "cloud-sun",
    server: "weather-mcp",
    description: "Get a daily weather forecast for a destination over a date range.",
    params: [
      { name: "city", type: "string", description: "City name, e.g. 'Istanbul'" },
      { name: "start_date", type: "string", description: "First day (YYYY-MM-DD)" },
      { name: "end_date", type: "string", description: "Last day (YYYY-MM-DD)" },
    ],
  },
  {
    name: "get_attractions",
    icon: "landmark",
    server: "places-mcp",
    description: "Find attractions in a city, filtered by category.",
    params: [
      { name: "city", type: "string", description: "City name, e.g. 'Istanbul'" },
      { name: "category", type: "string", description: "'outdoor', 'indoor', or 'all'" },
      { name: "limit", type: "number", description: "Max results to return" },
    ],
  },
  {
    name: "create_itinerary",
    icon: "route",
    server: "planner-mcp",
    description: "Assemble a complete trip itinerary from the chosen flight, hotel, and plan.",
    params: [
      { name: "trip_name", type: "string", description: "Title for the trip" },
      { name: "flight_id", type: "string", description: "Chosen flight id" },
      { name: "hotel_id", type: "number", description: "Chosen hotel id" },
      { name: "daily_schedule", type: "object", description: "Date → list of activities" },
    ],
  },
];

export function getToolMeta(name: string): McpToolMeta | undefined {
  return MCP_TOOLS.find((t) => t.name === name);
}