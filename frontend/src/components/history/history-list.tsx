"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";

import { ErrorState } from "@/components/states";
import { buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { messageFor } from "@/lib/api/errors";
import { useHistory } from "@/lib/api/hooks";

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

export function HistoryList() {
  const history = useHistory();

  if (history.isPending) {
    return (
      <div className="space-y-3" aria-busy="true" aria-label="Loading your rounds">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-20 rounded-2xl" />
        ))}
      </div>
    );
  }
  if (history.error) {
    return <ErrorState message={messageFor(history.error)} onRetry={() => void history.refetch()} />;
  }

  const { results } = history.data;
  if (results.length === 0) {
    return (
      <div className="surface flex flex-col items-center gap-4 px-6 py-14 text-center">
        <p className="text-lg font-medium">No rounds yet</p>
        <p className="text-muted-foreground max-w-sm text-sm">
          Finish a round and it will show up here, so you can look back at how your choices leaned.
        </p>
        <Link href="/play" className={buttonVariants({ size: "lg" })}>
          Start a Round
        </Link>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {results.map((entry) => (
        <li key={entry.round_id}>
          <Link
            href={`/results/${entry.round_id}`}
            className="surface hover:border-primary/60 flex items-center gap-4 p-4 transition-colors sm:p-5"
          >
            <div className="min-w-0 flex-1">
              <p className="font-heading truncate text-lg font-semibold">{entry.profile.title}</p>
              <p className="text-muted-foreground text-sm">
                {entry.category_name} · {dateFormat.format(new Date(entry.completed_at))}
              </p>
            </div>
            <ChevronRight className="text-muted-foreground size-5 shrink-0" aria-hidden />
          </Link>
        </li>
      ))}
    </ul>
  );
}
