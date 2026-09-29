"use client";

import { motion } from "motion/react";

import type { DimensionScore } from "@/lib/api/types";
import { cn } from "@/lib/utils";

/** "7.4" for a real score; the API sends `null` when a dimension came up too rarely to judge. */
export function formatScore(score: number): string {
  return score.toFixed(1);
}

export function ScoreBars({ scores }: { scores: DimensionScore[] }) {
  return (
    <ul className="space-y-4">
      {scores.map((row, index) => {
        const hasScore = row.score !== null;
        return (
          <li key={row.dimension} data-testid={`score-${row.dimension}`}>
            <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
              <span className="font-medium">{row.label}</span>
              {hasScore ? (
                <span className="font-heading tabular-nums">
                  {formatScore(row.score!)} <span className="text-muted-foreground">/ 10</span>
                </span>
              ) : (
                <span className="text-muted-foreground text-xs">Not enough data this round</span>
              )}
            </div>
            <div
              role="meter"
              aria-label={row.label}
              aria-valuemin={0}
              aria-valuemax={10}
              aria-valuenow={hasScore ? row.score! : undefined}
              aria-valuetext={hasScore ? `${formatScore(row.score!)} out of 10` : "Not enough data"}
              className={cn(
                "h-2.5 overflow-hidden rounded-full",
                hasScore ? "bg-muted" : "bg-muted/50 border-border border border-dashed",
              )}
            >
              {hasScore && (
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-violet-400 to-amber-300"
                  initial={{ width: 0 }}
                  animate={{ width: `${(row.score! / 10) * 100}%` }}
                  transition={{ duration: 0.9, delay: 0.1 + index * 0.05, ease: "easeOut" }}
                />
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
