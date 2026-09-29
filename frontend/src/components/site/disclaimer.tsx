import { cn } from "@/lib/utils";

/** The entertainment-only notice. Shown wherever a result or score appears. */
export function Disclaimer({ className, text }: { className?: string; text?: string }) {
  return (
    <p className={cn("text-muted-foreground text-xs leading-relaxed", className)}>
      {text ??
        "Just for fun and self-reflection. This isn't a psychological or moral assessment, and it only reflects the choices you made in this one round."}
    </p>
  );
}
