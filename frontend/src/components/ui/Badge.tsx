import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Badge({
  className,
  color,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { color?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        !color && "bg-ink/8 text-ink",
        className,
      )}
      style={color ? { background: color, color: "white" } : undefined}
      {...props}
    />
  );
}
