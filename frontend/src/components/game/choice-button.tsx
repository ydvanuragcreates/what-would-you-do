import { Loader2 } from "lucide-react";

import type { Choice } from "@/lib/api/types";
import { CHOICE_STYLES } from "@/lib/choices";
import { cn } from "@/lib/utils";

type Props = {
  choice: Choice;
  /** This option was picked and the answer is being sent. */
  pending: boolean;
  /** Some option is being sent, so all options are locked. */
  locked: boolean;
  onSelect: (choice: Choice) => void;
};

export function ChoiceButton({ choice, pending, locked, onSelect }: Props) {
  const style = CHOICE_STYLES[choice.label];
  return (
    <button
      type="button"
      disabled={locked}
      aria-label={`Option ${choice.label}: ${choice.text}`}
      onClick={() => onSelect(choice)}
      className={cn(
        "group border-border bg-card/70 flex w-full items-center gap-4 rounded-2xl border px-4 py-4 text-left backdrop-blur-sm transition-all duration-200 sm:px-5 sm:py-5",
        "focus-visible:ring-ring/60 outline-none focus-visible:ring-3",
        !locked && "hover:-translate-y-0.5 hover:border-foreground/25 hover:bg-card active:translate-y-0",
        pending && style.ring,
        locked && !pending && "opacity-50",
      )}
    >
      <span
        aria-hidden
        className={cn(
          "grid size-9 shrink-0 place-items-center rounded-xl text-base font-bold transition-transform group-hover:scale-105",
          style.badge,
        )}
      >
        {choice.label}
      </span>
      <span className="flex-1 text-base leading-snug sm:text-lg">{choice.text}</span>
      {pending && <Loader2 className="text-muted-foreground size-5 animate-spin" aria-hidden />}
    </button>
  );
}
