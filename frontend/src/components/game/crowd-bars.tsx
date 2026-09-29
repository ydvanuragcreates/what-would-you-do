"use client";

import { motion } from "motion/react";

import type { Choice, CrowdStats } from "@/lib/api/types";
import { CHOICE_STYLES } from "@/lib/choices";
import { cn } from "@/lib/utils";

type Props = {
  choices: Choice[];
  crowd: CrowdStats;
  yourChoiceId: number;
};

/**
 * "How others answered": one row per option with the share of OTHER players who chose it.
 * When there isn't enough data the bars are replaced by an honest message; nothing is
 * ever estimated or filled in.
 */
export function CrowdBars({ choices, crowd, yourChoiceId }: Props) {
  const percentFor = new Map(crowd.choices.map((share) => [share.choice_id, share.percent]));
  // The most popular option(s) get emphasised.
  const topPercent = Math.max(0, ...crowd.choices.map((share) => share.percent));

  return (
    <div className="space-y-3">
      <ul className="space-y-2.5">
        {choices.map((choice) => {
          const style = CHOICE_STYLES[choice.label];
          const isYours = choice.id === yourChoiceId;
          const percent = crowd.available ? (percentFor.get(choice.id) ?? 0) : null;
          return (
            <li
              key={choice.id}
              data-testid={`crowd-row-${choice.label}`}
              className={cn(
                "relative overflow-hidden rounded-xl border px-3.5 py-3",
                isYours ? style.ring : "border-border bg-background/40",
              )}
            >
              {percent !== null && (
                <motion.div
                  aria-hidden
                  className={cn("absolute inset-y-0 left-0 opacity-25", style.bar)}
                  initial={{ width: 0 }}
                  animate={{ width: `${percent}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                />
              )}
              <div className="relative flex items-center gap-3">
                <span
                  aria-hidden
                  className={cn(
                    "grid size-7 shrink-0 place-items-center rounded-lg text-sm font-bold",
                    style.badge,
                  )}
                >
                  {choice.label}
                </span>
                <span className="flex-1 text-[0.95rem] leading-snug">
                  {choice.text}
                  {isYours && (
                    <span className={cn("ml-2 text-xs font-semibold tracking-wide uppercase", style.text)}>
                      You
                    </span>
                  )}
                </span>
                {percent !== null && (
                  <span
                    className={cn(
                      "font-heading text-lg font-semibold tabular-nums",
                      percent === topPercent && percent > 0 ? "text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {percent}%
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {crowd.available ? (
        <p className="text-muted-foreground text-xs">
          Based on {crowd.total_responses} other {crowd.total_responses === 1 ? "player" : "players"}.
        </p>
      ) : (
        <p className="text-muted-foreground text-sm" data-testid="crowd-unavailable">
          {crowd.message ?? "Not enough responses yet."}{" "}
          <span className="text-muted-foreground/80">
            Other players&apos; answers appear here once enough people have played.
          </span>
        </p>
      )}
    </div>
  );
}
