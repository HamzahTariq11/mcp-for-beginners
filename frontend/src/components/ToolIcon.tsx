import {
  Plane,
  Hotel,
  CloudSun,
  Landmark,
  Route,
  Wrench,
  type LucideProps,
} from "lucide-react";

const MAP: Record<string, React.ComponentType<LucideProps>> = {
  plane: Plane,
  hotel: Hotel,
  "cloud-sun": CloudSun,
  landmark: Landmark,
  route: Route,
};

export function ToolIcon({ name, ...props }: { name: string } & LucideProps) {
  const Cmp = MAP[name] ?? Wrench;
  return <Cmp {...props} />;
}