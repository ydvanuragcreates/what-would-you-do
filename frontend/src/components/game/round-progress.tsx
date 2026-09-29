import { cn } from "@/lib/utils";

/** "Question 4 / 10" with one segment per question. */
export function RoundProgress({ current, total }: { current: number; total: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between text-xs font-medium tracking-widest uppercase">
        <span className="text-muted-foreground">Round</span>
        <span>
          Question {current} <span className="text-muted-foreground">/ {total}</span>
        </span>
      </div>
      <div
        role="progressbar"
        aria-label={`Question ${current} of ${total}`}
        aria-valuemin={1}
        aria-valuemax={total}
        aria-valuenow={current}
        className="flex gap-1.5"
      >
        {Array.from({ length: total }, (_, index) => {
          const position = index + 1;
          return (
            <span
              key={position}
              data-state={position < current ? "done" : position === current ? "current" : "todo"}
              className={cn(
                "h-1.5 flex-1 rounded-full transition-colors duration-500",
                position < current && "bg-primary",
                position === current && "bg-gradient-to-r from-violet-400 to-amber-300",
                position > current && "bg-muted",
              )}
            />
          );
        })}
      </div>
    </div>
  );
}
