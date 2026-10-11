import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: React.ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-none border border-border bg-[var(--ed-bg-elev)] px-2 py-0.5 font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.12em] text-[var(--ed-fg-soft)]",
        className,
      )}
      {...props}
    />
  );
}
