"use client";

import Link from "next/link";

import { ResultsView } from "@/components/results/results-view";
import { ErrorState, PageLoading } from "@/components/states";
import { buttonVariants } from "@/components/ui/button";
import { isApiError, messageFor } from "@/lib/api/errors";
import { useResult } from "@/lib/api/hooks";

export function ResultsScreen({ roundId }: { roundId: string }) {
  const result = useResult(roundId);

  if (result.isPending) return <PageLoading label="Working out your profile…" />;

  if (result.error) {
    if (isApiError(result.error, "round_not_completed")) {
      return (
        <div className="mx-auto flex max-w-md flex-col items-center gap-4 py-24 text-center">
          <h1 className="text-2xl font-semibold">This round isn&apos;t finished yet</h1>
          <p className="text-muted-foreground">Answer every question to see your result.</p>
          <Link href={`/play/${roundId}`} className={buttonVariants({ size: "lg" })}>
            Back to the round
          </Link>
        </div>
      );
    }
    if (isApiError(result.error, "round_not_found")) {
      return (
        <ErrorState
          title="Result not found"
          message="This result doesn't exist, or it belongs to someone else."
        />
      );
    }
    return <ErrorState message={messageFor(result.error)} onRetry={() => void result.refetch()} />;
  }

  return <ResultsView result={result.data} />;
}
