"use client";

import { Dices, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ErrorState } from "@/components/states";
import { Skeleton } from "@/components/ui/skeleton";
import { useCategories, useStartRound } from "@/lib/api/hooks";
import { messageFor } from "@/lib/api/errors";
import { cn } from "@/lib/utils";

type CardProps = {
  title: string;
  subtitle: string;
  emoji?: string;
  featured?: boolean;
  playable: boolean;
  starting: boolean;
  disabled: boolean;
  onClick: () => void;
};

function OptionCard({ title, subtitle, emoji, featured, playable, starting, disabled, onClick }: CardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || !playable}
      className={cn(
        "surface group flex flex-col items-start gap-3 p-5 text-left transition-all duration-200 outline-none",
        "focus-visible:ring-ring/60 focus-visible:ring-3",
        playable && !disabled && "hover:-translate-y-0.5 hover:border-primary/60 hover:shadow-[0_0_40px_-12px_var(--glow)]",
        !playable && "opacity-55",
        featured && "sm:col-span-2 lg:col-span-3 sm:flex-row sm:items-center sm:gap-5 sm:p-6",
      )}
    >
      <span
        aria-hidden
        className={cn(
          "grid shrink-0 place-items-center rounded-2xl bg-primary/15 text-3xl",
          featured ? "size-14" : "size-12",
        )}
      >
        {emoji ?? <Dices className="text-primary size-7" />}
      </span>
      <span className="flex-1 space-y-0.5">
        <span className="font-heading block text-lg font-semibold">{title}</span>
        <span className="text-muted-foreground block text-sm">{subtitle}</span>
      </span>
      {starting && <Loader2 className="text-muted-foreground size-5 animate-spin" aria-label="Starting" />}
      {!playable && (
        <span className="bg-muted text-muted-foreground rounded-full px-2.5 py-0.5 text-xs font-medium">
          Coming soon
        </span>
      )}
    </button>
  );
}

export function CategoryPicker() {
  const router = useRouter();
  const categories = useCategories();
  const start = useStartRound();
  // Which card was clicked, so only that one shows the spinner.
  const [startingId, setStartingId] = useState<number | "random" | null>(null);
  const [error, setError] = useState<string | null>(null);

  function begin(categoryId: number | null) {
    setError(null);
    setStartingId(categoryId ?? "random");
    start.mutate(categoryId, {
      onSuccess: (round) => router.push(`/play/${round.id}`),
      onError: (failure) => {
        setStartingId(null);
        setError(messageFor(failure));
      },
    });
  }

  if (categories.isPending) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-label="Loading categories">
        <Skeleton className="h-28 rounded-2xl sm:col-span-2 lg:col-span-3" />
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-32 rounded-2xl" />
        ))}
      </div>
    );
  }

  if (categories.error) {
    return <ErrorState message={messageFor(categories.error)} onRetry={() => void categories.refetch()} />;
  }

  const { random, categories: list, round_length: roundLength } = categories.data;
  const busy = start.isPending;

  return (
    <div className="space-y-5">
      {error && (
        <p role="alert" className="bg-destructive/10 text-destructive rounded-lg px-3 py-2 text-sm">
          {error}
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <OptionCard
          featured
          title="Random"
          subtitle={`${roundLength} questions from every category. The classic way to play.`}
          playable={random.playable}
          starting={startingId === "random"}
          disabled={busy}
          onClick={() => begin(null)}
        />
        {list.map((category) => (
          <OptionCard
            key={category.id}
            title={category.name}
            emoji={category.emoji || undefined}
            subtitle={
              category.playable
                ? `${category.scenario_count} situations`
                : `${category.scenario_count} of ${roundLength} situations ready`
            }
            playable={category.playable}
            starting={startingId === category.id}
            disabled={busy}
            onClick={() => begin(category.id)}
          />
        ))}
      </div>
    </div>
  );
}
