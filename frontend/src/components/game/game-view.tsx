"use client";

import { ArrowRight, Flag } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect } from "react";

import { ChoiceButton } from "@/components/game/choice-button";
import { CrowdBars } from "@/components/game/crowd-bars";
import { RoundProgress } from "@/components/game/round-progress";
import { Button } from "@/components/ui/button";
import type { Choice, LastAnswer, Question } from "@/lib/api/types";
import { labelForKey } from "@/lib/choices";

export type GameViewProps = {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  /** The option being sent to the server right now, if any. */
  pendingChoiceId: number | null;
  /** Set once the server has accepted the answer: switches the screen to the reveal. */
  reveal: LastAnswer | null;
  isLastQuestion: boolean;
  error: string | null;
  onChoose: (choice: Choice) => void;
  onNext: () => void;
};

/**
 * One question, in two phases:
 *  1. answering: the situation and three options (click, or press A/B/C or 1/2/3)
 *  2. reveal: what you picked and how other players answered (Enter continues)
 * Pure UI: everything arrives as props, so it is easy to test without a server.
 */
export function GameView({
  question,
  questionNumber,
  totalQuestions,
  pendingChoiceId,
  reveal,
  isLastQuestion,
  error,
  onChoose,
  onNext,
}: GameViewProps) {
  const locked = pendingChoiceId !== null;

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.repeat) return;
      if (reveal) {
        if (event.key === "Enter") onNext();
        return;
      }
      if (locked) return;
      const label = labelForKey(event);
      const choice = question.choices.find((c) => c.label === label);
      if (choice) onChoose(choice);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [reveal, locked, question, onChoose, onNext]);

  return (
    <div className="mx-auto w-full max-w-2xl space-y-8">
      <RoundProgress current={questionNumber} total={totalQuestions} />

      <AnimatePresence mode="wait">
        <motion.section
          key={`${question.id}-${reveal ? "reveal" : "ask"}`}
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          aria-labelledby="situation"
          className="space-y-6"
        >
          <div className="surface space-y-3 p-6 sm:p-8">
            <p className="text-muted-foreground text-xs font-medium tracking-widest uppercase">
              {question.title}
            </p>
            <p id="situation" className="font-heading text-2xl leading-snug font-medium sm:text-3xl">
              {question.situation_text}
            </p>
          </div>

          {reveal ? (
            <div aria-live="polite" className="space-y-5">
              <h2 className="text-lg font-semibold">How everyone else answered</h2>
              <CrowdBars
                choices={question.choices}
                crowd={reveal.crowd}
                yourChoiceId={reveal.your_choice_id}
              />
              <div className="flex justify-end">
                <Button size="xl" onClick={onNext} autoFocus>
                  {isLastQuestion ? (
                    <>
                      See my results <Flag aria-hidden />
                    </>
                  ) : (
                    <>
                      Next question <ArrowRight aria-hidden />
                    </>
                  )}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <h2 className="text-muted-foreground text-base font-medium">What do you do?</h2>
              <div className="space-y-3">
                {question.choices.map((choice) => (
                  <ChoiceButton
                    key={choice.id}
                    choice={choice}
                    pending={pendingChoiceId === choice.id}
                    locked={locked}
                    onSelect={onChoose}
                  />
                ))}
              </div>
              <p className="text-muted-foreground hidden pt-1 text-xs sm:block">
                Tip: press <kbd className="font-mono">A</kbd>, <kbd className="font-mono">B</kbd> or{" "}
                <kbd className="font-mono">C</kbd> to answer.
              </p>
            </div>
          )}

          {error && (
            <p role="alert" className="bg-destructive/10 text-destructive rounded-lg px-3 py-2 text-sm">
              {error}
            </p>
          )}
        </motion.section>
      </AnimatePresence>
    </div>
  );
}
