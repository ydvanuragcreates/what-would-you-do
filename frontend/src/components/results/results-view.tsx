import { ArrowRight, History } from "lucide-react";
import Link from "next/link";

import { CrowdBars } from "@/components/game/crowd-bars";
import { ScoreBars } from "@/components/results/score-bars";
import { Disclaimer } from "@/components/site/disclaimer";
import { buttonVariants } from "@/components/ui/button";
import type { RoundResult } from "@/lib/api/types";
import { CHOICE_STYLES } from "@/lib/choices";
import { cn } from "@/lib/utils";

/** The end-of-round screen: profile, scores, and how each answer compared with everyone else's. */
export function ResultsView({ result }: { result: RoundResult }) {
  return (
    <div className="mx-auto w-full max-w-3xl space-y-14">
      <section className="animate-in fade-in slide-in-from-bottom-4 space-y-5 text-center duration-700">
        <p className="text-muted-foreground text-xs font-medium tracking-[0.3em] uppercase">
          Round complete · {result.category_name}
        </p>
        <p className="text-muted-foreground">Your decisions in this round resembled…</p>
        <h1 className="text-gradient text-5xl leading-tight font-bold sm:text-6xl">
          {result.profile.title}
        </h1>
        <p className="text-foreground/90 mx-auto max-w-xl text-lg leading-relaxed">
          {result.profile.summary}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link href="/play" className={buttonVariants({ size: "xl" })}>
            Play Another Round <ArrowRight aria-hidden />
          </Link>
          <Link href="/history" className={buttonVariants({ variant: "ghost", size: "xl" })}>
            <History aria-hidden /> History
          </Link>
        </div>
      </section>

      <section aria-labelledby="scores-heading" className="surface space-y-6 p-6 sm:p-8">
        <div className="space-y-1">
          <h2 id="scores-heading" className="text-2xl font-semibold">
            Your profile this round
          </h2>
          <p className="text-muted-foreground text-sm">
            Scores run from 0 to 10 and describe the options you chose, not who you are.
          </p>
        </div>
        <ScoreBars scores={result.scores} />
        <Disclaimer text={result.disclaimer} className="border-border border-t pt-4" />
      </section>

      <section aria-labelledby="others-heading" className="space-y-6">
        <div className="space-y-1">
          <h2 id="others-heading" className="text-2xl font-semibold">
            How others answered
          </h2>
          <p className="text-muted-foreground text-sm">
            Anonymous shares of other players. Your own answers are never counted here.
          </p>
        </div>
        <ol className="space-y-5">
          {result.questions.map((review) => {
            const yours = review.scenario.choices.find((c) => c.id === review.your_choice_id);
            return (
              <li key={review.question_number} className="surface space-y-4 p-5 sm:p-6">
                <div className="space-y-1.5">
                  <p className="text-muted-foreground text-xs font-medium tracking-widest uppercase">
                    Question {review.question_number} · {review.scenario.title}
                  </p>
                  <p className="font-heading text-lg leading-snug font-medium">
                    {review.scenario.situation_text}
                  </p>
                  {yours && (
                    <p className="text-sm">
                      You chose{" "}
                      <span className={cn("font-semibold", CHOICE_STYLES[yours.label].text)}>
                        {yours.label}
                      </span>
                    </p>
                  )}
                </div>
                <CrowdBars
                  choices={review.scenario.choices}
                  crowd={review.crowd}
                  yourChoiceId={review.your_choice_id}
                />
              </li>
            );
          })}
        </ol>
      </section>

      <div className="flex justify-center pb-8">
        <Link href="/play" className={buttonVariants({ size: "xl" })}>
          Play Another Round <ArrowRight aria-hidden />
        </Link>
      </div>
    </div>
  );
}
