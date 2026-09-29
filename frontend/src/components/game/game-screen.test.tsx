/**
 * The container that connects the game to the API. The API hooks are replaced with
 * fakes, so these tests check the flow (answer -> reveal -> next -> results) and the
 * error handling without any server.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import type { RoundState } from "@/lib/api/types";
import { CROWD_AVAILABLE, makeLastAnswer, makeQuestion } from "@/test/fixtures";

const router = { push: vi.fn(), replace: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

// What the fake hooks currently return; each test sets these up.
let roundQuery: { data?: RoundState; isPending: boolean; error: unknown; refetch: () => void };
const mutate = vi.fn();
vi.mock("@/lib/api/hooks", () => ({
  keys: { round: (id: string) => ["round", id] },
  useRound: () => roundQuery,
  useSubmitAnswer: () => ({ mutate }),
}));

import { GameScreen } from "./game-screen";

const question = makeQuestion();

function inProgress(number = 4): RoundState {
  return {
    id: "round-1",
    status: "in_progress",
    category_id: null,
    question_count: 10,
    current_question_number: number,
    question,
    result: null,
  };
}

function renderScreen() {
  const client = new QueryClient();
  const invalidate = vi.spyOn(client, "invalidateQueries");
  render(
    <QueryClientProvider client={client}>
      <GameScreen roundId="round-1" />
    </QueryClientProvider>,
  );
  return { user: userEvent.setup(), invalidate };
}

/** Pretend the server answered the request that `mutate` was last called with. */
function serverAnswers(state: Partial<RoundState>) {
  const callbacks = mutate.mock.calls.at(-1)![1] as { onSuccess: (s: RoundState) => void };
  act(() => callbacks.onSuccess({ ...inProgress(), ...state }));
}

function serverFails(error: unknown) {
  const callbacks = mutate.mock.calls.at(-1)![1] as { onError: (e: unknown) => void };
  act(() => callbacks.onError(error));
}

beforeEach(() => {
  vi.clearAllMocks();
  roundQuery = { data: inProgress(), isPending: false, error: null, refetch: vi.fn() };
});

describe("GameScreen", () => {
  it("shows the current question of the round", () => {
    renderScreen();

    expect(screen.getByText(question.situation_text)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "4");
  });

  it("sends the chosen option along with the question it belongs to", async () => {
    const { user } = renderScreen();

    await user.click(screen.getByRole("button", { name: /option b/i }));

    expect(mutate).toHaveBeenCalledTimes(1);
    expect(mutate.mock.calls[0][0]).toEqual({ scenarioId: 7, choiceId: 102 });
  });

  it("locks the options while the answer is in flight", async () => {
    const { user } = renderScreen();

    await user.click(screen.getByRole("button", { name: /option b/i }));

    for (const button of screen.getAllByRole("button")) expect(button).toBeDisabled();
    await user.keyboard("a"); // and the keyboard can't sneak a second answer in
    expect(mutate).toHaveBeenCalledTimes(1);
  });

  it("shows the reveal once the server accepts the answer", async () => {
    const { user } = renderScreen();
    await user.click(screen.getByRole("button", { name: /option b/i }));

    serverAnswers({ last_answer: makeLastAnswer(CROWD_AVAILABLE, 102) });

    // the question card animates out before the reveal animates in, so wait for it
    expect(await screen.findByText(/how everyone else answered/i)).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(router.push).not.toHaveBeenCalled();
  });

  it("goes to the results after the final reveal, not before", async () => {
    roundQuery.data = inProgress(10);
    const { user } = renderScreen();
    await user.click(screen.getByRole("button", { name: /option a/i }));

    serverAnswers({
      status: "completed",
      question: null,
      current_question_number: null,
      last_answer: makeLastAnswer(CROWD_AVAILABLE, 101),
    });
    // The round is finished on the server, but the player still gets to see the reveal.
    expect(router.replace).not.toHaveBeenCalled();
    expect(router.push).not.toHaveBeenCalled();

    await user.click(await screen.findByRole("button", { name: /see my results/i }));

    expect(router.push).toHaveBeenCalledWith("/results/round-1");
  });

  it("re-enables the options and explains when the request fails", async () => {
    const { user } = renderScreen();
    await user.click(screen.getByRole("button", { name: /option b/i }));

    serverFails(new ApiError(0, "network_error", "Can't reach the server."));

    expect(screen.getByRole("alert")).toHaveTextContent("Can't reach the server.");
    for (const button of screen.getAllByRole("button")) expect(button).toBeEnabled();
  });

  it("resyncs with the server when the question was already answered (double click, other tab)", async () => {
    const { user, invalidate } = renderScreen();
    await user.click(screen.getByRole("button", { name: /option b/i }));

    serverFails(new ApiError(409, "not_current_question", "That isn't the current question."));

    expect(screen.getByRole("alert")).toHaveTextContent(/already answered/i);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["round", "round-1"] });
  });

  it("sends people who open a finished round to its result", () => {
    roundQuery.data = { ...inProgress(), status: "completed", question: null, current_question_number: null };

    renderScreen();

    expect(router.replace).toHaveBeenCalledWith("/results/round-1");
    expect(screen.queryByRole("button", { name: /option/i })).not.toBeInTheDocument();
  });

  it("shows a loading state while the round loads", () => {
    roundQuery = { isPending: true, error: null, refetch: vi.fn() };

    renderScreen();

    expect(screen.getByRole("status")).toHaveTextContent(/loading your round/i);
  });

  it("explains a missing round without leaking whether it belongs to someone else", () => {
    roundQuery = {
      isPending: false,
      error: new ApiError(404, "round_not_found", "That round doesn't exist."),
      refetch: vi.fn(),
    };

    renderScreen();

    expect(screen.getByRole("alert")).toHaveTextContent(/doesn't exist, or it belongs to someone else/i);
  });

  it("offers a retry for other failures", async () => {
    roundQuery = {
      isPending: false,
      error: new ApiError(500, "internal_error", "Something went wrong."),
      refetch: vi.fn(),
    };
    const { user } = renderScreen();

    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(roundQuery.refetch).toHaveBeenCalled();
  });
});
