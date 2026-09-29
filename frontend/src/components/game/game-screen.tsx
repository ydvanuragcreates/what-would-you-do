"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { GameView } from "@/components/game/game-view";
import { ErrorState, PageLoading } from "@/components/states";
import { buttonVariants } from "@/components/ui/button";
import { keys, useRound, useSubmitAnswer } from "@/lib/api/hooks";
import { isApiError, messageFor } from "@/lib/api/errors";
import type { Choice, LastAnswer, Question } from "@/lib/api/types";

/** What we remember about the answer just given, so the reveal can be shown before moving on. */
type Revealed = {
  question: Question;
  number: number;
  lastAnswer: LastAnswer;
  /** That was the final answer: continuing goes to the results page. */
  finished: boolean;
};

export function GameScreen({ roundId }: { roundId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const round = useRound(roundId);
  const submit = useSubmitAnswer(roundId);

  const [pendingChoiceId, setPendingChoiceId] = useState<number | null>(null);
  const [revealed, setRevealed] = useState<Revealed | null>(null);
  const [error, setError] = useState<string | null>(null);

  const state = round.data;

  // Opened a finished round (reload after the last answer, an old link): go to its result.
  useEffect(() => {
    if (state && state.status !== "in_progress" && !revealed) {
      router.replace(`/results/${roundId}`);
    }
  }, [state, revealed, roundId, router]);

  const onChoose = useCallback(
    (choice: Choice) => {
      if (!state?.question || state.current_question_number == null || pendingChoiceId !== null) {
        return;
      }
      const { question, current_question_number: number } = state;
      setPendingChoiceId(choice.id);
      setError(null);

      submit.mutate(
        { scenarioId: question.id, choiceId: choice.id },
        {
          onSuccess: (next) => {
            if (next.last_answer) {
              setRevealed({
                question,
                number,
                lastAnswer: next.last_answer,
                finished: next.status === "completed",
              });
            } else {
              setPendingChoiceId(null);
            }
          },
          onError: (failure) => {
            setPendingChoiceId(null);
            if (isApiError(failure, "not_current_question")) {
              // Another tab (or a double click) already answered: resync with the server.
              setError("That question was already answered, so here's where you are now.");
              void queryClient.invalidateQueries({ queryKey: keys.round(roundId) });
            } else {
              setError(messageFor(failure));
            }
          },
        },
      );
    },
    [state, pendingChoiceId, submit, queryClient, roundId],
  );

  const onNext = useCallback(() => {
    if (!revealed) return;
    const { finished } = revealed;
    setRevealed(null);
    setPendingChoiceId(null);
    if (finished) router.push(`/results/${roundId}`);
  }, [revealed, roundId, router]);

  if (round.isPending) return <PageLoading label="Loading your round…" />;

  if (round.error) {
    if (isApiError(round.error, "round_not_found")) {
      return (
        <ErrorState
          title="Round not found"
          message="This round doesn't exist, or it belongs to someone else."
        />
      );
    }
    return <ErrorState message={messageFor(round.error)} onRetry={() => void round.refetch()} />;
  }

  // Finished and not showing the last reveal: the effect above is already redirecting.
  if (!revealed && (state?.status !== "in_progress" || !state.question)) {
    return <PageLoading label="Opening your results…" />;
  }

  const question = revealed ? revealed.question : state!.question!;
  const questionNumber = revealed ? revealed.number : (state!.current_question_number ?? 1);
  const total = state!.question_count;

  return (
    <GameView
      question={question}
      questionNumber={questionNumber}
      totalQuestions={total}
      pendingChoiceId={pendingChoiceId}
      reveal={revealed?.lastAnswer ?? null}
      isLastQuestion={questionNumber === total}
      error={error}
      onChoose={onChoose}
      onNext={onNext}
    />
  );
}

export function LeaveRoundLink() {
  return (
    <Link href="/play" className={buttonVariants({ variant: "ghost", size: "sm" })}>
      Leave round
    </Link>
  );
}
