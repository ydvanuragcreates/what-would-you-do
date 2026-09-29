import { Loader2, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function PageLoading({ label = "Loading…", className }: { label?: string; className?: string }) {
  return (
    <div
      role="status"
      className={cn("text-muted-foreground flex flex-1 items-center justify-center gap-3 py-24", className)}
    >
      <Loader2 className="size-5 animate-spin" aria-hidden />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn("mx-auto flex max-w-md flex-1 flex-col items-center justify-center gap-4 py-24 text-center", className)}
    >
      <TriangleAlert className="text-destructive size-8" aria-hidden />
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">{title}</h2>
        <p className="text-muted-foreground text-sm">{message}</p>
      </div>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
